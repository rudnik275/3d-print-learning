#!/usr/bin/env python3
"""Support gap plate for SUNLU PLA on the A1 mini: shelf specimens with different support_top_z_distance.

Each specimen is a post with an 18-mm shelf at z = 8; the support under the shelf is the only support on it.
The variable is the Z gap between the support interface and the shelf underside, set per object; everything else
is our working package — from the plate only, xy distance 0.8, default interface (2 layers, spacing 0.5),
0.20mm Standard, calibrated SUNLU PLA. Judge each shelf: does the support come off by hand in one piece, and how
does the underside look (smooth / lines drooping). The smallest gap that still comes off cleanly is the value.

Two rows, because the gap behaves differently by support type (measured on this plate, Studio 2.8):
  back row  — tree(auto) 0.2 / 0.4: trees put the gap on the layer grid, 0.1-0.3 all slice as 0.2 and 0.4-0.5
              as 0.4, so at 0.2 layers there are only these two values to choose from;
  front row — normal(auto) 0.10 ... 0.30: with independent_support_layer_height = 1 normal supports get the gap
              exactly as set.
verify() measures the real gap of every specimen in the sliced G-code.

Usage: build.py [out dir]   (default: this folder)"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
from bbs_calib import build, stl_mesh
from bbs_project import _read_zip, _write_zip, gcode3mf

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else HERE
SCAD = "/Applications/OpenSCAD Dev.app/Contents/MacOS/OpenSCAD"   # Homebrew openscad gets killed (137) on this Mac
SLICE = os.path.expanduser("~/dev/bambu-print-model/skills/print-model/scripts/slice.py")
BASE = os.path.join(REPO, "prints", "2026-09-17-snap-fit", "Snap-fit-test.3mf")   # A1 mini, 0.20 Standard, SUNLU PLA, textured PEI
NAME = "pla-support-gap"
PITCH = 28.0                     # specimens are 22 mm long in x, 6 mm apart; the left edge stays right of x = 20
SPECIMENS = [                    # (label on the shelf, support_type, gap, (centre x, centre y))
    ("T0.2", "tree(auto)", 0.2, (76.0, 112.0)), ("T0.4", "tree(auto)", 0.4, (104.0, 112.0)),
] + [(f"{g:.2f}", "normal(auto)", g, (90.0 + (i - 2) * PITCH, 72.0)) for i, g in enumerate([0.10, 0.15, 0.20, 0.25, 0.30])]

GLOBAL = {"support_type": "tree(auto)", "support_object_xy_distance": "0.8", "support_interface_spacing": "0.5"}
FILAMENT = {"filament_max_volumetric_speed": "13"}   # SUNLU PLA recalibrated 27.09 (base project still has 12)

def stl(label):
    p = os.path.join(OUT, f"gap-{label}.stl")
    subprocess.run([SCAD, "-o", p, "-D", f'label="{label}"', "--export-format", "binstl", os.path.join(HERE, "support_gap.scad")],
                   check=True, capture_output=True)
    return stl_mesh(p)

def project():
    objs = [(f"{t.split('(')[0]}_{g:.2f}", *stl(label), at) for label, t, g, at in SPECIMENS]
    per = {f"{t.split('(')[0]}_{g:.2f}": {"support_type": t, "support_top_z_distance": f"{g:.2f}"} for _, t, g, _ in SPECIMENS}
    out = os.path.join(OUT, f"{NAME}.3mf")
    build(BASE, out, objs, lambda name: per[name], GLOBAL, "PLA support gap")
    files = _read_zip(out); cfg = json.loads(files["Metadata/project_settings.config"])
    for k, v in FILAMENT.items():
        cfg[k] = [v]
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    keys = [k for k in diff[1].split(";") if k]
    diff[1] = ";".join(keys + [k for k in FILAMENT if k not in keys]); cfg["different_settings_to_system"] = diff
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode(); _write_zip(out, files)
    return out

def verify(sliced):
    """per specimen: top of the support interface under the shelf vs the bottom of the shelf's first layer"""
    g = _read_zip(sliced)["Metadata/plate_1.gcode"].decode("utf8", "ignore").splitlines()
    z = h = x = y = 0.0; feat = ""; sup_top = {}; shelf = {}; layers = 0
    for l in g:
        if l.startswith("; Z_HEIGHT:"): z = float(l.split(":")[1]); layers += 1
        elif l.startswith("; LAYER_HEIGHT:"): h = float(l.split(":")[1])
        elif l.startswith("; FEATURE:"): feat = l.split(":", 1)[1].strip()
        if not re.match(r"G[0123] ", l): continue
        mx, my = re.search(r"X([-\d.]+)", l), re.search(r"Y([-\d.]+)", l)
        nx = float(mx.group(1)) if mx else x; ny = float(my.group(1)) if my else y
        e = re.search(r" E([-\d.]+)", l)
        if e and float(e.group(1)) > 0 and (mx or my):
            px, py = (x + nx) / 2, (y + ny) / 2                     # segment midpoint: support lines end past the shelf edge
            for i, (_, _, _, (cx, cy)) in enumerate(SPECIMENS):
                if not (cx - 6 < px < cx + 12 and abs(py - cy) < 9): continue   # under / on the shelf, clear of the post
                if feat.startswith("Support interface") and z < 9: sup_top[i] = max(sup_top.get(i, 0), z)
                if not feat.startswith("Support") and 7.5 < z < 9.5 and i not in shelf: shelf[i] = (z, h)
        x, y = nx, ny
    print("layers:", layers, "| M1002:", "\n".join(g).count("M1002"))
    for i, (label, t, gap, _) in enumerate(SPECIMENS):
        if i in sup_top and i in shelf:
            zs, hs = shelf[i]
            print(f"  {label:5s} {t:12s} set {gap:.2f}: interface top z {sup_top[i]:.3f}, shelf from z {zs - hs:.3f} -> real gap {zs - hs - sup_top[i]:.3f} mm")
        else:
            print(f"  {label:5s} {t:12s} set {gap:.2f}: interface {sup_top.get(i)} shelf {shelf.get(i)} — not found")

if __name__ == "__main__":
    proj = project()
    sdir = os.path.join(OUT, "cli")
    subprocess.run([sys.executable, SLICE, sdir, proj], check=True)
    sliced = os.path.join(sdir, NAME, f"{NAME}.gcode.3mf")
    verify(sliced)
    final = os.path.join(OUT, f"{NAME}.gcode.3mf"); gcode3mf(sliced, final); print("hand over:", final)
