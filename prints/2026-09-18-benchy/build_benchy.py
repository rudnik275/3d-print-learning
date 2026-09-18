import sys, os
sys.path.insert(0, "/Users/rudnikdmitriy/dev/3d-print-learning/.claude/worktrees/skeleton-duck-retarget/tools")
from bbs_calib import build, stl_mesh
v, t = stl_mesh("/Applications/BambuStudio.app/Contents/Resources/model/3DBenchy.stl")
objects = [("3DBenchy", v, t, (100.0, 90.0))]
gs = {"wall_loops": "2", "enable_support": "0", "slice_closing_radius": "0.01"}
build(os.path.expanduser("~/Downloads/Box-skill-test-v3.3mf"), os.path.expanduser("~/Downloads/Benchy.3mf"),
      objects, lambda n: {}, gs, "Benchy")
