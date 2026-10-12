#!/bin/bash
# usage: mvs_build.sh <flow_ratio> <temp>  -> sunlu-pla-recal-mvs-5-26.gcode.3mf (ramp 5 -> 26 mm3/s nominal over z 0.4..60)
set -e
FLOW=$1; TEMP=$2; T=/Users/rudnikdmitriy/.claude/jobs/a138266c/tmp; S=~/dev/bambu-print-model/skills/print-model/scripts
cd $T
uv run --quiet --with numpy --with trimesh python3 - <<PY
import sys, os; sys.path.insert(0, os.path.expanduser("$S"))
import numpy as np, trimesh, bbs_calib
vs, ts = bbs_calib.cylinder_mesh(40.0, 60.0); trimesh.Trimesh(np.array(vs), np.array(ts)).export("mvs-cyl.stl")
PY
uv run --quiet --with numpy --with trimesh python3 make3mf.py mvs-5-26.3mf "mvs_5_26=mvs-cyl.stl@100,90:brim_type=outer_only" >/dev/null
rm -rf out-mvs
python3 slice_noarrange.py slice $T/out-mvs mvs-5-26.3mf --machine "Bambu Lab A1 mini 0.4 nozzle" --process "0.20mm Standard @BBL A1M" --filament "Generic PLA @BBL A1M" \
  --set filament_flow_ratio=$FLOW --set nozzle_temperature=$TEMP --set nozzle_temperature_initial_layer=$TEMP \
  --set spiral_mode=1 --set wall_loops=1 --set top_shell_layers=0 --set bottom_shell_layers=2 --set sparse_infill_density=0% \
  --set outer_wall_speed=310 --set slow_down_layer_time=0 --set slow_down_for_layer_cooling=0 --set enable_overhang_speed=0 \
  --set only_one_wall_top=0 --set resolution=0.05 --set filament_max_volumetric_speed=50 --set brim_type=outer_only --set brim_width=5 | tail -1
cp out-mvs/mvs-5-26.gcode.3mf sunlu-pla-recal-mvs-5-26.gcode.3mf
python3 - <<PY
import sys, os; sys.path.insert(0, os.path.expanduser("$S"))
import bbs_calib; bbs_calib.speed_ramp("$T/sunlu-pla-recal-mvs-5-26.gcode.3mf", 5, 26)
PY
unzip -p sunlu-pla-recal-mvs-5-26.gcode.3mf Metadata/plate_1.gcode > mvs-check.gcode
grep -E "^; (filament_flow_ratio|nozzle_temperature|spiral_mode|wall_loops|filament_max_volumetric_speed|slow_down_for_layer_cooling) =" mvs-check.gcode
echo "layers: $(grep -c '^; CHANGE_LAYER' mvs-check.gcode)  M1002: $(grep -c M1002 mvs-check.gcode)"
awk '/^; Z_HEIGHT:/{z=$3} /^G1 .*X.*E/{if (match($0,/F[0-9]+/)) {f=substr($0,RSTART+1,RLENGTH-1); if (z==10.2||z==20.2||z==30.2||z==40.2||z==50.2||z==60) {if (!(z in seen)) {seen[z]=1; printf "z=%s F=%s mm/min = %.0f mm/s\n", z, f, f/60}}}}' mvs-check.gcode
