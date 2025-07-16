#!/usr/bin/env bash
set -euo pipefail

# CONFIG
SVG_DIR="AOAnimation"      # where your frame_00000.svg … frame_00311.svg live
PNG_DIR="png_frames"       # temp folder for PNGs
OUT_VIDEO="animation.mp4"  # final output
FPS=30                     # desired frame rate

# 1) Clean & prep
rm -rf "$PNG_DIR"
mkdir -p "$PNG_DIR"

# 2) Export each SVG → PNG at exact pixel size
echo "Converting SVGs to PNGs…"
for svg in "$SVG_DIR"/frame_*.svg; do
  base=$(basename "${svg%.svg}")
  inkscape "$svg" \
    --export-type=png \
    --export-filename="$PNG_DIR/$base.png" \
    >/dev/null
done

# 3) Build MP4 with H.264, yuv420p for broad compatibility
echo "Building MP4 at ${FPS} fps…"
ffmpeg -y -framerate "$FPS" -i "$PNG_DIR/frame_%05d.png" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart \
  "$OUT_VIDEO"

echo "Done! → $OUT_VIDEO"