#!/usr/bin/env python3
"""Move every Bambu Studio user preset to OrcaSlicer, value for value.

Usage: orca_presets.py [--dry-run] [--repo-copy DIR]

For each user preset in ~/Library/Application Support/BambuStudio/user/<id>/{machine,process,filament}/:
  1. resolve its Studio system parent and the same-named Orca system parent (full `inherits` chains);
  2. Orca preset = inherits the Orca parent + every key where the two system parents disagree (Studio's value wins)
     + the user's own keys;
  3. process presets get the bridge mapping below, filament presets get dont_slow_down_outer_wall = 1 (see FILAMENT_EXTRAS);
  4. written with a `version` key to Orca's user/default/<kind>/ (and to DIR, default profiles/orca/).

Orca reads presets only at start — quit Orca first or restart it after. Studio is not touched.

Traps found on 2026-10-03 (Orca 2.4.2, Studio 02.08.02.61):
- Orca silently skips a user preset without `version` ("loaded 0 presets" in its log).
- `tree_support_wall_count = -1` is Studio's "auto"; Orca's range is 0..2 and the CLI refuses the whole config.
- Machine start/end G-code stays Orca's own: same Bambu blocks (21 x M1002 in the start), written against Orca's
  placeholder set; Studio's newer blocks use placeholders Orca may not know (old_filament_temp).

Orca 2.5.0-alpha (installed ~2026-10-17) ships its system presets as <vendor>.opc caches, without BBL.json and the BBL/
tree, so the Orca parent can no longer be read from JSON: the script asks Orca's CLI for it (--export-settings with a
one-line user preset inheriting the parent, in a scratch data dir holding Orca's system/ caches — the CLI resolves
inherits and include itself, 0.2 s per parent) and reads the version from the stamp at the head of BBL.opc. Parity
then compares values, not spellings: the resolved config writes 1 and 100% where Studio's JSON has 1.0 and 100.
The plugin's orca.py does the same (bambu-print-model 0.1.11, references/orca.md "Orca 2.5").

Bridges. Studio lays a bridge as a round thread d = 0.4 * sqrt(bridge_flow) spaced d + 0.05 (measured on a Studio
G-code: 1.6 -> 0.203 mm2 at 0.558 mm), which is Orca's *thick* bridge; Orca's thin bridge is a flat 0.4 x 0.2 strip and
its 1.6 puts down half the plastic (0.114 mm2). Orca's internal bridge reuses the bridge thread and multiplies it by
internal_bridge_flow; overhang walls take the same thread, scaled by overhang_flow_ratio (only with
set_other_flow_ratios on). So 1 / bridge_flow returns both to the plain d0.4 thread Studio used for them, and internal
bridges run at 75 mm/s — what Orca's own A1 mini preset gives them (150 % of its 50 mm/s bridge); 50 until 2026-10-21,
when a 153 x 153 mm plate spent 11 of its 118 min on one internal-bridge layer. The thread (0.126 mm2) tops out near
95 mm/s at SUNLU PLA's 12 mm3/s. The slow 10 mm/s x 1.6 of ADR-0007 then stayed on visible bridges only: inherited by
internal bridges it hung in loops over 10 % gyroid (Gridfinity bin, 2026-10-03). Since 2026-10-24 no preset sets
bridge_flow (it sagged at times), so the mapping yields Orca's defaults; it still matters for a project that sets one."""
import glob, json, os, shutil, struct, subprocess, sys, tempfile

STUDIO = os.path.expanduser("~/Library/Application Support/BambuStudio")
ORCA_APP = "/Applications/OrcaSlicer.app/Contents/Resources/profiles"
ORCA_CLI = "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer"
ORCA_DATA = os.path.expanduser("~/Library/Application Support/OrcaSlicer")
ORCA_USER = f"{ORCA_DATA}/user/default"
KINDS = ("machine", "process", "filament")
META = {"name", "inherits", "from", "setting_id", "base_id", "filament_id", "version", "instantiation", "description",
        "renamed_from", "type", "print_settings_id", "filament_settings_id", "printer_settings_id", "compatible_printers",
        "compatible_printers_condition", "compatible_prints", "compatible_prints_condition", "upward_compatible_machine",
        "filament_extruder_variant", "print_extruder_id", "print_extruder_variant", "is_custom_defined"}
REJECTED = {("tree_support_wall_count", "-1")}
# What Studio 2.8 could not do and Orca can, added to every process preset:
# - scarf seam: Studio wrote seam_slope_* into the header but left the G-code body unchanged (ring, Benchy, CLI and
#   GUI); "external" + conditional puts a scarf only on smooth outer contours, a contour with a sharp corner keeps a
#   plain seam in that corner; length 20 mm, 10 steps, threshold 155 deg — Orca's defaults;
# - wipe_on_loops: a short inward move at the end of a closed loop against the seam blob; Studio has no such key.
ORCA_EXTRAS = {"seam_slope_type": "external", "seam_slope_conditional": "1", "wipe_on_loops": "1"}
# Studio name -> Orca name, same meaning (the print-model quality package sets the Studio one per project):
RENAMES = {"no_slow_down_for_cooling_on_outwalls": "dont_slow_down_outer_wall"}
# Added to every filament preset, so that slicing from the Orca GUI gets it too: the cooling slowdown (layer time
# under slow_down_layer_time) then stretches the inner wall and infill, never the outer wall. Measured on a 50 mm bin:
# 17 wall layers between the floor and the top shell had the outer wall at 145 instead of 200 mm/s — a band with a
# step at each edge; with the key the inner lines go 300 -> 107 there, layer time 5.7 s and total time unchanged.
# Cost: a small feature (a 17 x 8 mm tab: 5.8 -> 2.7 s per layer) loses the slowdown and needs a modifier part with
# a low outer_wall_speed over it; forecast check 7 of the print-model skill finds such layers.
FILAMENT_EXTRAS = {"dont_slow_down_outer_wall": ["1"]}


def find(roots, kind, name):
    for root in roots:
        for pat in (f"{root}/{kind}/{name}.json", f"{root}/{kind}/*/{name}.json"):
            hits = glob.glob(pat)
            if hits:
                return json.load(open(hits[0]))
    raise SystemExit(f"preset not found: {kind}/{name} in {roots}")


def resolve(roots, kind, name):
    chain = []
    while name:
        j = find(roots, kind, name)
        chain.append(j)
        name = j.get("inherits")
    merged = {}
    for j in reversed(chain):
        merged.update(j)
    return merged


def one(v):
    return v[0] if isinstance(v, list) and len(v) == 1 else v


def norm(v):
    """A value as it reads: Orca's resolved config writes 1 and 100% where Studio's JSON has 1.0 and 100."""
    v = one(v)
    if isinstance(v, list):
        return [norm(x) for x in v]
    try:
        return float(str(v).strip().rstrip("%"))
    except ValueError:
        return str(v)


def orca_version():
    """BBL.json's version (Orca 2.4), else the BBL.opc stamp: 20-byte header, u32 format, u64-sized name, u64-sized version."""
    for d in (ORCA_APP, f"{ORCA_DATA}/system"):
        if os.path.isfile(f"{d}/BBL.json"):
            return json.load(open(f"{d}/BBL.json"))["version"]
    for d in (f"{ORCA_DATA}/system", ORCA_APP):
        if os.path.isfile(f"{d}/BBL.opc"):
            b = open(f"{d}/BBL.opc", "rb").read(4096)
            i = 24 + 8 + struct.unpack_from("<Q", b, 24)[0]
            return b[i + 8:i + 8 + struct.unpack_from("<Q", b, i)[0]].decode()
    raise SystemExit("neither BBL.json nor BBL.opc found: open OrcaSlicer once")


_ORCA = {}


def orca_parent(kind, name):
    """The same-named Orca system preset, resolved: from Orca 2.4's JSON tree, else through Orca 2.5's CLI."""
    if os.path.isfile(f"{ORCA_APP}/BBL.json"):
        return resolve([f"{ORCA_APP}/BBL", f"{ORCA_APP}/OrcaFilamentLibrary"], kind, name)
    if (kind, name) not in _ORCA:
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(f"{ORCA_DATA}/system", f"{tmp}/system")
            os.makedirs(f"{tmp}/user/default/{kind}")
            stand = f"{tmp}/user/default/{kind}/{name} - stand-in.json"
            key = {"process": "print_settings_id", "filament": "filament_settings_id", "machine": "printer_settings_id"}[kind]
            json.dump({"type": kind, "name": name + " - stand-in", "inherits": name, "from": "User",
                       "version": orca_version(), key: name + " - stand-in"}, open(stand, "w"))
            r = subprocess.run([ORCA_CLI, "--datadir", tmp, "--load-filaments" if kind == "filament" else "--load-settings",
                                stand, "--export-settings", f"{tmp}/flat.json"], capture_output=True, text=True)
            if r.returncode or not os.path.exists(f"{tmp}/flat.json"):
                raise SystemExit(f"Orca could not resolve {kind}/{name}: " + (r.stdout + r.stderr).strip()[-300:])
            _ORCA[(kind, name)] = json.load(open(f"{tmp}/flat.json"))
    return _ORCA[(kind, name)]


def bridges(keys):
    bf = float(one(keys.get("bridge_flow", "1")))
    inv = f"{1 / bf:.3f}".rstrip("0").rstrip(".")
    out = {"thick_bridges": "1", "thick_internal_bridges": "1", "internal_bridge_speed": "75", "internal_bridge_flow": inv}
    if bf != 1:
        out.update({"set_other_flow_ratios": "1", "overhang_flow_ratio": inv})
    return out


def convert(kind, user, version):
    parent = user["inherits"]
    s, o = resolve([f"{STUDIO}/system/BBL"], kind, parent), orca_parent(kind, parent)
    parity = {k: s[k] for k in s if k in o and k not in META and not k.endswith("_gcode") and norm(s[k]) != norm(o[k])}
    own = {k: v for k, v in user.items() if k not in META}
    keys = {RENAMES.get(k, k): v for k, v in {**parity, **own}.items()}
    if kind == "process":
        keys.update(bridges(keys))
        keys.update(ORCA_EXTRAS)
    if kind == "filament":
        keys.update(FILAMENT_EXTRAS)
    keys = {k: v for k, v in keys.items() if (k, str(one(v))) not in REJECTED}
    out = {"from": "User", "version": version, "inherits": parent, "name": user["name"]}
    out.update({"process": {"print_settings_id": user["name"]}, "filament": {"filament_settings_id": [user["name"]]},
                "machine": {"printer_settings_id": user["name"]}}[kind])
    out.update(keys)
    return out, parity


def pending_delete(json_path):
    """A preset deleted through its .info (sync_info = delete) keeps its JSON until Studio next starts — on 2026-10-24
    the three Gridfinity presets ADR-0008 retired were still there, eleven days on, while Dima sliced in Orca."""
    info = json_path[:-5] + ".info"
    return os.path.isfile(info) and any(l.split("=", 1)[1].strip() == "delete"
                                         for l in open(info) if l.startswith("sync_info"))


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    repo = args[args.index("--repo-copy") + 1] if "--repo-copy" in args else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles", "orca")
    version = orca_version()
    users = [d for d in glob.glob(f"{STUDIO}/user/*/") if glob.glob(f"{d}*/*.json")]
    for d in users:
        for kind in KINDS:
            for f in sorted(glob.glob(f"{d}{kind}/*.json")):
                user = json.load(open(f))
                if pending_delete(f):
                    print(f"{kind:8s} {user['name']:32s} skipped: marked sync_info = delete, Studio removes it on its next start")
                    continue
                out, parity = convert(kind, user, version)
                print(f"{kind:8s} {user['name']:32s} <- {user['inherits']}   parity: {sorted(parity) or '-'}")
                if dry:
                    continue
                for root in (ORCA_USER, repo):
                    os.makedirs(f"{root}/{kind}", exist_ok=True)
                    json.dump(out, open(f"{root}/{kind}/{user['name']}.json", "w"), indent=4, ensure_ascii=False)
    if not dry:
        print(f"written to {ORCA_USER} and {repo}; restart Orca to load them")


if __name__ == "__main__":
    main()
