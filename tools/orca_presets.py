#!/usr/bin/env python3
"""Move every Bambu Studio user preset to OrcaSlicer, value for value.

Usage: orca_presets.py [--dry-run] [--repo-copy DIR]

For each user preset in ~/Library/Application Support/BambuStudio/user/<id>/{machine,process,filament}/:
  1. resolve its Studio system parent and the same-named Orca system parent (full `inherits` chains);
  2. Orca preset = inherits the Orca parent + every key where the two system parents disagree (Studio's value wins)
     + the user's own keys;
  3. process presets get the bridge mapping below;
  4. written with a `version` key to Orca's user/default/<kind>/ (and to DIR, default profiles/orca/).

Orca reads presets only at start — quit Orca first or restart it after. Studio is not touched.

Traps found on 2026-10-03 (Orca 2.4.2, Studio 02.08.02.61):
- Orca silently skips a user preset without `version` ("loaded 0 presets" in its log).
- `tree_support_wall_count = -1` is Studio's "auto"; Orca's range is 0..2 and the CLI refuses the whole config.
- Machine start/end G-code stays Orca's own: same Bambu blocks (21 x M1002 in the start), written against Orca's
  placeholder set; Studio's newer blocks use placeholders Orca may not know (old_filament_temp).

Bridges. Studio lays a bridge as a round thread d = 0.4 * sqrt(bridge_flow) spaced d + 0.05 (measured on a Studio
G-code: 1.6 -> 0.203 mm2 at 0.558 mm), which is Orca's *thick* bridge; Orca's thin bridge is a flat 0.4 x 0.2 strip and
its 1.6 puts down half the plastic (0.114 mm2). Orca's internal bridge reuses the bridge thread and multiplies it by
internal_bridge_flow; overhang walls take the same thread, scaled by overhang_flow_ratio (only with
set_other_flow_ratios on). So 1 / bridge_flow returns both to the plain d0.4 thread Studio used for them, and internal
bridges run at 50 mm/s — Studio's internal bridges before ADR-0007, with no recorded problems. The slow 10 mm/s x 1.6
of ADR-0007 then stays on visible bridges only: inherited by internal bridges it hung in loops over 10 % gyroid
(Gridfinity bin, 2026-10-03)."""
import glob, json, os, sys

STUDIO = os.path.expanduser("~/Library/Application Support/BambuStudio")
ORCA_APP = "/Applications/OrcaSlicer.app/Contents/Resources/profiles"
ORCA_USER = os.path.expanduser("~/Library/Application Support/OrcaSlicer/user/default")
KINDS = ("machine", "process", "filament")
META = {"name", "inherits", "from", "setting_id", "base_id", "filament_id", "version", "instantiation", "description",
        "renamed_from", "type", "print_settings_id", "filament_settings_id", "printer_settings_id", "compatible_printers",
        "compatible_printers_condition", "compatible_prints", "compatible_prints_condition", "upward_compatible_machine",
        "filament_extruder_variant", "print_extruder_id", "print_extruder_variant", "is_custom_defined"}
REJECTED = {("tree_support_wall_count", "-1")}


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


def bridges(keys):
    bf = float(one(keys.get("bridge_flow", "1")))
    inv = f"{1 / bf:.3f}".rstrip("0").rstrip(".")
    out = {"thick_bridges": "1", "thick_internal_bridges": "1", "internal_bridge_speed": "50", "internal_bridge_flow": inv}
    if bf != 1:
        out.update({"set_other_flow_ratios": "1", "overhang_flow_ratio": inv})
    return out


def convert(kind, user, version):
    studio_roots = [f"{STUDIO}/system/BBL"]
    orca_roots = [f"{ORCA_APP}/BBL", f"{ORCA_APP}/OrcaFilamentLibrary"]
    parent = user["inherits"]
    s, o = resolve(studio_roots, kind, parent), resolve(orca_roots, kind, parent)
    parity = {k: s[k] for k in s if k in o and k not in META and not k.endswith("_gcode") and one(s[k]) != one(o[k])}
    own = {k: v for k, v in user.items() if k not in META}
    keys = {**parity, **own}
    if kind == "process":
        keys.update(bridges(keys))
    keys = {k: v for k, v in keys.items() if (k, str(one(v))) not in REJECTED}
    out = {"from": "User", "version": version, "inherits": parent, "name": user["name"]}
    out.update({"process": {"print_settings_id": user["name"]}, "filament": {"filament_settings_id": [user["name"]]},
                "machine": {"printer_settings_id": user["name"]}}[kind])
    out.update(keys)
    return out, parity


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    repo = args[args.index("--repo-copy") + 1] if "--repo-copy" in args else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles", "orca")
    version = json.load(open(f"{ORCA_APP}/BBL.json"))["version"]
    users = [d for d in glob.glob(f"{STUDIO}/user/*/") if glob.glob(f"{d}*/*.json")]
    for d in users:
        for kind in KINDS:
            for f in sorted(glob.glob(f"{d}{kind}/*.json")):
                user = json.load(open(f))
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
