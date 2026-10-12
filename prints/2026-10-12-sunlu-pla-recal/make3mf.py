"""make3mf.py out.3mf name=file.stl[@x,y][:key=val,key=val] ...  — plain 3MF, one object per STL, per-object settings."""
import sys, zipfile, trimesh, numpy as np
out = sys.argv[1]; objs = []
for i, a in enumerate(sys.argv[2:]):
    head, _, kv = a.partition(":"); name, _, rest = head.partition("="); f, _, at = rest.partition("@")
    m = trimesh.load(f); x, y = (float(v) for v in at.split(",")) if at else (90, 90)
    c = m.bounds.mean(0); m.apply_translation([x - c[0], y - c[1], -m.bounds[0][2]])
    objs.append((2 * i + 1, name, m, [p.split("=", 1) for p in kv.split(",") if p]))
NS = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"'
model = [f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n<resources>']
for oid, name, m, _ in objs:
    model.append(f'<object id="{oid}" type="model"><mesh><vertices>')
    model += [f'<vertex x="{v[0]:.5f}" y="{v[1]:.5f}" z="{v[2]:.5f}"/>' for v in m.vertices]
    model.append('</vertices><triangles>')
    model += [f'<triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>' for t in m.faces]
    model.append('</triangles></mesh></object>')
model.append('</resources>\n<build>')
model += [f'<item objectid="{oid}" printable="1"/>' for oid, *_ in objs]
model.append('</build>\n</model>')
cfg = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>']
for oid, name, m, kv in objs:
    cfg.append(f'  <object id="{oid}">\n    <metadata key="name" value="{name}"/>\n    <metadata key="extruder" value="1"/>')
    cfg += [f'    <metadata key="{k}" value="{v}"/>' for k, v in kv]
    cfg.append(f'    <part id="1" subtype="normal_part">\n      <metadata key="name" value="{name}"/>\n    </part>\n  </object>')
cfg.append('</config>')
ct = '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
rels = '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels)
    z.writestr("3D/3dmodel.model", "\n".join(model)); z.writestr("Metadata/model_settings.config", "\n".join(cfg))
print("wrote", out, [(n, m.extents.round(1).tolist(), kv) for _, n, m, kv in objs])
