#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["build123d", "trimesh", "numpy"]
# ///
"""Four identical wall-test blocks 25 x 25 x 30, label debossed 0.8 mm into the top. One STL per label."""
import sys, os
from build123d import Box, Text, extrude, Align, Pos, export_stl
FONT = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
W, H, DEPTH = 25.0, 30.0, 0.8
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for label in sys.argv[2:]:
    body = Box(W, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    txt = extrude(Text(label, font_size=7.0, font_path=FONT, align=(Align.CENTER, Align.CENTER)), amount=DEPTH + 0.2)
    txt = txt.moved(Pos(0, 0, H - DEPTH))
    part = body - txt
    bb = part.bounding_box()
    export_stl(part, f"{out}/{label}.stl")
    print(label, round(bb.max.X - bb.min.X, 2), round(bb.max.Y - bb.min.Y, 2), round(bb.max.Z - bb.min.Z, 2))
