#!/bin/zsh
# Screenshot for "seeing" Bambu Studio (or anything on screen). Usage: bbs_screenshot.sh [out.png]
# Captures through tools/ScreenGrab.app — an app-bundle wrapper around screencapture, because macOS
# grants Screen Recording only to .app bundles. One-time: System Settings → Privacy & Security →
# Screen & System Audio Recording → enable "ScreenGrab".
out=${1:-${CLAUDE_JOB_DIR:-/tmp}/tmp/screen-$(date +%H%M%S).png}
mkdir -p "$(dirname "$out")"; rm -f "$out"
app="$(cd "$(dirname "$0")" && pwd)/ScreenGrab.app"
open -W -a "$app" --args -x "$out"
[[ -s "$out" ]] && echo "$out" || { echo "no image — enable ScreenGrab in Screen Recording settings" >&2; exit 1; }
