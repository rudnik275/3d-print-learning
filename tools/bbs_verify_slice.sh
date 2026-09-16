#!/bin/zsh
# Show the settings actually used by Studio's latest slice of a given window (by pid) — from its
setopt null_glob
# autosave G-code (hidden file Metadata/.<pid>.<n>.gcode). Usage: bbs_verify_slice.sh <pid> [key ...]
pid=$1; shift
d=$(ls -d ${TMPDIR:-$(getconf DARWIN_USER_TEMP_DIR)}bamboo_model/*/*#${pid}#*/ 2>/dev/null | tail -1)
g=$(ls -t "$d"/Metadata/.${pid}.*.gcode 2>/dev/null | head -1)
[[ -n "$g" ]] || { echo "no slice from pid $pid yet" >&2; exit 1; }
echo "gcode: $g ($(stat -f %Sm -t %H:%M "$g"))"
grep -E "^; model printing time|^; object max height|^; total layer" "$g"
keys=(${@:-seam_slope_type wall_loops precise_outer_wall print_settings_id filament_settings_id})
for k in $keys; do grep -m1 -E "^; $k = " "$g" || echo "; $k = <absent>"; done
