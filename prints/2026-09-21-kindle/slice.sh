#!/bin/zsh
# CLI-slice Studio projects, 3 at a time: <name>.3mf -> <out dir>/<name>/{<name>.gcode.3mf, plate_1.gcode, result.json, cli.log}
# Usage: slice.sh <out dir> <project.3mf> [project.3mf ...]
O=$1; shift; mkdir -p "$O"
one() {
  f=$1; n=$(basename "$f" .3mf); d="$O/$n"; rm -rf "$d"; mkdir -p "$d"
  /Applications/BambuStudio.app/Contents/MacOS/BambuStudio --slice 0 --export-3mf "$n.gcode.3mf" --outputdir "$d" --debug 0 "$f" >"$d/cli.log" 2>&1
  if [ -f "$d/result.json" ]; then
    python3 - "$d/result.json" "$n" <<'EOF'
import json, sys
r = json.load(open(sys.argv[1])); p = r["sliced_plates"][0]
print(sys.argv[2] + ":", r["error_string"], "| warn:", repr(p["warning_message"]), "| main %d:%02d + prep %d:%02d" % (p["main_predication"] // 3600, p["main_predication"] % 3600 // 60, (p["total_predication"] - p["main_predication"]) // 3600, (p["total_predication"] - p["main_predication"]) % 3600 // 60), "| g:", round(p["filaments"][0]["total_used_g"], 1))
EOF
  else echo "$n: NO result.json"; tail -3 "$d/cli.log"; fi
}
i=0
for f in "$@"; do
  one "$f" &
  i=$((i + 1)); if [ $((i % 3)) -eq 0 ]; then wait; fi
done
wait
