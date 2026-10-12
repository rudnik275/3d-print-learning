import sys, os, subprocess
sys.path.insert(0, os.path.expanduser("~/dev/bambu-print-model/skills/print-model/scripts"))
import numpy as np, trimesh, bbs_calib
objs = bbs_calib.generic_objects(os.path.join(bbs_calib.calib_dir(), "flowrate-test-pass1.3mf"))
def mod(name):
    s = name[9:]; return -float(s[1:]) if s.startswith("m") else float(s)
objs.sort(key=lambda o: mod(o[0])); os.makedirs("flow1", exist_ok=True)
w = max(max(v[0] for v in o[1]) - min(v[0] for v in o[1]) for o in objs); d = max(max(v[1] for v in o[1]) - min(v[1] for v in o[1]) for o in objs)
px, py = w + 5, d + 5; cols = max(1, min(4, int(160 // px))); rows = -(-len(objs) // cols)
args = []
for i, (name, vs, ts) in enumerate(objs):
    m = trimesh.Trimesh(np.array(vs), np.array(ts)); p = f"flow1/{name}.stl"; m.export(p)
    r, c = divmod(i, cols); cx = 90 + (c - (cols - 1) / 2) * px; cy = 90 + ((rows - 1) / 2 - r) * py
    keys = f"print_flow_ratio={1 + mod(name) / 100:.4f},wall_loops=3,top_shell_layers=5,bottom_shell_layers=1,sparse_infill_density=35%,ironing_type=no ironing,top_surface_pattern=monotonic,detect_thin_wall=1"
    args.append(f"{name}={p}@{cx:.1f},{cy:.1f}:{keys}")
print(f"block {w:.0f}x{d:.0f} mm, {cols} per row, order back(+Y)->front, left->right:", " | ".join(f"{mod(o[0]):+.0f}%" for o in objs))
subprocess.run([sys.executable, "make3mf.py", "flow1-generic.3mf"] + args, check=True)
