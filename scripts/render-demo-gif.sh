#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRAMES_DIR="${ROOT}/docs/assets/.tool-tax-demo-frames"
HTML="file://${ROOT}/docs/assets/tool-tax-demo.html"
OUT="${ROOT}/docs/assets/tool-tax-demo.gif"
PALETTE="${FRAMES_DIR}/palette.png"

rm -rf "${FRAMES_DIR}"
mkdir -p "${FRAMES_DIR}"

for frame in $(seq 0 47); do
  npx -y playwright@1.60.0 screenshot \
    --viewport-size=1200,675 \
    --wait-for-timeout=80 \
    "${HTML}?frame=${frame}" \
    "${FRAMES_DIR}/frame-$(printf "%03d" "${frame}").png" >/dev/null
done

ffmpeg -y \
  -framerate 8 \
  -i "${FRAMES_DIR}/frame-%03d.png" \
  -vf "fps=8,scale=960:-1:flags=lanczos,palettegen=stats_mode=diff" \
  "${PALETTE}" >/dev/null 2>&1

ffmpeg -y \
  -framerate 8 \
  -i "${FRAMES_DIR}/frame-%03d.png" \
  -i "${PALETTE}" \
  -lavfi "fps=8,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3" \
  -loop 0 \
  "${OUT}" >/dev/null 2>&1

rm -rf "${FRAMES_DIR}"
echo "wrote ${OUT}"
