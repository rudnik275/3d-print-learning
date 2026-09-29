#!/usr/bin/env python3
"""Fan calibration plate for SUNLU PETG on the A1 mini: fan steps 0-20-40-60-80-100 % in 10-mm bands.

Two objects (fan_test.scad): a tower with a 20-mm bridge and 45°/60° ledges in every band — the lowest band
where they are clean is the lower bound of the fan window; a flat two-wall tube snapped by hand band by band —
the highest band that still holds is the upper bound. The part fan is one per layer, so one print covers both.

Fan is written into the sliced G-code (every part-fan M106 between the start and end blocks, plus one at every
layer change); Studio's own fan logic is neutralised first (fan 0-0, overhang fan off) so nothing interleaves.
Print the produced .gcode.3mf as is — re-slicing in Studio drops the bands.

Usage: build.py [out dir]   (default: this folder)"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
from bbs_calib import build, stl_mesh
from bbs_project import _read_zip, _write_zip, gcode3mf

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else HERE
SCAD = "/Applications/OpenSCAD Dev.app/Contents/MacOS/OpenSCAD"   # Homebrew openscad gets killed (137) on this Mac
SLICE = os.path.expanduser("~/dev/bambu-print-model/skills/print-model/scripts/slice.py")
BASE = os.path.join(REPO, "prints", "2026-09-22-petg-calib", "petg-flow-fine-099.3mf")   # A1 mini, 0.20 Standard, PETG, textured PEI
NAME = "petg-fan-0-100"
PLINTH, BAND, FANS = 2.0, 10.0, [0, 20, 40, 60, 80, 100]

FILAMENT = {   # calibrated SUNLU PETG (22.09) + neutral fan so only the bands decide
    "filament_settings_id": "SUNLU PETG @BBL A1M", "nozzle_temperature": "245", "nozzle_temperature_initial_layer": "245",
    "filament_flow_ratio": "0.95", "filament_max_volumetric_speed": "16",
    "fan_min_speed": "0", "fan_max_speed": "0", "enable_overhang_bridge_fan": "0", "overhang_fan_speed": "0",
}

def fan_at(z):
    k = int((z - PLINTH - 1e-6) // BAND) if z > PLINTH else 0
    return FANS[max(0, min(k, len(FANS) - 1))]

def stl(part):
    p = os.path.join(OUT, f"{part}.stl")
    subprocess.run([SCAD, "-o", p, "-D", f'part="{part}"', "--export-format", "binstl", os.path.join(HERE, "fan_test.scad")],
                   check=True, capture_output=True)
    return stl_mesh(p)

def project():
    tower, tube = stl("tower"), stl("tube")
    out = os.path.join(OUT, f"{NAME}.3mf")
    brim = lambda name: {"brim_type": "outer_only"}
    build(BASE, out, [("fan_tower", *tower, (78.0, 90.0)), ("snap_tube", *tube, (112.0, 90.0))], brim, {}, "PETG fan 0-100")
    files = _read_zip(out); cfg = json.loads(files["Metadata/project_settings.config"])
    for k, v in FILAMENT.items():
        cfg[k] = [v]
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    keys = [k for k in diff[1].split(";") if k]
    keys += [k for k in FILAMENT if k != "filament_settings_id" and k not in keys]
    diff[1] = ";".join(keys); cfg["different_settings_to_system"] = diff
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, ensure_ascii=False).encode(); _write_zip(out, files)
    return out

def fan_bands(sliced):
    files = _read_zip(sliced); g = files["Metadata/plate_1.gcode"].decode("utf8", "ignore").splitlines()
    out, inside, z, n_set, n_rep = [], False, 0.0, 0, 0
    for line in g:
        if line.startswith("; MACHINE_START_GCODE_END"): inside = True
        if line.startswith("; MACHINE_END_GCODE_START"): inside = False
        if inside and line.startswith("; Z_HEIGHT:"):
            z = float(line.split(":")[1]); out.append(line)
            out.append(f"M106 S{round(255 * fan_at(z) / 100)} ; fan band {fan_at(z)} %"); n_set += 1; continue
        if inside and re.match(r"M106 (P1 )?S[\d.]+", line):
            line = f"M106 S{round(255 * fan_at(z) / 100)} ; fan band {fan_at(z)} % (was: {line.split(';')[0].strip()})"; n_rep += 1
        out.append(line)
    data = ("\n".join(out) + "\n").encode()
    files["Metadata/plate_1.gcode"] = data; files["Metadata/plate_1.gcode.md5"] = hashlib.md5(data).hexdigest().upper().encode()
    _write_zip(sliced, files); print(f"fan bands: {n_set} layer commands, {n_rep} slicer M106 rewritten")
    return data.decode()

def verify(gcode):
    lines = gcode.splitlines(); z = 0.0; fan = {}; temps = set(); layers = 0; inside = False
    for l in lines:
        if l.startswith("; MACHINE_START_GCODE_END"): inside = True
        if l.startswith("; MACHINE_END_GCODE_START"): inside = False
        if l.startswith("; Z_HEIGHT:"): z = float(l.split(":")[1]); layers += 1
        m = re.match(r"M106 (?:P1 )?S([\d.]+)", l)
        if inside and m: fan.setdefault(round(float(m.group(1)) / 2.55), [z, z])[1] = z
        t = re.match(r"M10[49] S(\d+)", l)
        if t: temps.add(int(t.group(1)))
    print("layers:", layers, "| M1002:", gcode.count("M1002"), "| nozzle temps set:", sorted(temps))
    for p, (a, b) in sorted(fan.items()): print(f"  fan {p:3d} %  z {a:5.2f} .. {b:5.2f}")

if __name__ == "__main__":
    proj = project()
    sdir = os.path.join(OUT, "cli")
    subprocess.run([sys.executable, SLICE, sdir, proj], check=True)
    sliced = os.path.join(sdir, NAME, f"{NAME}.gcode.3mf")
    verify(fan_bands(sliced))
    final = os.path.join(OUT, f"{NAME}.gcode.3mf"); gcode3mf(sliced, final); print("hand over:", final)
