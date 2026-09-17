import sys, os
sys.path.insert(0, "/Users/rudnikdmitriy/dev/3d-print-learning/.claude/worktrees/skeleton-duck-retarget/tools")
from bbs_calib import build, stl_mesh
E = os.path.expanduser("~/Desktop/exports/")
v1, t1 = stl_mesh(E + "fit snap_fit snap_Body1.stl")
v2, t2 = stl_mesh(E + "fit snap_fit snap_Body2.stl")
# Body1: rotate 180 deg about X -> solid 20x13 face becomes the base, end-slot opens at the top
v1 = [(x, -y, -z) for x, y, z in v1]; t1 = [(a, c, b) for a, b, c in t1]  # keep outward normals
objects = [("slot-block", v1, t1, (100.0, 90.0)), ("snap-clip", v2, t2, (124.0, 90.0))]
gs = {"slice_closing_radius": "0.01",
      "enable_support": "1", "support_type": "normal(auto)", "support_on_build_plate_only": "1",
      "support_interface_spacing": "0.2"}
build(os.path.expanduser("~/Downloads/Box-skill-test-v3.3mf"), os.path.expanduser("~/Downloads/Snap-fit-test.3mf"),
      objects, lambda n: {}, gs, "Snap-fit test")
