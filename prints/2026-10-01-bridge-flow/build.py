#!/usr/bin/env python3
"""Bridge plate for SUNLU PLA on the A1 mini: three rows with bridge_flow 0.8 / 0.9 / 1.0, spans 15-45 mm in each.

Each row is one object (bridge_row.scad): a 10-mm deck at z = 6 over spans 15 / 25 / 35 / 45 mm, set per object to
its bridge_flow. Everything else is our working package — 0.20mm Standard, calibrated SUNLU PLA, bridge speed 50,
bridge fan 100 %, no supports. Judge the underside of every span: strands taut and touching / sagging / gaps
between strands. Two answers from one print: the bridge_flow to keep, and the longest span that is still clean
(the forecast's check 3 calls 25 mm noticeable and 40 mm stop — this plate tests that).

verify() reads the first deck layer of the sliced G-code: bridge E per mm of every row (should scale 0.8 : 0.9 : 1)
and the bridge line length over every span.

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
NAME = "pla-bridge-flow"
FLOWS = [0.8, 0.9, 1.0]
CX, ROW_Y = 95.0, [120.0, 90.0, 60.0]          # rows 146 mm long: x 22..168, the left edge stays right of x = 20
SPANS, TAB, POST, LENGTH = [15, 25, 35, 45], 10, 4, 146
UNDER = 6.0

GLOBAL = {"enable_support": "0"}
FILAMENT = {"filament_max_volumetric_speed": "13"}   # SUNLU PLA recalibrated 27.09 (base project still has 12)

def span_x(i):
    """bed x range of span i (row centred at CX)"""
    a = TAB + POST * i + sum(SPANS[:i]); left = CX - LENGTH / 2
    return left + a, left + a + SPANS[i]

def stl(label):
    p = os.path.join(OUT, f"bridge-{label}.stl")
    subprocess.run([SCAD, "-o", p, "-D", f'label="{label}"', "--export-format", "binstl", os.path.join(HERE, "bridge_row.scad")],
                   check=True, capture_output=True)
    return stl_mesh(p)

def project():
    objs = [(f"bridge_flow_{f:.1f}", *stl(f"{f:.1f}"), (CX, y)) for f, y in zip(FLOWS, ROW_Y)]
    out = os.path.join(OUT, f"{NAME}.3mf")
    build(BASE, out, objs, lambda name: {"bridge_flow": name.rsplit("_", 1)[1]}, GLOBAL, "PLA bridge flow")
    files = _read_zip(out); cfg = json.loads(files["Metadata/project_settings.config"])
    for k, v in FILAMENT.items():
        cfg[k] = [v]
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    keys = [k for k in diff[1].split(";") if k]
    diff[1] = ";".join(keys + [k for k in FILAMENT if k not in keys]); cfg["different_settings_to_system"] = diff
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode(); _write_zip(out, files)
    return out

def verify(sliced):
    """first deck layer: Bridge E/mm per row and the longest bridge line over each span"""
    g = _read_zip(sliced)["Metadata/plate_1.gcode"].decode("utf8", "ignore").splitlines()
    z = x = y = 0.0; feat = ""; layers = 0; e_mm = {}; longest = {}; fans = set()
    for l in g:
        if l.startswith("; Z_HEIGHT:"): z = float(l.split(":")[1]); layers += 1
        elif l.startswith("; FEATURE:"): feat = l.split(":", 1)[1].strip()
        if abs(z - (UNDER + 0.2)) < 1e-3 and l.startswith("M106"): fans.add(l.split(";")[0].strip())
        if not re.match(r"G[0123] ", l): continue
        mx, my = re.search(r"X([-\d.]+)", l), re.search(r"Y([-\d.]+)", l)
        nx = float(mx.group(1)) if mx else x; ny = float(my.group(1)) if my else y
        e = re.search(r" E([-\d.]+)", l)
        if e and float(e.group(1)) > 0 and (mx or my) and feat == "Bridge" and abs(z - (UNDER + 0.2)) < 1e-3:
            L = ((nx - x) ** 2 + (ny - y) ** 2) ** .5; px, py = (x + nx) / 2, (y + ny) / 2
            for r, ry in enumerate(ROW_Y):
                if abs(py - ry) > 5.5: continue
                a = e_mm.setdefault(r, [0.0, 0.0]); a[0] += float(e.group(1)); a[1] += L
                for i in range(len(SPANS)):
                    x0, x1 = span_x(i)
                    if x0 - 3 < px < x1 + 3: longest[(r, i)] = max(longest.get((r, i), 0), L)
        x, y = nx, ny
    print("layers:", layers, "| M1002:", "\n".join(g).count("M1002"), "| fan on the first deck layer:", sorted(fans) or "unchanged")
    base = e_mm.get(len(FLOWS) - 1, [0, 1]); base = base[0] / base[1] if base[1] else 0
    for r, f in enumerate(FLOWS):
        if r not in e_mm: print(f"  bridge_flow {f:.1f}: no Bridge found on z {UNDER + 0.2:.1f}"); continue
        k = e_mm[r][0] / e_mm[r][1]
        spans = "  ".join(f"{s} mm: line {longest.get((r, i), 0):.1f}" for i, s in enumerate(SPANS))
        print(f"  bridge_flow {f:.1f}: E/mm {k:.4f} ({k / base:.2f} of 1.0) | {spans}")

if __name__ == "__main__":
    proj = project()
    sdir = os.path.join(OUT, "cli")
    subprocess.run([sys.executable, SLICE, sdir, proj], check=True)
    sliced = os.path.join(sdir, NAME, f"{NAME}.gcode.3mf")
    verify(sliced)
    final = os.path.join(OUT, f"{NAME}.gcode.3mf"); gcode3mf(sliced, final); print("hand over:", final)
