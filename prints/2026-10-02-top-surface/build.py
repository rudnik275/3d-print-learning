#!/usr/bin/env python3
"""Top surface plate for SUNLU PLA on the A1 mini: flow x top speed, plus the same flows ironed.

Why: the bridge lids showed grooves between top lines. The G-code says the geometry is right (lines 0.377 mm apart,
E/mm exactly the calibrated flow 0.98), but the top went at the volumetric cap: 200 mm/s set, 172 mm/s actual,
12.7 of 13 mm3/s. Two suspects — top speed and a flow that is a little lean — and one way around both, ironing.

20 squares 24 x 24 x 3 (top_square.scad), label engraved mirrored on the bottom ("speed" over "flow"), one variable
between neighbours:
  columns — print_flow_ratio 0.97 / 1.00 / 1.03 / 1.06 / 1.09 on top of the preset's 0.98: the whole object, the way
            Studio's flow wizard does it, so the plate re-checks the old flow calibration too;
  rows    — top_surface_speed 200 (preset) / 120 / 60, and a fourth row "IR": the preset's speed with Bambu's
            default ironing (10 %, 30 mm/s, spacing 0.15).
Everything else as in our prints — 0.20mm Standard, 5 top layers, monotonic line top, calibrated SUNLU PLA.

verify() reads every square's last top layer: speed, E per mm against the 1.00 column, ironing present or not.

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
NAME = "pla-top-surface"
FLOWS = [0.97, 1.00, 1.03, 1.06, 1.09]
ROWS = ["200", "120", "60", "IR"]               # back to front
PITCH, SIZE, TOP_Z = 27.0, 24.0, 3.0           # 5 columns: x 24..156, 4 rows: y 42..147
COL_X = [90.0 + (j - 2) * PITCH for j in range(len(FLOWS))]
ROW_Y = [135.0 - i * PITCH for i in range(len(ROWS))]

GLOBAL = {"enable_support": "0"}
FILAMENT = {"filament_max_volumetric_speed": "13"}   # SUNLU PLA recalibrated 27.09 (base project still has 12)

def per_object(row, flow):
    s = {"print_flow_ratio": f"{flow:.2f}"}
    if row == "IR":
        s["ironing_type"] = "top"
    else:
        s["top_surface_speed"] = row
    return s

def stl(row, flow, name):
    p = os.path.join(OUT, f"{name}.stl")
    subprocess.run([SCAD, "-o", p, "-D", f'line1="{row}"', "-D", f'line2="{flow:.2f}"', "--export-format", "binstl",
                    os.path.join(HERE, "top_square.scad")], check=True, capture_output=True)
    return stl_mesh(p)

def project():
    objs, per = [], {}
    for row, y in zip(ROWS, ROW_Y):
        for flow, x in zip(FLOWS, COL_X):
            name = f"top_{row}_flow_{flow:.2f}"
            objs.append((name, *stl(row, flow, name), (x, y))); per[name] = per_object(row, flow)
    out = os.path.join(OUT, f"{NAME}.3mf")
    build(BASE, out, objs, lambda name: per[name], GLOBAL, "PLA top surface")
    files = _read_zip(out); cfg = json.loads(files["Metadata/project_settings.config"])
    for k, v in FILAMENT.items():
        cfg[k] = [v]
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    keys = [k for k in diff[1].split(";") if k]
    diff[1] = ";".join(keys + [k for k in FILAMENT if k not in keys]); cfg["different_settings_to_system"] = diff
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode(); _write_zip(out, files)
    return out

def verify(sliced):
    """last top layer of every square: Top surface speed and E/mm, Ironing length"""
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
        if e and float(e.group(1)) > 0 and (mx or my) and feat in ("Top surface", "Ironing") and abs(z - TOP_Z) < 1e-3:
            L = ((nx - x) ** 2 + (ny - y) ** 2) ** .5; px, py = (x + nx) / 2, (y + ny) / 2
            for i, ry in enumerate(ROW_Y):
                for j, cx in enumerate(COL_X):
                    if abs(px - cx) < SIZE / 2 + 1 and abs(py - ry) < SIZE / 2 + 1:
                        a = acc.setdefault((i, j, feat), [0.0, 0.0, 0.0]); a[0] += float(e.group(1)); a[1] += L
                        a[2] += L / (f / 60) if L > 3 else 0
        x, y = nx, ny
    print("layers:", layers, "| M1002:", "\n".join(g).count("M1002"))
    for i, row in enumerate(ROWS):
        ref = acc.get((i, FLOWS.index(1.00), "Top surface"))
        cells = []
        for j, flow in enumerate(FLOWS):
            t, ir = acc.get((i, j, "Top surface")), acc.get((i, j, "Ironing"))
            if not t: cells.append(f"{flow:.2f}: no top"); continue
            cells.append(f"{flow:.2f}: x{t[0] / t[1] / (ref[0] / ref[1]):.3f}" + (f" ir {ir[1]:.0f}mm" if ir else ""))
        speeds = [acc[(i, j, "Top surface")] for j in range(len(FLOWS)) if (i, j, "Top surface") in acc]
        lens = sum(a[1] for a in speeds); tm = sum(a[2] for a in speeds)
        print(f"  row {row:>3}: top speed ~{lens / tm if tm else 0:.0f} mm/s | " + " | ".join(cells))

if __name__ == "__main__":
    proj = project()
    sdir = os.path.join(OUT, "cli")
    subprocess.run([sys.executable, SLICE, sdir, proj], check=True)
    sliced = os.path.join(sdir, NAME, f"{NAME}.gcode.3mf")
    verify(sliced)
    final = os.path.join(OUT, f"{NAME}.gcode.3mf"); gcode3mf(sliced, final); print("hand over:", final)
