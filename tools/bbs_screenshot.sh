#!/bin/zsh
# Screenshot for "seeing" Bambu Studio. Usage: bbs_screenshot.sh [out.png]
# Needs macOS permission: System Settings → Privacy & Security → Screen Recording → the process
# that runs this session ("claude", or the terminal app). Falls back to full-screen capture.
out=${1:-${CLAUDE_JOB_DIR:-/tmp}/tmp/bbs-$(date +%H%M%S).png}
mkdir -p "$(dirname "$out")"
osascript -e 'tell application "BambuStudio" to activate' 2>/dev/null; sleep 0.5
screencapture -x "$out" && echo "$out" || { echo "screencapture failed — grant Screen Recording permission" >&2; exit 1; }
