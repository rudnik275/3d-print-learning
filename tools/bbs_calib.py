#!/usr/bin/env python3
"""Build Bambu Studio calibration plates without the GUI wizard, replicating CalibUtils.cpp.

  bbs_calib.py flow1 <base_project.3mf> <out.3mf>            flow-rate coarse: 9 blocks, -20..+20 %
  bbs_calib.py flow2 <base_project.3mf> <out.3mf> <coarse>   flow-rate fine: 10 blocks, -9..0 % on top of
                                                             the coarse flow ratio (e.g. 0.95)

base_project supplies printer/filament/process settings (Metadata/project_settings.config).
Per-object settings follow the wizard: print_flow_ratio = 1 + k/100, wall_loops 3, top 5, bottom 1,
infill 35 %, monotonic top, no ironing, detect_thin_wall; global reduce_crossing_wall = 1."""
import json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bbs_project import _read_zip, _write_zip
from bbs_rebuild import HEAD, TAIL

CALIB = "/Applications/BambuStudio.app/Contents/Resources/calib/filament_flow"
BED = 180.0   # A1 mini

def generic_objects(path):
    """objects of a plain 3MF: [(name, verts, tris)] with build transforms applied"""
    z = zipfile.ZipFile(path); x = z.read("3D/3dmodel.model").decode("utf8", "ignore")
    objs = {}
    for tag, body in re.findall(r'(<object [^>]*>)(.*?)</object>', x, re.S):
        oid = re.search(r'\bid="(\d+)"', tag).group(1); nm = re.search(r'\bname="([^"]*)"', tag)
        name = nm.group(1) if nm else f"object_{oid}"
        vs = [tuple(float(v) for v in m) for m in re.findall(r'<vertex\s+x="([^"]+)"\s+y="([^"]+)"\s+z="([^"]+)"', body)]
        ts = [tuple(int(v) for v in m) for m in re.findall(r'<triangle\s+v1="(\d+)"\s+v2="(\d+)"\s+v3="(\d+)"', body)]
        if vs: objs[oid] = (name, vs, ts)
    out = []
    for tag in re.findall(r'<item [^>]*>', x):
        oid = re.search(r'objectid="(\d+)"', tag).group(1); trm = re.search(r'transform="([^"]+)"', tag)
        tr = trm.group(1) if trm else "1 0 0 0 1 0 0 0 1 0 0 0"
        if oid not in objs: continue
        name, vs, ts = objs[oid]; t = [float(v) for v in tr.split()]
        vs = [(t[0]*a+t[3]*b+t[6]*c+t[9], t[1]*a+t[4]*b+t[7]*c+t[10], t[2]*a+t[5]*b+t[8]*c+t[11]) for a, b, c in vs]
        out.append((name, vs, ts))
    return out

def build(base, out, objects, per_obj, global_sets, title):
    """objects: [(name, verts, tris, (cx, cy))] placed with their bbox centre at (cx, cy), z on the bed"""
    files = _read_zip(base)
    cfg = json.loads(files["Metadata/project_settings.config"])
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    for k, v in global_sets.items():
        cfg[k] = v; keys = [x for x in diff[0].split(";") if x]; keys.append(k) if k not in keys else None; diff[0] = ";".join(keys)
    cfg["different_settings_to_system"] = diff
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode()
    model = [files["3D/3dmodel.model"].decode().split("<resources>")[0] + "<resources>\n"]
    model[0] = re.sub(r'(<metadata name="Title">)[^<]*(</metadata>)', r'\g<1>%s\g<2>' % title, model[0])
    items, rels, ms_objs, ms_inst = [], [], [], []
    for n, (name, vs, ts, (cx, cy)) in enumerate(objects, 1):
        xs, ys, zs = [v[0] for v in vs], [v[1] for v in vs], [v[2] for v in vs]
        ox, oy, oz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2   # Studio centres meshes
        part = 65536 + n; path = f"3D/Objects/object_{n}.model"
        xml = [HEAD, f'  <object id="{part}" p:UUID="{n:04x}0000-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n   <mesh>\n    <vertices>\n']
        xml += [f'     <vertex x="{x-ox:.6g}" y="{y-oy:.6g}" z="{z-oz:.6g}"/>\n' for x, y, z in vs]
        xml += ['    </vertices>\n    <triangles>\n'] + [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in ts] + ['    </triangles>\n', TAIL]
        files[path] = "".join(xml).encode()
        model.append(f'  <object id="{n}" p:UUID="{n:08x}-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n   <components>\n'
                     f'    <component p:path="/{path}" objectid="{part}" p:UUID="{n:04x}0000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>\n')
        zh = (max(zs)-min(zs))/2
        items.append(f'  <item objectid="{n}" p:UUID="{n:08x}-b1ec-4553-aec9-835e5b724bb4" transform="1 0 0 0 1 0 0 0 1 {cx:.4f} {cy:.4f} {zh:.4f}" printable="1"/>\n')
        rels.append(f' <Relationship Target="/{path}" Id="rel-{n}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n')
        meta = "".join(f'    <metadata key="{k}" value="{v}"/>\n' for k, v in per_obj(name).items())
        ms_objs.append(f'  <object id="{n}">\n    <metadata key="name" value="{name}"/>\n    <metadata key="extruder" value="1"/>\n{meta}'
                       f'    <part id="{part}" subtype="normal_part">\n      <metadata key="name" value="{name}"/>\n      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                       f'      <mesh_stat face_count="{len(ts)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n  </object>\n')
        ms_inst.append(f'    <model_instance>\n      <metadata key="object_id" value="{n}"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{100+n}"/>\n    </model_instance>\n')
    model.append(" </resources>\n <build>\n" + "".join(items) + " </build>\n</model>\n")
    files["3D/3dmodel.model"] = "".join(model).encode()
    files["3D/_rels/3dmodel.model.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + "".join(rels) + "</Relationships>\n").encode()
    files["Metadata/model_settings.config"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(ms_objs) +
        '  <plate>\n    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value=""/>\n    <metadata key="locked" value="false"/>\n    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
        + "".join(ms_inst) + "  </plate>\n</config>\n").encode()
    for k in list(files):
        if k.startswith("3D/Objects/") and not any(k == f"3D/Objects/object_{i}.model" for i in range(1, len(objects)+1)): del files[k]
    _write_zip(out, files); print("written:", out, "objects:", [o[0] for o in objects])

def flow_plate(base, out, pass_no, coarse=1.0):
    src = os.path.join(CALIB, f"flowrate-test-pass{pass_no}.3mf")
    objs = generic_objects(src)
    def mod(name):
        s = name[9:]; return -float(s[1:]) if s.startswith("m") else float(s)
    objs.sort(key=lambda o: mod(o[0]))
    size = max(max(v[0] for v in o[1]) - min(v[0] for v in o[1]) for o in objs)
    cols = 3 if len(objs) <= 9 else 4; rows = -(-len(objs) // cols); pitch = size + 8
    placed = []
    for i, (name, vs, ts) in enumerate(objs):
        r, c = divmod(i, cols)
        cx = BED/2 + (c - (cols-1)/2) * pitch; cy = BED/2 + ((rows-1)/2 - r) * pitch
        placed.append((name, vs, ts, (cx, cy)))
    def per_obj(name):
        return {"print_flow_ratio": f"{coarse * (1 + mod(name)/100):.4f}", "wall_loops": "3", "top_shell_layers": "5",
                "bottom_shell_layers": "1", "sparse_infill_density": "35%", "ironing_type": "no ironing",
                "top_surface_pattern": "monotonic", "detect_thin_wall": "1"}
    build(base, out, placed, per_obj, {"reduce_crossing_wall": "1"}, f"Flow rate pass {pass_no}")
    print("layout: %d objects, block %.1f mm, pitch %.1f mm, rows from back(+Y) to front: " % (len(objs), size, pitch) + " | ".join(f"{mod(o[0]):+.0f}%" for o in objs))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "flow1": flow_plate(a[1], a[2], 1)
    elif a[0] == "flow2": flow_plate(a[1], a[2], 2, float(a[3]))
    else: print(__doc__)
