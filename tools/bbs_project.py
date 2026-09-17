#!/usr/bin/env python3
"""Build and modify Bambu Studio project files (.3mf) without the UI.

  assemble <autosave_dir> <out.3mf>          full project from a Studio autosave
                                             (its settings-only .3mf + 3D/Objects/*.model)
  variant <in.3mf> <out.3mf> [--keep 1,2,3] [--set key=value ...] [--title T]
                                             keep only these object ids (as in model_settings.config),
                                             override settings in Metadata/project_settings.config
  show <in.3mf>                              objects and their ids
  retarget <in.3mf> <out.3mf> --machine M [--process P] [--filament F] [--bed B]
                                             move a foreign project (MakerWorld, another printer) onto our
                                             presets: the full preset values are written into the project,
                                             the author's *process* overrides (different_settings_to_system)
                                             are kept, their filament/machine overrides are dropped
  move <in.3mf> <out.3mf> --at x,y [--id N]  put an object's footprint centre at (x, y) on the bed — foreign
                                             projects sit in their printer's coordinates (H2S: x up to 350),
                                             on the 180 mm A1 mini that slices as "outside"; default: first item
  gcode3mf <in.gcode.3mf> <out.gcode.3mf>    turn a CLI slice export into what Studio calls a sliced file:
                                             geometry stripped, plate points at the G-code — Studio then opens
                                             it in Preview with "Print plate" active instead of as a project

Values for --set are written as strings; list-type keys (filament ones) take a single value."""
import json, os, re, sys, zipfile

def _read_zip(p):
    z = zipfile.ZipFile(p); return {n: z.read(n) for n in z.namelist()}
def _write_zip(p, files):
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        for n in ["[Content_Types].xml"] + [k for k in files if k != "[Content_Types].xml"]:
            if n in files: z.writestr(n, files[n])

def assemble(src, out):
    files = _read_zip(os.path.join(src, ".3mf"))
    objdir = os.path.join(src, "3D", "Objects")
    for f in sorted(os.listdir(objdir)):
        if f.endswith(".model"): files["3D/Objects/" + f] = open(os.path.join(objdir, f), "rb").read()
    _write_zip(out, files); print("assembled:", out, "objects:", [f for f in files if f.startswith("3D/Objects/")])

def show(p):
    files = _read_zip(p); ms = files["Metadata/model_settings.config"].decode()
    for oid, body in re.findall(r'<object id="(\d+)">(.*?)</object>', ms, re.S):
        name = re.search(r'key="name" value="([^"]*)"', body); src = re.search(r'key="source_file" value="([^"]*)"', body)
        print(f"  id {oid}: {name.group(1) if name else '?'}  ({src.group(1) if src else '-'})")

def variant(inp, out, keep=None, sets=(), title=None):
    files = _read_zip(inp)
    model = files["3D/3dmodel.model"].decode(); ms = files["Metadata/model_settings.config"].decode()
    if keep is not None:
        all_ids = re.findall(r'<object id="(\d+)">', ms); drop = [i for i in all_ids if i not in keep]
        for i in drop:
            model = re.sub(r'\s*<item objectid="%s" [^>]*/>' % i, "", model)
            m = re.search(r'<object id="%s" [^>]*>.*?</object>\s*' % i, model, re.S)
            path = re.search(r'p:path="([^"]+)"', m.group(0)).group(1) if m else None
            if m: model = model.replace(m.group(0), "")
            ms = re.sub(r'\s*<object id="%s">.*?</object>' % i, "", ms, flags=re.S)
            ms = re.sub(r'\s*<model_instance>\s*<metadata key="object_id" value="%s"/>.*?</model_instance>' % i, "", ms, flags=re.S)
            ms = re.sub(r'\s*<assemble_item object_id="%s" [^>]*/>' % i, "", ms)
            if path:
                files.pop(path.lstrip("/"), None)
                rels = files.get("3D/_rels/3dmodel.model.rels")
                if rels: files["3D/_rels/3dmodel.model.rels"] = re.sub(r'\s*<Relationship Target="%s" [^>]*/>' % re.escape(path), "", rels.decode()).encode()
        print("kept objects:", keep, "dropped:", drop)
    if title: model = re.sub(r'(<metadata name="Title">)[^<]*(</metadata>)', r'\g<1>%s\g<2>' % title, model)
    files["3D/3dmodel.model"] = model.encode(); files["Metadata/model_settings.config"] = ms.encode()
    if sets:
        cfg = json.loads(files["Metadata/project_settings.config"])
        for k, v in sets:
            if k not in cfg: print("warn: unknown key", k)
            cfg[k] = [v] if isinstance(cfg.get(k), list) else v
            print(f"set {k} = {cfg[k]}")
        # Studio marks changed keys per tab in different_settings_to_system = [process, filament, machine]
        # (";"-joined key names); keeping it in sync gives the orange "modified" markers in the UI.
        from bbs_resolve import resolve
        fil = cfg.get("filament_settings_id", ["?"]); fil = fil[0] if isinstance(fil, list) else fil
        bases = [resolve("process", cfg.get("print_settings_id", "")), resolve("filament", fil), resolve("machine", cfg.get("printer_settings_id", ""))]
        diff = cfg.get("different_settings_to_system") or ["", "", ""]
        for k, v in sets:
            hit = [i for i, b in enumerate(bases) if k in b]
            i = hit[0] if hit else 0                       # keys absent from every base (project-only) count as process
            base_v = bases[i].get(k); base_v = base_v[0] if isinstance(base_v, list) else base_v
            if base_v is None or str(base_v) != str(v):
                keys = [x for x in diff[i].split(";") if x]
                if k not in keys: keys.append(k)
                diff[i] = ";".join(keys)
        cfg["different_settings_to_system"] = diff; print("different_settings_to_system =", diff)
        files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode()
    _write_zip(out, files); print("written:", out)

# keys that describe a preset file, not a printing setting — never copied into a project
_PRESET_META = {"name", "from", "version", "inherits", "instantiation", "type", "setting_id", "description",
                "filament_id", "compatible_printers", "compatible_printers_condition", "compatible_prints",
                "compatible_prints_condition", "print_settings_id", "filament_settings_id", "printer_settings_id",
                "is_custom_defined", "_chain"}

def retarget(inp, out, machine, process=None, filament=None, bed=None):
    from bbs_resolve import resolve
    files = _read_zip(inp); cfg = json.loads(files["Metadata/project_settings.config"])
    m = resolve("machine", machine)
    process = process or m["default_print_profile"]
    dfp = m["default_filament_profile"]; filament = filament or (dfp[0] if isinstance(dfp, list) else dfp)
    p = resolve("process", process); f = resolve("filament", filament)
    for kind, base in (("process", p), ("filament", f)):
        cps = base.get("compatible_printers") or []
        if cps and machine not in cps: raise SystemExit(f"{kind} preset '{base['name']}' is not for '{machine}': {cps}")

    # author's overrides live in different_settings_to_system = [process; filament; machine] (";"-joined).
    # Process tweaks describe the model (walls, supports) — keep; filament/machine ones describe their setup — drop.
    # keys like precise_outer_wall live only in the project (Studio defaults, absent from preset files) — keep those too
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    old_n = len(cfg.get("filament_settings_id") or [1])   # the author's filament count (AMS projects: 4)
    keep = [k for k in diff[0].split(";") if k and k in cfg]
    author = {k: cfg[k] for k in keep}
    dropped = [k for k in diff[0].split(";") if k and k not in cfg] + [k for k in (diff[1] + ";" + diff[2]).split(";") if k]
    print("was    :", cfg.get("printer_settings_id"), "/", cfg.get("print_settings_id"), "/", cfg.get("filament_settings_id"))
    print("author :", author or "(no process overrides)")
    if dropped: print("dropped:", dropped)

    for base in (m, p, f):
        for k, v in base.items():
            if k not in _PRESET_META: cfg[k] = v
    # Studio 2.x hides the real BBL machine G-code: the system machine JSON has no machine_start_gcode and the
    # resolver falls through to fdm_machine_common's Ender-style placeholder (M109 S205, purge line to Y200).
    # Printing with it = wrong temperature, no nozzle wipe, purge off the bed (2026-09-17). Trusted blobs live in
    # profiles/baseline/machine-gcode-<slug>.json, snapshotted from a Studio-made project for that printer.
    slug = machine.replace("Bambu Lab ", "").replace(" 0.4 nozzle", "").replace(" ", "")
    gpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profiles", "baseline", f"machine-gcode-{slug}.json")
    if not os.path.exists(gpath): raise SystemExit(f"no trusted machine G-code for '{machine}': {gpath} (snapshot it from a Studio-made project first)")
    g = json.load(open(gpath))
    for k, v in g.items():
        if k.endswith("_gcode") and v is not None: cfg[k] = v
    print("gcode  : machine blobs from", os.path.relpath(gpath), f"(start {len(g['machine_start_gcode'])} chars)")
    # per-filament lists the author's setup left behind in project-only keys: P1S carries two extruder
    # variants (2-element lists), an AMS project carries one value per filament (4 — filament_colour,
    # filament_map, pressure_advance, fan keys, a 4×4 flush matrix). We print with one filament, so every
    # project-only list of the author's filament count is cut to its first value — otherwise Studio shows
    # four filament slots for a one-filament plate (branch stand, 2026-09-18)
    for k, v in list(cfg.items()):
        if not isinstance(v, list) or len(v) < 2 or any(k in b for b in (m, p, f)): continue
        if k == "flush_volumes_matrix": cfg[k] = ["0"]
        elif len(v) == old_n or k.startswith("filament_"): cfg[k] = v[:1]
    cfg.update(author)
    cfg["printer_settings_id"] = machine; cfg["print_settings_id"] = process; cfg["filament_settings_id"] = [filament]
    cfg["print_compatible_printers"] = p.get("compatible_printers") or [machine]
    if f.get("filament_id"): cfg["filament_ids"] = [f["filament_id"]]
    if bed: cfg["curr_bed_type"] = bed
    cfg["different_settings_to_system"] = [";".join(keep), "", ""]
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode()
    _write_zip(out, files)
    print("now    :", machine, "/", process, "/", filament, "/ bed:", cfg.get("curr_bed_type"))
    print("different_settings_to_system =", cfg["different_settings_to_system"]); print("written:", out)

def move(inp, out, at, oid=None):
    """shift a build item's translation so its footprint centre lands at `at` (mesh read with all transforms)"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mesh_slopes import load
    files = _read_zip(inp); model = files["3D/3dmodel.model"].decode()
    items = re.findall(r'<item objectid="(\d+)"', model)
    oid = oid or items[0]
    vs = [v for name, verts, _ in load(inp) if name.split()[1].split("/")[0] == oid for v in verts]
    if not vs: raise SystemExit(f"no mesh for item {oid}; items: {items}")
    cx = (min(v[0] for v in vs) + max(v[0] for v in vs)) / 2; cy = (min(v[1] for v in vs) + max(v[1] for v in vs)) / 2
    dx, dy = at[0] - cx, at[1] - cy
    def shift(m):
        t = m.group(2).split(); t[9] = f"{float(t[9]) + dx:.6f}"; t[10] = f"{float(t[10]) + dy:.6f}"
        return m.group(1) + " ".join(t) + m.group(3)
    model, n = re.subn(r'(<item objectid="%s" [^>]*transform=")([^"]+)(")' % oid, shift, model)
    if n != 1: raise SystemExit(f"item {oid}: transform not found")
    files["3D/3dmodel.model"] = model.encode(); _write_zip(out, files)
    print(f"moved item {oid}: centre ({cx:.1f}, {cy:.1f}) -> ({at[0]:g}, {at[1]:g}), shift ({dx:+.1f}, {dy:+.1f}); written: {out}")

def gcode3mf(inp, out):
    """Studio's own "export sliced file" carries no mesh: <resources/> <build/> and a model_settings.config with
    only the <plate> block. With a mesh present it loads the file as a project (Prepare, Print greyed)."""
    files = _read_zip(inp)
    if "Metadata/plate_1.gcode" not in files: raise SystemExit("no Metadata/plate_1.gcode — slice first (--slice 0 --export-3mf)")
    for n in [k for k in files if k.startswith("3D/Objects/") or k.startswith("3D/_rels/")]: files.pop(n)
    model = files["3D/3dmodel.model"].decode()
    model = re.sub(r'\s+xmlns:p="[^"]*"', "", model); model = re.sub(r'\s+requiredextensions="p"', "", model)
    model = re.sub(r"<resources>.*</resources>", "<resources>\n </resources>", model, flags=re.S)
    model = re.sub(r"<build[^>]*>.*</build>|<build/>", "<build/>", model, flags=re.S)
    files["3D/3dmodel.model"] = model.encode()
    ms = files["Metadata/model_settings.config"].decode()
    plates = re.findall(r"<plate>.*?</plate>", ms, re.S)
    keep = []
    for p in plates:
        p = re.sub(r"\s*<model_instance>.*?</model_instance>", "", p, flags=re.S)
        m = re.search(r'key="plater_id" value="(\d+)"', p); i = m.group(1) if m else "1"
        if "pattern_bbox_file" not in p:
            p = p.replace("</plate>", f'  <metadata key="pattern_bbox_file" value="Metadata/plate_{i}.json"/>\n  </plate>')
        keep.append(p)
    files["Metadata/model_settings.config"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  ' + "\n  ".join(keep) + "\n</config>\n").encode()
    si = files.get("Metadata/slice_info.config")
    if si: files["Metadata/slice_info.config"] = si.replace(b'key="printer_model_id" value=""', b'key="printer_model_id" value="N1"')
    _write_zip(out, files); print("gcode-only 3mf:", out, "plates:", len(keep))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "assemble": assemble(a[1], a[2])
    elif a[0] == "show": show(a[1])
    elif a[0] == "gcode3mf": gcode3mf(a[1], a[2])
    elif a[0] == "move":
        at = tuple(float(v) for v in a[a.index("--at") + 1].split(","))
        move(a[1], a[2], at, a[a.index("--id") + 1] if "--id" in a else None)
    elif a[0] == "retarget":
        opt = lambda n: a[a.index(n) + 1] if n in a else None
        retarget(a[1], a[2], opt("--machine"), opt("--process"), opt("--filament"), opt("--bed"))
    elif a[0] == "variant":
        keep = a[a.index("--keep") + 1].split(",") if "--keep" in a else None
        title = a[a.index("--title") + 1] if "--title" in a else None
        sets = [(s.split("=", 1)[0], s.split("=", 1)[1]) for i, s in enumerate(a) if i > 0 and a[i - 1] == "--set"]
        variant(a[1], a[2], keep, sets, title)
