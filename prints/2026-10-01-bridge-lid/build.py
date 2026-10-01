#!/usr/bin/env python3
"""Lid + high-flow bridge plate for SUNLU PLA on the A1 mini, all at the slow bridge speed (10 mm/s).

Follow-up to ../2026-10-01-bridge-slow, where 10/1.6 — the highest flow tried — came out the flattest deck.
Two questions on one plate, each with one variable:
  decks (bridge_row.scad, free edges, spans 15-45): 10/1.8, 10/2.0 — is there anything better above 1.6?
           The 10/1.6 deck from the previous plate is the control.
  lids (bridge_lid.scad, 40 x 40 roof anchored on all four sides, a closed pocket over the hot bed):
           10/1.4, 10/1.6, 10/1.8 — does the deck winner hold on a lid, or does a lid want another flow?
"Slow" is the MakerWorld 2050964 set: bridge_speed 10, overhang_2_4_speed 10, overhang_3_4_speed 10.
Everything else as before — 0.20mm Standard, calibrated SUNLU PLA, bridge fan 100 %, no supports.

verify() reads the first bridge layer (z 6.2) of the sliced G-code: bridge speed and E per mm of every object.

Usage: build.py [out dir]   (default: this folder)"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
from bbs_calib import build, stl_mesh
from bbs_project import _read_zip, _write_zip, gcode3mf

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else HERE
SCAD = "/Applications/OpenSCAD Dev.app/Contents/MacOS/OpenSCAD"   # Homebrew openscad gets killed (137) on this Mac
ROW_SCAD = os.path.join(REPO, "prints", "2026-10-01-bridge-flow", "bridge_row.scad")
LID_SCAD = os.path.join(HERE, "bridge_lid.scad")
SLICE = os.path.expanduser("~/dev/bambu-print-model/skills/print-model/scripts/slice.py")
BASE = os.path.join(REPO, "prints", "2026-09-17-snap-fit", "Snap-fit-test.3mf")   # A1 mini, 0.20 Standard, SUNLU PLA, textured PEI
NAME = "pla-bridge-lid"
SPEED, UNDER = 10, 6.0
REF_EMM = 0.0310          # bridge E per mm at bridge_flow 1.0, measured on the two previous plates
# (kind, flow, centre x, centre y, half size x, half size y) — decks 150 x 10 at the back, lids 48 x 48 in front (x 21..171)
OBJECTS = [("deck", 1.8, 97.0, 140.0, 75, 5), ("deck", 2.0, 97.0, 114.0, 75, 5),
           ("lid", 1.4, 45.0, 56.0, 24, 24), ("lid", 1.6, 96.0, 56.0, 24, 24), ("lid", 1.8, 147.0, 56.0, 24, 24)]

GLOBAL = {"enable_support": "0"}
FILAMENT = {"filament_max_volumetric_speed": "13"}   # SUNLU PLA recalibrated 27.09 (base project still has 12)
SLOW = {"bridge_speed": str(SPEED), "overhang_2_4_speed": str(SPEED), "overhang_3_4_speed": str(SPEED)}

def stl(kind, label, name):
    p = os.path.join(OUT, f"{name}.stl")
    args = ["-D", f'label="{label}"'] + (["-D", "tab=14", "-D", "label_size=3.2"] if kind == "deck" else [])
    subprocess.run([SCAD, "-o", p, *args, "--export-format", "binstl", ROW_SCAD if kind == "deck" else LID_SCAD],
                   check=True, capture_output=True)
    return stl_mesh(p)

def project():
    objs, per = [], {}
    for kind, flow, cx, cy, _, _ in OBJECTS:
        name = f"{kind}_{SPEED}mms_flow_{flow:.1f}"
        objs.append((name, *stl(kind, f"{SPEED}/{flow:.1f}", name), (cx, cy))); per[name] = dict(SLOW, bridge_flow=f"{flow:.1f}")
    out = os.path.join(OUT, f"{NAME}.3mf")
    build(BASE, out, objs, lambda name: per[name], GLOBAL, "PLA bridge lid + high flow")
    files = _read_zip(out); cfg = json.loads(files["Metadata/project_settings.config"])
    for k, v in FILAMENT.items():
        cfg[k] = [v]
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    keys = [k for k in diff[1].split(";") if k]
    diff[1] = ";".join(keys + [k for k in FILAMENT if k not in keys]); cfg["different_settings_to_system"] = diff
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode(); _write_zip(out, files)
    return out

def verify(sliced):
    """first bridge layer: bridge feedrate, E/mm and longest line per object"""
    g = _read_zip(sliced)["Metadata/plate_1.gcode"].decode("utf8", "ignore").splitlines()
    z = x = y = f = 0.0; feat = ""; layers = 0; acc = {}
    for l in g:
        if l.startswith("; Z_HEIGHT:"): z = float(l.split(":")[1]); layers += 1
        elif l.startswith("; FEATURE:"): feat = l.split(":", 1)[1].strip()
        if not re.match(r"G[0123] ", l): continue
        mf = re.search(r"F([\d.]+)", l); f = float(mf.group(1)) if mf else f
        mx, my = re.search(r"X([-\d.]+)", l), re.search(r"Y([-\d.]+)", l)
        nx = float(mx.group(1)) if mx else x; ny = float(my.group(1)) if my else y
        e = re.search(r" E([-\d.]+)", l)
        if e and float(e.group(1)) > 0 and (mx or my) and feat == "Bridge" and abs(z - (UNDER + 0.2)) < 1e-3:
            L = ((nx - x) ** 2 + (ny - y) ** 2) ** .5; px, py = (x + nx) / 2, (y + ny) / 2
            for i, (_, _, cx, cy, hx, hy) in enumerate(OBJECTS):
                if abs(px - cx) <= hx + 2 and abs(py - cy) <= hy + 2:
                    a = acc.setdefault(i, [0.0, 0.0, 0.0, 0.0]); a[0] += float(e.group(1)); a[1] += L
                    a[2] += L / (f / 60) if f else 0; a[3] = max(a[3], L)
        x, y = nx, ny
    print("layers:", layers, "| M1002:", "\n".join(g).count("M1002"))
    for i, (kind, flow, *_rest) in enumerate(OBJECTS):
        a = acc.get(i)
        if not a: print(f"  {kind} {flow:.1f}: no Bridge on z {UNDER + 0.2:.1f}"); continue
        print(f"  {kind:4s} {SPEED}/{flow:.1f}: bridge {a[1] / a[2]:.0f} mm/s, E/mm {a[0] / a[1]:.4f} ({a[0] / a[1] / REF_EMM:.2f} of 1.0), "
              f"longest line {a[3]:.1f} mm, {a[2] / 60:.1f} min")

if __name__ == "__main__":
    proj = project()
    sdir = os.path.join(OUT, "cli")
    subprocess.run([sys.executable, SLICE, sdir, proj], check=True)
    sliced = os.path.join(sdir, NAME, f"{NAME}.gcode.3mf")
    verify(sliced)
    final = os.path.join(OUT, f"{NAME}.gcode.3mf"); gcode3mf(sliced, final); print("hand over:", final)
