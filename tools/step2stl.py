#!/usr/bin/env -S uv run --quiet --with cadquery python3
"""STEP -> one binary STL per body, meshed by OCP with a fine tolerance (linear 0.01 mm, angular 0.15 rad).
Studio's own STEP importer lays coarse triangles on fillets (ADR-0003: export STL, not STEP); Fusion was not
running, so the STEP from ~/Desktop/exports is meshed here instead. Body names come from the file's
MANIFOLD_SOLID_BREP records in order (Fusion writes them in body order). Also prints bbox/volume per body.
Usage: step2stl.py <file.step> <outdir> [lin=0.01] [ang=0.15]"""
import sys, re, json
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
src, outdir = sys.argv[1], sys.argv[2]
lin = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01; ang = float(sys.argv[4]) if len(sys.argv) > 4 else 0.15
names = re.findall(r"MANIFOLD_SOLID_BREP\('([^']*)'", open(src, errors="replace").read())
rd = STEPControl_Reader(); assert rd.ReadFile(src) == IFSelect_RetDone; rd.TransferRoots(); shape = rd.OneShape()
solids = []; ex = TopExp_Explorer(shape, TopAbs_SOLID)
while ex.More(): solids.append(TopoDS.Solid_s(ex.Current())); ex.Next()
assert len(solids) == len(names), (len(solids), names)
def tri_count(s):
    n = 0; fx = TopExp_Explorer(s, TopAbs_FACE)
    while fx.More():
        t = BRep_Tool.Triangulation_s(TopoDS.Face_s(fx.Current()), TopLoc_Location()); n += t.NbTriangles() if t else 0; fx.Next()
    return n
w = StlAPI_Writer(); w.ASCIIMode = False; info = []
for i, (nm, s) in enumerate(zip(names, solids)):
    b = Bnd_Box(); BRepBndLib.AddOptimal_s(s, b, True, False); x0, y0, z0, x1, y1, z1 = b.Get()
    gp = GProp_GProps(); BRepGProp.VolumeProperties_s(s, gp)
    BRepMesh_IncrementalMesh(s, lin, False, ang, True)
    safe = re.sub(r"[^A-Za-z0-9]+", "_", nm).strip("_"); path = f"{outdir}/body-{i}-{safe}.stl"; w.Write(s, path)
    d = dict(i=i, name=nm, file=path, bbox=[round(v, 2) for v in (x0, y0, z0, x1, y1, z1)], vol=round(gp.Mass(), 1), tris=tri_count(s))
    info.append(d); print(d, flush=True)
json.dump(info, open(f"{outdir}/bodies.json", "w"), indent=1)
