#!/bin/zsh
# Prototype pass (21.09, PETG, speed over finish): re-target the shipped projects to 0.20 Standard, two walls,
# 10 % infill; the supports/blocker/brim/seam decisions stay. box2 also as 0.24 Draft for the time comparison.
# Usage: fast.sh <proj dir with bezel/box2/cap-*.3mf> <proj dir with vent-blk.3mf> <out dir>
set -e
P=$1; V=$2; O=$3; T=$(cd "$(dirname "$0")/../.." && pwd)/tools; mkdir -p "$O"
M="Bambu Lab A1 mini 0.4 nozzle"; F="SUNLU PETG Olive Green @BBL A1M"; B="Textured PEI Plate"
fast() {  # <in.3mf> <out name> <process>
  python3 "$T/bbs_project.py" retarget "$1" "$O/$2-rt.3mf" --machine "$M" --process "$3" --filament "$F" --bed "$B" >/dev/null
  python3 "$T/bbs_project.py" variant "$O/$2-rt.3mf" "$O/$2.3mf" --set wall_loops=2 --set sparse_infill_density=10% >/dev/null
  rm -f "$O/$2-rt.3mf"; echo "built $O/$2.3mf ($3)"
}
fast "$P/bezel.3mf"     bezel-f   "0.20mm Standard @BBL A1M"
fast "$V/vent-blk.3mf"  vent-f    "0.20mm Standard @BBL A1M"
fast "$P/cap-right.3mf" cap-right-f "0.20mm Standard @BBL A1M"
fast "$P/cap-left.3mf"  cap-left-f  "0.20mm Standard @BBL A1M"
fast "$P/box2.3mf"      box2-f    "0.20mm Standard @BBL A1M"
fast "$P/box2.3mf"      box2-d    "0.24mm Draft @BBL A1M"
