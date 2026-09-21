#!/usr/bin/env -S uv run --quiet --with trimesh --with numpy --with shapely --with rtree --with scipy --with networkx python3
"""Kindle retro-TV (Fusion, 13 bodies, PETG one colour) -> six A1 mini plates as Studio projects.

Bodies (Fusion Y up, Z = depth, front at Z≈0): box (2) = middle C-shell 125×170×120 (roof with 12 slots and a
round bump, back wall with cable hole, floor with pin holes, 9-mm inner lips at the front for the bezel);
box / box (1) = right / left rounded cheeks 59×165×120 (same lips, 3 tongues at the back edge into box (2));
face right = screen bezel 173×155×26 (flat front, 45° bevel round a 123×91 window, 8 snap fingers + 4 corner
hooks on the back); vent = louvred speaker grille 48×155×30 (28 slats ~2 mm, hollow dome Ø23 11 mm proud);
leg1..4 = leaning tapered legs (foot Ø18, 25 tall, lean 36°); Pin body ×4 = 2.6×3.6×14.7 clips leg->floor.

Orientation per part (why in README.md): shells back-down (rounded back edges become the only overhang band,
lips at z 98 get tree supports from the inner back surface, slots turn into vertical slits); bezel front-down
(flat face on textured PEI, bevel = 45° overhang, hooks supported); vent on its straight edge (slats vertical,
dome half-overhang, brim); legs foot-down = as assembled, so the 36° overhang side faces inward/down; pins flat.

Usage: build.py <mesh dir from tools/step2stl.py> <base dir: base-020mm/016mm/012mm.3mf from retarget> <out dir>"""
import sys, os, math, zipfile
import numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
from bbs_calib import build, stl_mesh
MESH, BASE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

def body(i):
    f = [n for n in os.listdir(MESH) if n.startswith(f"body-{i}-")][0]
    vs, ts = stl_mesh(os.path.join(MESH, f)); return np.array(vs, float), ts

# proper rotations (det +1) Fusion (X,Y,Z) -> bed (x,y,z); a reflection would need the triangle winding flipped
BACK_DOWN = lambda v: np.c_[v[:, 0], -v[:, 1], -v[:, 2]]          # back wall (Z=120) on the bed, TV top toward bed front
FRONT_DOWN_90 = lambda v: np.c_[-v[:, 1], v[:, 0], v[:, 2]]       # bezel: front (Z=-2) down, 173-mm side along bed Y
EDGE_DOWN = lambda v: np.c_[v[:, 1], v[:, 2], v[:, 0]]            # vent / pins: X down -> length along bed x, front toward bed front
FOOT_DOWN = lambda v: np.c_[v[:, 0], -v[:, 2], v[:, 1]]           # legs: Y up stays up = as assembled

def rot_z(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.c_[c * v[:, 0] - s * v[:, 1], s * v[:, 0] + c * v[:, 1], v[:, 2]]

def leg(i):
    """foot-down, then turned so the lean (foot -> socket end) points to +y: the overhang belly then faces the
    bed's back, where seam_position=back also puts the seam — both end up under the TV, facing inward."""
    v, t = body(i); v = FOOT_DOWN(v); z0, z1 = v[:, 2].min(), v[:, 2].max()
    foot = v[v[:, 2] < z0 + 0.05][:, :2].mean(0); top = v[v[:, 2] > z1 - 0.05][:, :2].mean(0)
    lean = top - foot; ang = 90 - math.degrees(math.atan2(lean[1], lean[0]))
    v = rot_z(v, ang); print(f"  leg body {i}: lean {np.linalg.norm(lean):.1f} mm, turned {ang:+.0f}°")
    return v, t

def louver_thickness(v, t):
    """slats are thin slanted plates; at mid-height each is a parallelogram: thickness ≈ 2·area/perimeter"""
    m = trimesh.Trimesh(v, np.array(t), process=False); z = v[:, 2].min() + 15.0
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]); p2, _ = s.to_2D()
    th = [2 * pg.area / pg.length for pg in p2.polygons_full if 6 < (pg.bounds[2] - pg.bounds[0]) < 9 and 10 < (pg.bounds[3] - pg.bounds[1]) < 13]
    return float(np.median(th)), len(th)

PKG = {"resolution": "0.004", "slice_closing_radius": "0.01", "precise_outer_wall": "1",     # ADR-0003, ADR-0004
       "reduce_crossing_wall": "1", "max_travel_detour_distance": "300",
       "top_surface_pattern": "monotonic", "enable_prime_tower": "0"}
SUPPORT = {"enable_support": "1", "support_type": "tree(auto)", "support_top_z_distance": "0.25",   # PETG welds to supports at 0.2
           "support_threshold_angle": "30"}
SHELL = {**PKG, **SUPPORT, "support_on_build_plate_only": "0",     # lips at z 98 hang over the inner back surface
         "wall_loops": "3", "brim_type": "no_brim", "seam_position": "back"}

def strip_stale(path):
    """the base container came from a real Studio project: drop its slice leftovers so nothing stale rides along"""
    z = zipfile.ZipFile(path); keep = {n: z.read(n) for n in z.namelist()
        if not (n.startswith("Metadata/plate_") or n.startswith("Metadata/pick_") or n.startswith("Metadata/top_")
                or n in ("Metadata/slice_info.config", "Metadata/cut_information.xml", "Metadata/layer_config_ranges.xml"))}
    dropped = sorted(set(z.namelist()) - set(keep)); z.close()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as w:
        for n in ["[Content_Types].xml"] + [k for k in keep if k != "[Content_Types].xml"]: w.writestr(n, keep[n])
    if dropped: print("  stripped:", dropped)

def plate(name, base, objects, per_obj, sets, title):
    out = os.path.join(OUT, f"{name}.3mf")
    objs = [(n, [tuple(p) for p in v], t, xy) for n, v, t, xy in objects]
    build(os.path.join(BASE, base), out, objs, per_obj, sets, title); strip_stale(out)
    for n, v, t, (cx, cy) in objects:
        ex = v.max(0) - v.min(0); print(f"  {n}: {ex[0]:.1f} x {ex[1]:.1f} x {ex[2]:.1f} mm at ({cx}, {cy}) -> x {cx-ex[0]/2:.1f}..{cx+ex[0]/2:.1f}, y {cy-ex[1]/2:.1f}..{cy+ex[1]/2:.1f}")

# 1. bezel — 0.12 Fine: the 45° bevel is the most visible surface of the whole TV
v, t = body(8); v = FRONT_DOWN_90(v)
plate("bezel", "base-012mm.3mf", [("bezel", v, t, (100.0, 90.0))], lambda n: {},
      {**PKG, **SUPPORT, "support_threshold_angle": "50",       # hooks (90°) yes, the 45° bevel no
       "support_on_build_plate_only": "0", "wall_loops": "3", "brim_type": "no_brim", "elefant_foot_compensation": "0.15"},
      "Kindle TV - bezel")

# 2-4. shells — 0.16 High Quality: big flat vertical walls, outer wall 60 mm/s against ripple
for name, i, title in (("box2", 12, "Kindle TV - middle box"), ("cap-right", 10, "Kindle TV - right cheek"), ("cap-left", 11, "Kindle TV - left cheek")):
    v, t = body(i); v = BACK_DOWN(v)
    plate(name, "base-016mm.3mf", [(name, v, t, (100.0, 90.0))], lambda n: {}, SHELL, title)

# 5. vent — 0.12 Fine (dome top and rounded end are shallow slopes), on its straight edge, brim; slats sized to whole lines
v, t = body(9); v = EDGE_DOWN(v)
th, n = louver_thickness(v, t); loops = 2; lw = min(0.5, max(0.4, th / (2 * loops)))
print(f"  vent: {n} slats, thickness {th:.2f} mm -> {loops} loops x {lw:.2f} mm per side")
VENT = {**PKG, "wall_loops": "3", "outer_wall_line_width": f"{lw:.2f}", "inner_wall_line_width": f"{lw:.2f}",
        "brim_type": "outer_only", "brim_width": "4", "seam_position": "back"}
plate("vent-nosup", "base-012mm.3mf", [("vent", v, t, (97.5, 90.0))], lambda n: {}, VENT, "Kindle TV - speaker grille")   # slicer warns: floating regions (dome bottom)
plate("vent-sup", "base-012mm.3mf", [("vent", v, t, (97.5, 90.0))], lambda n: {},
      {**VENT, **SUPPORT, "support_on_build_plate_only": "1"}, "Kindle TV - speaker grille (dome supported)")
# trees also grew between the louvres up to the top rail (z 43): Studio treats the rail over the slat tops as an
# overhang, not a bridge (bridge_no_support=1 changed nothing). A support blocker above the dome's equator keeps
# the dome trees (in front, open air) and drops the rest; then 0.08 layers on the rounded end's top band (check 15).
from bbs_blocker import blocker
from bbs_project import ranges
blocker(os.path.join(OUT, "vent-sup.3mf"), os.path.join(OUT, "vent-blk.3mf"), 1, (15, 70, 24, 180, 110, 50))
ranges(os.path.join(OUT, "vent-blk.3mf"), os.path.join(OUT, "vent.3mf"), 1, 42, 48, [("layer_height", "0.08")])

# 6. legs + pins — 0.20 Standard; pins solid
objs = []
for k, i in enumerate((4, 5, 6, 7)):
    v, t = leg(i); objs.append((f"leg{k+1}", v, t, (60.0 + 30.0 * k, 100.0)))
for k in range(6):
    v, t = body(k % 4); objs.append((f"pin{k+1}", EDGE_DOWN(v), t, (55.0 + 20.0 * k, 60.0)))
plate("legs", "base-020mm.3mf", objs, lambda n: {"sparse_infill_density": "100%"} if n.startswith("pin") else {},
      {**PKG, "wall_loops": "3", "brim_type": "no_brim", "seam_position": "back"}, "Kindle TV - legs and pins")
