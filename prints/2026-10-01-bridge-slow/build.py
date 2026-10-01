#!/usr/bin/env python3
"""Slow bridge plate for SUNLU PLA on the A1 mini: does a slow, over-flowed bridge beat our best fast one?

Follow-up to ../2026-10-01-bridge-flow (50 mm/s: flow 0.8 looked best of 0.8 / 0.9 / 1.0, still not perfect).
The idea under test comes from MakerWorld 2050964 (bridge 10 mm/s, bridge_flow 1.1-1.9). Same rows as the first
plate (bridge_row.scad: 10-mm deck at z = 6 over spans 15 / 25 / 35 / 45 mm, free edges), five of them, one
variable between neighbours:
  10/0.8 — speed alone changed against the first plate's 0.8 row (that part is the control: same day, spool
           and bridge settings, so it is not reprinted);
  10/1.0, 10/1.2, 10/1.4, 10/1.6 — flow at the slow speed.
"Slow" is the author's set: bridge_speed 10, overhang_2_4_speed 10, overhang_3_4_speed 10 (the deck edges are
overhang walls). Everything else as before — 0.20mm Standard, calibrated SUNLU PLA, bridge fan 100 %, no supports.
Labels on the row tabs read speed/flow.

verify() reads the first deck layer of the sliced G-code: bridge speed and E per mm of every row.

Usage: build.py [out dir]   (default: this folder)"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
from bbs_calib import build, stl_mesh
from bbs_project import _read_zip, _write_zip, gcode3mf

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else HERE
SCAD = "/Applications/OpenSCAD Dev.app/Contents/MacOS/OpenSCAD"   # Homebrew openscad gets killed (137) on this Mac
ROW_SCAD = os.path.join(REPO, "prints", "2026-10-01-bridge-flow", "bridge_row.scad")
SLICE = os.path.expanduser("~/dev/bambu-print-model/skills/print-model/scripts/slice.py")
BASE = os.path.join(REPO, "prints", "2026-09-17-snap-fit", "Snap-fit-test.3mf")   # A1 mini, 0.20 Standard, SUNLU PLA, textured PEI
NAME = "pla-bridge-slow"
ROWS = [(10, 0.8), (10, 1.0), (10, 1.2), (10, 1.4), (10, 1.6)]   # (bridge speed mm/s, bridge_flow), back to front
TAB, LENGTH, UNDER = 14, 150, 6.0                     # rows 150 mm long: x 22..172, the left edge stays right of x = 20
CX, ROW_Y = 97.0, [142.0 - 26.0 * i for i in range(len(ROWS))]

GLOBAL = {"enable_support": "0"}
FILAMENT = {"filament_max_volumetric_speed": "13"}   # SUNLU PLA recalibrated 27.09 (base project still has 12)

def per_object(speed, flow):
    s = {"bridge_flow": f"{flow:.1f}"}
    if speed != 50:
        s.update({"bridge_speed": str(speed), "overhang_2_4_speed": str(speed), "overhang_3_4_speed": str(speed)})
    return s

def stl(label, name):
    p = os.path.join(OUT, f"{name}.stl")
    subprocess.run([SCAD, "-o", p, "-D", f'label="{label}"', "-D", f"tab={TAB}", "-D", "label_size=3.2",
                    "--export-format", "binstl", ROW_SCAD], check=True, capture_output=True)
    return stl_mesh(p)

def project():
    objs, per = [], {}
    for (speed, flow), y in zip(ROWS, ROW_Y):
        name = f"bridge_{speed}mms_flow_{flow:.1f}"
        objs.append((name, *stl(f"{speed}/{flow:.1f}", name), (CX, y))); per[name] = per_object(speed, flow)
    out = os.path.join(OUT, f"{NAME}.3mf")
    build(BASE, out, objs, lambda name: per[name], GLOBAL, "PLA slow bridge")
    files = _read_zip(out); cfg = json.loads(files["Metadata/project_settings.config"])
    for k, v in FILAMENT.items():
        cfg[k] = [v]
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    keys = [k for k in diff[1].split(";") if k]
    diff[1] = ";".join(keys + [k for k in FILAMENT if k not in keys]); cfg["different_settings_to_system"] = diff
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode(); _write_zip(out, files)
    return out

def verify(sliced):
    """first deck layer: bridge feedrate and E/mm per row, overhang-wall feedrate per row"""
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
        if e and float(e.group(1)) > 0 and (mx or my) and feat in ("Bridge", "Overhang wall") and abs(z - (UNDER + 0.2)) < 1e-3:
            L = ((nx - x) ** 2 + (ny - y) ** 2) ** .5; py = (y + ny) / 2
            for r, ry in enumerate(ROW_Y):
                if abs(py - ry) > 6: continue
                a = acc.setdefault((r, feat), [0.0, 0.0, 0.0]); a[0] += float(e.group(1)); a[1] += L; a[2] += L / (f / 60) if f else 0
        x, y = nx, ny
    print("layers:", layers, "| M1002:", "\n".join(g).count("M1002"))
    ref = acc.get((ROWS.index((10, 1.0)), "Bridge"))  # row 10/1.0 is the flow reference
    for r, (speed, flow) in enumerate(ROWS):
        b, o = acc.get((r, "Bridge")), acc.get((r, "Overhang wall"))
        if not b: print(f"  {speed}/{flow:.1f}: no Bridge on z {UNDER + 0.2:.1f}"); continue
        line = f"  {speed:2d} mm/s / flow {flow:.1f}: bridge {b[1] / b[2]:.0f} mm/s, E/mm {b[0] / b[1]:.4f} ({b[0] / b[1] / (ref[0] / ref[1]):.2f} of 1.0), {b[2] / 60:.1f} min"
        if o: line += f" | edge walls {o[1] / o[2]:.0f} mm/s"
        print(line)

if __name__ == "__main__":
    proj = project()
    sdir = os.path.join(OUT, "cli")
    subprocess.run([sys.executable, SLICE, sdir, proj], check=True)
    sliced = os.path.join(sdir, NAME, f"{NAME}.gcode.3mf")
    verify(sliced)
    final = os.path.join(OUT, f"{NAME}.gcode.3mf"); gcode3mf(sliced, final); print("hand over:", final)
