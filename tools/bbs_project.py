#!/usr/bin/env python3
"""Build and modify Bambu Studio project files (.3mf) without the UI.

  assemble <autosave_dir> <out.3mf>          full project from a Studio autosave
                                             (its settings-only .3mf + 3D/Objects/*.model)
  variant <in.3mf> <out.3mf> [--keep 1,2,3] [--set key=value ...] [--title T]
                                             keep only these object ids (as in model_settings.config),
                                             override settings in Metadata/project_settings.config
  show <in.3mf>                              objects and their ids

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

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "assemble": assemble(a[1], a[2])
    elif a[0] == "show": show(a[1])
    elif a[0] == "variant":
        keep = a[a.index("--keep") + 1].split(",") if "--keep" in a else None
        title = a[a.index("--title") + 1] if "--title" in a else None
        sets = [(s.split("=", 1)[0], s.split("=", 1)[1]) for i, s in enumerate(a) if i > 0 and a[i - 1] == "--set"]
        variant(a[1], a[2], keep, sets, title)
