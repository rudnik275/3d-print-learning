#!/bin/zsh
set -e
W=/Users/rudnikdmitriy/dev/3d-print-learning/.claude/worktrees/skeleton-duck-retarget
D=/Users/rudnikdmitriy/Downloads
cd "$W"
./tools/bbs_project.py move "$D/Branch-stand-rt.3mf" "$D/Branch-stand-mv.3mf" --at 100,90
./tools/bbs_project.py variant "$D/Branch-stand-mv.3mf" "$D/Branch-stand.3mf" --title "Branch stand" \
  --set resolution=0.004 --set slice_closing_radius=0.01 --set reduce_crossing_wall=1 --set max_travel_detour_distance=300 \
  --set support_top_z_distance=0.2 --set support_object_xy_distance=0.8 --set enable_prime_tower=0
./tools/bbs_current.py "$D/Branch-stand.3mf" 2>&1 | sed -n '/^machine/,/^objects/p;/differs/,/project-only/p' | grep -v -E 'project-only|^  filament_|^  [a-z_]+: .* -> \[' | head -30
rm -rf "$D/stand-cli"; mkdir -p "$D/stand-cli"
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --slice 0 --export-3mf Branch-stand-cli.gcode.3mf --outputdir "$D/stand-cli" --debug 0 "$D/Branch-stand.3mf" >/dev/null 2>&1 || true
ls "$D/stand-cli"
python3 -c "import json; r=json.load(open('$D/stand-cli/result.json')); p=r['sliced_plates'][0]; print('result:', r['error_string'], 'warn:', repr(p['warning_message']), 'main s:', round(p['main_predication']), 'total s:', round(p['total_predication']), 'g:', round(p['filaments'][0]['total_used_g'],2)); print('objects:', [(o['name'], o['bbox']) for o in p['objects']]); print({k: round(v) for k, v in p['feature_type_times'].items()})"
grep -E '^; (total layer number|filament used \[g\]|support_top_z_distance|support_object_xy_distance|enable_prime_tower|wall_loops|brim_type|layer_height|outer_wall_speed) ' "$D/stand-cli/plate_1.gcode"
echo S205=$(grep -c S205 "$D/stand-cli/plate_1.gcode") M1002=$(grep -c M1002 "$D/stand-cli/plate_1.gcode") brim=$(grep -c 'FEATURE: Brim' "$D/stand-cli/plate_1.gcode") tower=$(grep -c 'FEATURE: Prime tower' "$D/stand-cli/plate_1.gcode")
unzip -p "$D/stand-cli/Branch-stand-cli.gcode.3mf" Metadata/slice_info.config | grep -E 'warning|outside|support_used'
