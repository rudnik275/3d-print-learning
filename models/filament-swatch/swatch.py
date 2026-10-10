#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["build123d", "trimesh", "manifold3d", "numpy", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Filament swatch in the Bambu Lab card format: 24 x 24 x 2 mm, snap hole for a 3.1 mm pin in the top-left
corner, the filament name debossed 0.8 mm into the top. Sliced in OrcaSlicer the way everyday prints are.

  swatch.py --extract "Swatch Display Board.3mf"
      one time: take Bambu's card mesh out of their 3MF and keep it next to this script (bambu-card.stl, not in git)
  swatch.py "SUNLU" "PLA Matte" "Oak" --filament "SUNLU Matte @BBL A1M" [--process P] [--font F.ttf] [--send]
      line 1 goes right of the snap hole, lines 2-3 run full width below it;
      out/<name>.gcode.3mf -> open in Orca, Slice plate -> Print plate. --send uploads it and starts the print.

Why each part exists:
- The card is Bambu's own mesh, not a redrawn one: its hole is a snap (a 2.95 mm circle with two S-shaped slits
  that spring over the 3.1 mm pin of Bambu's board and organizers), and its edges carry 0.1 mm chamfers. Its license
  (MakerWorld 14863, Standard Digital File License) forbids redistributing it, so the repo keeps only this script.
- Debossed, not raised: the card stays 2 mm and flat, so it stacks on a pin like Bambu's own cards.
  0.8 mm = 4 layers at 0.20, the depth of the most printed text-swatch profile on 14863.
- DIN Alternate Bold: at ~5 mm its strokes are ~0.7 mm wide, which a 0.4 nozzle keeps open; light fonts close up.
- Process 0.20mm Standard + the print-model quality package: the swatch shows the filament as everyday prints do.
  elefant_foot_compensation stays 0, as in Bambu's own swatch profile, so the snap fits like theirs."""
import argparse, glob, os, re, subprocess, sys, zipfile
import numpy as np, trimesh
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.join(HERE, "bambu-card.stl")
REPO = os.path.dirname(os.path.dirname(HERE))
FONT = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
SCRIPTS = os.environ.get("PRINT_MODEL_SCRIPTS", os.path.expanduser("~/dev/bambu-print-model/skills/print-model/scripts"))
DEPTH, T, MARGIN, GAP, MIN_FONT = 0.8, 2.0, 1.6, 1.8, 3.5
QUALITY = ["resolution=0.004", "slice_closing_radius=0.01", "precise_outer_wall=1", "wall_generator=classic",
           "reduce_crossing_wall=1", "max_travel_detour_distance=300", "no_slow_down_for_cooling_on_outwalls=1",
           "top_surface_pattern=monotonic"]
NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
SOURCE = "MakerWorld 14863 (Swatch Display Board by Bambu Lab), profile 14645 '0.2mm layer, 5 top&bot layer swatch'"


def hole_bounds(card):
    sec = card.section(plane_origin=[0, 0, T / 2], plane_normal=[0, 0, 1]).to_2D(to_2D=np.eye(4))[0]
    return max(sec.polygons_full, key=lambda g: g.area).interiors[0].bounds


def extract(path):
    """the 24 x 24 x 2 mesh in Bambu's 3MF -> bambu-card.stl: thickness on Z, card on 0..24, hole top-left"""
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".model"):
                continue
            for o in ET.fromstring(z.read(name)).iter(NS + "object"):
                m = o.find(NS + "mesh")
                if m is None:
                    continue
                v = np.array([[float(x.get(k)) for k in "xyz"] for x in m.iter(NS + "vertex")])
                f = np.array([[int(x.get(k)) for k in ("v1", "v2", "v3")] for x in m.iter(NS + "triangle")])
                me = trimesh.Trimesh(v, f, process=True)
                if not np.allclose(sorted(me.extents), [T, 24, 24], atol=0.05):
                    continue
                axis = int(np.argmin(me.extents))
                if axis != 2:
                    me.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0] if axis == 1 else [0, 1, 0]))
                me.apply_translation(-me.bounds[0])
                for _ in range(4):
                    hb = hole_bounds(me)
                    if (hb[0] + hb[2]) / 2 < 12 < (hb[1] + hb[3]) / 2:
                        break
                    me.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1], [12, 12, 0]))
                me.export(CARD)
                print(f"{CARD}: {me.extents.round(2).tolist()} mm, hole {np.round(hole_bounds(me), 2).tolist()}")
                return
    sys.exit(f"no 24 x 24 x 2 card in {path}")


def text(s, size, font):
    from build123d import Text, extrude, Align
    sol = extrude(Text(s, font_size=size, font_path=font, align=(Align.CENTER, Align.CENTER)), amount=DEPTH + 0.2)
    bb = sol.bounding_box()
    return sol, bb.max.X - bb.min.X, bb.max.Y - bb.min.Y


def fit(s, w, h, font):
    _, tw, th = text(s, 10, font)
    return 10 * min(w / tw, h / th)


def build(lines, font, out_stl):
    from build123d import Pos, Compound, export_stl
    card = trimesh.load(CARD)
    hb = hole_bounds(card)
    r1 = (hb[2] + 1.2, 24 - MARGIN, hb[1], 24 - MARGIN)     # x0 x1 y0 y1: right of the hole
    r2 = (MARGIN, 24 - MARGIN, MARGIN, hb[1] - 1.0)          # full width below it
    z0 = T - DEPTH
    s1 = min(fit(lines[0], r1[1] - r1[0], r1[3] - r1[2], font), 7.0)
    sol, _, _ = text(lines[0], s1, font)
    parts, sizes = [sol.moved(Pos((r1[0] + r1[1]) / 2, (r1[2] + r1[3]) / 2, z0))], [s1]
    def lower_size(ls):   # one size for all lower lines, never above line 1
        h_each = (r2[3] - r2[2] - GAP * (len(ls) - 1)) / len(ls)
        return min(min(fit(s, r2[1] - r2[0], h_each, font) for s in ls), s1)

    rest = lines[1:]
    if len(rest) == 1 and " " in rest[0] and lower_size(rest) < MIN_FONT:
        w = rest[0].split()   # "PLA Bone White" at 3.1 mm -> two lines, split where the letters come out largest
        rest = max(([" ".join(w[:i]), " ".join(w[i:])] for i in range(1, len(w))), key=lower_size)
    if rest:
        s2 = lower_size(rest)
        hs = [text(s, s2, font)[2] for s in rest]
        y = (r2[2] + r2[3]) / 2 + (sum(hs) + GAP * (len(rest) - 1)) / 2
        for s, h in zip(rest, hs):
            parts.append(text(s, s2, font)[0].moved(Pos((r2[0] + r2[1]) / 2, y - h / 2, z0)))
            y -= h + GAP
        sizes.append(s2)
    export_stl(Compound(parts), out_stl + ".text.stl", tolerance=0.002, angular_tolerance=0.05)
    res = trimesh.boolean.difference([card, trimesh.load(out_stl + ".text.stl")], engine="manifold")
    os.remove(out_stl + ".text.stl")
    res.export(out_stl)
    print(f"{out_stl}: {' | '.join(lines[:1] + rest)}; font {' / '.join(f'{s:.1f}' for s in sizes)} mm, "
          f"text {card.volume - res.volume:.1f} mm3")
    if min(sizes) < MIN_FONT:
        print(f"  warning: letters below {MIN_FONT} mm print as mush on a 0.4 nozzle - shorten the longest line")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lines", nargs="*", help="1-3 lines: brand (beside the hole), then material / colour")
    ap.add_argument("--extract", metavar="3MF")
    ap.add_argument("--filament", help="Orca filament preset, e.g. 'SUNLU Matte @BBL A1M'")
    ap.add_argument("--process", default="0.20mm Standard @BBL A1M")
    ap.add_argument("--machine", default="Bambu Lab A1 mini 0.4 nozzle")
    ap.add_argument("--font", default=FONT)
    ap.add_argument("--send", action="store_true", help="upload to the printer and start (tools/bbl_printer.py)")
    a = ap.parse_args()
    if a.extract:
        return extract(a.extract)
    if not 1 <= len(a.lines) <= 3 or not a.filament:
        ap.error("1-3 text lines and --filament are required")
    if not os.path.exists(CARD):
        sys.exit(f"{CARD} missing: download the 3MF of {SOURCE}, then run swatch.py --extract <file.3mf>")
    name = "swatch-" + re.sub(r"[^a-z0-9]+", "-", " ".join(a.lines).lower()).strip("-")
    out = os.path.join(HERE, "out", name)
    os.makedirs(out, exist_ok=True)
    stl = os.path.join(out, name + ".stl")
    build(a.lines, a.font, stl)
    cmd = [sys.executable, os.path.join(SCRIPTS, "orca.py"), "slice", out, stl, "--machine", a.machine,
           "--process", a.process, "--filament", a.filament]
    for kv in QUALITY:
        cmd += ["--set", kv]
    sys.stdout.flush()
    subprocess.run(cmd, check=True)
    g3 = os.path.join(out, name + ".gcode.3mf")
    head = open(os.path.join(out, "plate_1.gcode"), errors="replace").read()
    t = re.search(r"total estimated time: ([^\n;]+)", head)
    g = re.search(r"filament used \[g\] = ([\d.]+)", head)
    print(f"{g3}\n  {t.group(1) if t else '?'}, {g.group(1) if g else '?'} g")
    if a.send:
        printer = os.path.join(REPO, "tools", "bbl_printer.py")
        subprocess.run([printer, "upload", g3, name + ".gcode.3mf"], check=True)
        subprocess.run([printer, "print", name + ".gcode.3mf", "--no-flowcal"], check=True)
        print("sent - confirm with tools/bbl_printer.py status (layer count 10)")


main()
