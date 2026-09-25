"""Folding sun visor for Lowrance Elite FS 9 — parametric model (build123d).

Coordinates: origin = unit centre (Lowrance mounting template), X right, Y up,
Z = depth: bezel rear face at z=0, front of bezel at z~-15 (toward the viewer is -Z).

Mechanism ("clamshell"):
  rail  — C-channel clip on the bezel rim (slides down from the top), carries the roof hinge
          and a keeper with a hole at the bottom of each side;
  roof  — hinged to the rail on an X axis in front of the bezel top, folds down over the screen;
  flaps — hinged to the roof side edges, fold flat under the roof; deployed, a peg on each flap
          snaps into the rail keeper and locks the roof open.
All pins are M3 bolts + nylock nuts. Each part is split at x=0 into mirrored halves.
"""
import json, math, sys
from pathlib import Path
from shapely.geometry import Polygon as SPoly, LineString
from build123d import (Box, Cylinder, Pos, Rot, Face, Wire, Vector, Axis, Plane,
                       extrude, export_step, export_stl, Compound)

HERE = Path(__file__).parent
TEMPLATE = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "fs9_template_geometry.json"

# ---- parameters -------------------------------------------------------------
CL = 0.5          # clearance clip -> bezel rim
WT = 3.2          # clip wall
LIP_BACK = 6.0    # how far the rear lip reaches behind the bezel
LIP_FRONT = 3.5   # how far the side front lips reach over the bezel face
Z_BACK = (0.2, 3.4)       # rear lip (behind the bezel rear face z=0)
Z_FRONT = -19.6           # front of the clip
Z_FLIP = -15.3            # rear face of the front lips (bezel face ~ -15.0 near the edge)
Y_BOTTOM = -35.5          # clip side ears end here

D = 100.0         # roof depth
T_ROOF = 3.0
YH, ZH = None, -28.0      # roof hinge axis (YH computed from the rail)
R_KN, R_CUT, R_PIN = 3.5, 3.9, 1.65   # knuckle, knuckle clearance, M3 hole
RAIL_HINGES = (30.0, 115.0)           # hinge group centres (right half)

T_FLAP = 2.4
FLAP_U0 = 4.5     # flap rear edge, measured forward from the roof axis
FLAP_Y_BOTTOM = -35.0
FLAP_H_FRONT = 50.0
PEG_R, PEG_L = 2.0, 2.6
PEG_U, PEG_Y = 9.0, -29.5


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_x(r, x0, x1, y, z):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def cyl_z(r, z0, z1, x, y):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def ext(poly: SPoly, z0, z1):
    pts = list(poly.exterior.coords)[:-1]
    face = Face(Wire.make_polygon([Vector(x, y, z0) for x, y in pts], close=True))
    solid = extrude(face, amount=z1 - z0, dir=(0, 0, 1))
    return solid


bezel = SPoly(json.loads(TEMPLATE.read_text())["product_outline_bezel"]).buffer(0)
inner = bezel.buffer(CL, join_style=1)
outer = bezel.buffer(CL + WT, join_style=1)
rim_top = LineString([(0, -300), (0, 300)]).intersection(bezel).bounds[3]      # 81.8
Y_SHELF0, Y_SHELF1 = rim_top + CL, rim_top + CL + WT
YH = (Y_SHELF0 + Y_SHELF1) / 2
XW = max(x for x, y in outer.exterior.coords)                           # clip outer half-width
X_FLAP = XW + 1.0 + T_FLAP / 2                                           # flap hinge axis x
Y_FLAP = YH - T_ROOF / 2 - 0.4 - T_FLAP / 2                              # flap axis y (folded flap under roof)
X_ROOF = X_FLAP - R_CUT                                                  # roof plate side edge
X_KEEP0 = X_FLAP + T_FLAP / 2 + 0.4                                      # keeper plate inner face
X_KEEP1 = X_KEEP0 + 2.4
Z_FLAP_REAR = ZH - FLAP_U0
PEG_Z = ZH - PEG_U


def rail_half():
    clip = box(0, 200, Y_BOTTOM, 150, -80, 20)
    wall = (ext(outer, Z_FRONT, Z_BACK[1]) - ext(inner, Z_FRONT, Z_BACK[1])) & clip
    back = (ext(inner, *Z_BACK) - ext(bezel.buffer(-LIP_BACK), *Z_BACK)) & clip
    front = (ext(inner, Z_FRONT, Z_FLIP) - ext(bezel.buffer(-LIP_FRONT), Z_FRONT, Z_FLIP)) \
        & box(0, 200, Y_BOTTOM, 60, -80, 20)
    shelf = box(0, XW - 2, Y_SHELF0, Y_SHELF1, ZH, Z_FRONT + 0.5) - cyl_x(R_CUT, -1, 200, YH, ZH)
    rail = wall + back + front + shelf
    for c in RAIL_HINGES:
        for x0, x1 in ((c - 10.4, c - 4.4), (c + 4.4, c + 10.4)):
            rail += cyl_x(R_KN, x0, x1, YH, ZH) + box(x0, x1, Y_SHELF0, Y_SHELF1, ZH, ZH + R_CUT + 0.5)
        rail -= cyl_x(R_PIN, c - 12, c + 12, YH, ZH)
    # centre splice flange (M3x12 x2)
    rail += box(0, 5, Y_SHELF1 - 0.5, Y_SHELF1 + 11.5, Z_FRONT, Z_BACK[1])
    for z in (Z_FRONT + 5, Z_BACK[1] - 5):
        rail -= cyl_x(R_PIN, -1, 6, Y_SHELF1 + 6, z)
    # keeper: bridge behind the flap rear edge + outer plate with the peg hole
    y0, y1 = FLAP_Y_BOTTOM - 0.5, PEG_Y + 6
    rail += box(XW - 1.7, X_KEEP1, y0, y1, Z_FLAP_REAR + 0.4, Z_FRONT + 0.8)
    rail += box(X_KEEP0, X_KEEP1, y0, y1, PEG_Z - 4.5, Z_FLAP_REAR + 0.4)
    rail -= cyl_x(PEG_R + 0.2, X_KEEP0 - 1, X_KEEP1 + 1, PEG_Y, PEG_Z)
    return rail


def roof_half():
    roof = box(0, X_ROOF, YH - T_ROOF / 2, YH + T_ROOF / 2, ZH - D, ZH) + cyl_x(R_KN, 0, X_ROOF, YH, ZH)
    for c in RAIL_HINGES:     # clear the rail knuckles + bolt head / nut
        roof -= cyl_x(R_CUT, c - 14.3, c - 4.4, YH, ZH)
        roof -= cyl_x(R_CUT, c + 4.4, c + 14.3, YH, ZH)
        roof -= cyl_x(R_PIN, c - 5, c + 5, YH, ZH)
    # splice rib (M3x12 x2) + front stiffening rib
    roof += box(0, 5, YH + T_ROOF / 2 - 0.5, YH + 11.5, ZH - D + 4, ZH - 8)
    for u in (25, D - 25):
        roof -= cyl_x(R_PIN, -1, 6, YH + 7, ZH - u)
    roof += box(0, X_ROOF, YH + T_ROOF / 2 - 0.5, YH + 5, ZH - D, ZH - D + 3)
    # flap hinge: roof knuckles + webs
    for u0, u1 in ((8, 14), (22.8, 28.8), (D - 28.8, D - 22.8), (D - 14, D - 8)):
        roof += cyl_z(R_KN, ZH - u1, ZH - u0, X_FLAP, Y_FLAP)
        roof += box(X_ROOF - 0.5, X_FLAP, YH - T_ROOF / 2, Y_FLAP + R_KN, ZH - u1, ZH - u0)
    for u0, u1 in ((6, 31), (D - 31, D - 6)):
        roof -= cyl_z(R_PIN, ZH - u1, ZH - u0, X_FLAP, Y_FLAP)
    return roof


def flap_half():
    z_front = ZH - (D - 3)
    pts = [(Z_FLAP_REAR, Y_FLAP), (z_front, Y_FLAP), (z_front, Y_FLAP - FLAP_H_FRONT), (Z_FLAP_REAR, FLAP_Y_BOTTOM)]
    x0 = X_FLAP - T_FLAP / 2
    face = Face(Wire.make_polygon([Vector(x0, y, z) for z, y in pts], close=True))
    flap = extrude(face, amount=T_FLAP, dir=(1, 0, 0))
    for u0, u1 in ((3.5, 14.0), (22.8, 32.3), (D - 32.3, D - 22.8), (D - 14.0, D - 2)):
        flap -= cyl_z(R_CUT, ZH - u1, ZH - u0, X_FLAP, Y_FLAP)
    for u0, u1 in ((14.4, 22.4), (D - 22.4, D - 14.4)):
        flap += cyl_z(R_KN, ZH - u1, ZH - u0, X_FLAP, Y_FLAP)
        flap -= cyl_z(R_PIN, ZH - u1 - 1, ZH - u0 + 1, X_FLAP, Y_FLAP)
    flap += cyl_x(PEG_R, X_FLAP + T_FLAP / 2 - 0.5, X_FLAP + T_FLAP / 2 + PEG_L, PEG_Y, PEG_Z)
    return flap


def unit_ghost():
    b = ext(bezel, -15.0, 0.0)
    housing = box(-136, 136, -72, 71, 0, 92)
    screen = box(-110, 88, -59, 59, -15.4, -15.0)
    return b + housing, screen


if __name__ == "__main__":
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    print(f"YH={YH:.2f} ZH={ZH} XW={XW:.2f} X_FLAP={X_FLAP:.2f} Y_FLAP={Y_FLAP:.2f} X_ROOF={X_ROOF:.2f}")
    parts = {"rail_R": rail_half(), "roof_R": roof_half(), "flap_R": flap_half()}
    for name in list(parts):
        parts[name.replace("_R", "_L")] = parts[name].mirror(Plane.YZ)
    unit, screen = unit_ghost()
    for name, p in parts.items():
        export_stl(p, str(out / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.2)
        bb = p.bounding_box()
        print(f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  vol {p.volume/1000:.1f} cm3")
    export_stl(unit, str(out / "unit.stl"), tolerance=0.2)
    export_stl(screen, str(out / "screen.stl"), tolerance=0.2)
    export_step(Compound(children=list(parts.values())), str(out / "fs9_visor_open.step"))
    # folded / closed states
    ax_roof = Axis((0, YH, ZH), (1, 0, 0))
    fold = {"flap_R": -90, "flap_L": 90}
    for n, a in fold.items():
        f = parts[n].rotate(Axis((math.copysign(X_FLAP, a * -1), Y_FLAP, 0), (0, 0, 1)), a)
        export_stl(f, str(out / f"{n}_folded.stl"), tolerance=0.05, angular_tolerance=0.2)
        export_stl(f.rotate(ax_roof, -90), str(out / f"{n}_closed.stl"), tolerance=0.05, angular_tolerance=0.2)
    for n in ("roof_R", "roof_L"):
        export_stl(parts[n].rotate(ax_roof, -90), str(out / f"{n}_closed.stl"), tolerance=0.05, angular_tolerance=0.2)
    print("ok")
