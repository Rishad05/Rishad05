#!/usr/bin/env python3
"""
make_ascii_svg.py
-----------------
Renders `source-prepped.png` into a cinematic ASCII-art terminal card
(`hxni-ascii.svg`):

  * Gold monospace typography (#D4AF37 family ramp) on a #0d0d0d card.
  * macOS-style traffic-light dots + terminal title in the top bar.
  * Animated line-by-line reveal via CSS `@keyframes fin` AND a SMIL
    <clipPath> wipe so it animates in as many renderers as possible.

Usage:
    python scripts/make_ascii_svg.py [--columns 56] [--font-size 8.5]
                                     [--output hxni-ascii.svg]
Dependencies: pillow, numpy (see scripts/requirements.txt).
"""

from __future__ import annotations

import argparse
import math
import os
import sys

# Brightness -> character density ramp (sparse ' ' -> dense '@').
RAMP = " .`:-=+*cs#%@"

# Gold shading ramp (bright -> deep).
GOLD_RAMP = [
    ("#fbeeb6", "#fff6d8"),  # bright highlight
    ("#f0d980", "#fff2c2"),
    ("#e6c24f", "#ffecb0"),
    ("#d4af37", "#ffd97a"),  # signature gold
    ("#b68f2b", "#e9c256"),
    ("#8f6f22", "#c09a38"),
    ("#6f5620", "#8f6f27"),
]

FONT_STACK = "JetBrains Mono, ui-monospace, Cascadia Code, Consolas, 'Courier New', monospace"


def clamp(v: float, lo: float = 0.0, hi: float = 255.0) -> float:
    return max(lo, min(hi, v))


def hex_round(x: float) -> str:
    return f"{round(x):d}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build hxni-ascii.svg from source-prepped.png")
    ap.add_argument("--input", default="source-prepped.png")
    ap.add_argument("--output", default="hxni-ascii.svg")
    ap.add_argument("--columns", type=int, default=56, help="ASCII columns (default: 56)")
    ap.add_argument("--font-size", type=float, default=8.6, help="Glyph font size (default: 8.6)")
    ap.add_argument("--card-width", type=int, default=370, help="Target card width (default: 370)")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"[ascii] ERROR: {args.input} not found. Run prep_photo.py first.", file=sys.stderr)
        return 1

    from PIL import Image, ImageOps
    from numpy import asarray, clip

    print(f"[ascii] reading {args.input} ...")
    img = Image.open(args.input).convert("RGBA")

    # White-matte the subject on black so the glyph figure reads on dark bg.
    bg = Image.new("RGBA", img.size, (13, 13, 13, 255))
    img = Image.alpha_composite(bg, img).convert("L")

    cols: int = args.columns
    fs: float = args.font_size
    cell_w: float = fs * 0.62      # reliable advance for monospace
    cell_h: float = fs * 1.22      # line height

    aspect = img.height / img.width
    rows = max(8, math.ceil(cols * aspect * (cell_w / cell_h)))

    # Downscale the photo to the grid for sampling.
    thumb = img.resize((cols, rows), Image.LANCZOS)
    px = asarray(thumb)

    # Small luma normalisation so the figure pops.
    lo, hi = int(px.min()), int(px.max())
    span = max(1, hi - lo)

    lines: list[str] = []
    for y in range(rows):
        row_chars: list[str] = []
        for x in range(cols):
            v = int(px[y][x])
            n = clip((v - lo) / span, 0.0, 1.0)          # 0 = darkest
            ch = RAMP[min(len(RAMP) - 1, int((1.0 - n) * (len(RAMP) - 1)))]
            gi = min(len(GOLD_RAMP) - 1, int(n * (len(GOLD_RAMP) - 1)))
            row_chars.append((ch, gi, int(round(n * 255))))
        lines.append(row_chars)

    # Layout ---------------------------------------------------------- #
    pad_x, pad_y = 20, 14
    title_h = 34
    content_w = cols * cell_w
    content_h = rows * cell_h
    W = int(content_w + pad_x * 2)
    H = int(title_h + content_h + pad_y * 2)

    # Rescale font if the card would exceed the target width.
    if W > args.card_width:
        fs = fs * args.card_width / W
        cell_w = fs * 0.62
        cell_h = fs * 1.22
        content_w = cols * cell_w
        content_h = rows * cell_h
        W = int(content_w + pad_x * 2)
        H = int(title_h + content_h + pad_y * 2)

    text_w = f"{fs}px"

    # SVG document ---------------------------------------------------- #
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="ASCII portrait of Iftakher Uddin Rishad">')

    parts.append(f"""<defs>
  <linearGradient id="cipherBg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0d0d0d"/><stop offset="0.55" stop-color="#0a0a0c"/><stop offset="1" stop-color="#050506"/>
  </linearGradient>
  <linearGradient id="cipherEdge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#3f3f46"/><stop offset="0.5" stop-color="#6b5620"/><stop offset="1" stop-color="#3f3f46"/>
  </linearGradient>
  <radialGradient id="subjectGlow" cx="0.5" cy="0.42" r="0.62">
    <stop offset="0" stop-color="#d4af37" stop-opacity="0.16"/>
    <stop offset="0.55" stop-color="#d4af37" stop-opacity="0.05"/>
    <stop offset="1" stop-color="#000000" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="goldTitle" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#f0d980"/><stop offset="0.5" stop-color="#d4af37"/><stop offset="1" stop-color="#f0d980"/>
  </linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="6" stdDeviation="14" flood-color="#000000" flood-opacity="0.7"/>
  </filter>
  <filter id="softGlow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="scan"><rect id="scanRect" x="0" y="0" width="{W}" height="0"/></clipPath>
  <style>{CSS}</style>
</defs>""")

    # Terminal card
    parts.append(f"""
<g filter="url(#shadow)">
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="16" fill="url(#cipherBg)" stroke="url(#cipherEdge)" stroke-width="1.5"/>
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="16" fill="none" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1"/>
  <rect x="{pad_x-10}" y="{title_h+4}" width="{W-(pad_x-10)*2}" height="{H-title_h-4-pad_y+4}" rx="6" fill="url(#subjectGlow)"/>
</g>
<g>
  <circle cx="{pad_x}" cy="{title_h*0.5}" r="5.2" fill="#ff5f57"/>
  <circle cx="{pad_x+17}" cy="{title_h*0.5}" r="5.2" fill="#febc2e"/>
  <circle cx="{pad_x+34}" cy="{title_h*0.5}" r="5.2" fill="#28c840"/>
  <text x="{pad_x+50}" y="{title_h*0.5+5}" font-family="{FONT_STACK}" font-size="{fs*1.25}px" font-weight="700"
        fill="url(#goldTitle)" letter-spacing="3">The Cipher Stack</text>
  <line x1="{pad_x}" y1="{title_h+2}" x2="{W-pad_x}" y2="{title_h+2}" stroke="#ffffff" stroke-opacity="0.06"/>
</g>""")

    # Kinetic wipe (SMIL) + staggered CSS lines.
    parts.append(f"""
<g clip-path="url(#scan)">
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="16" fill="url(#cipherBg)" opacity="0"/>
  <animate xlink:href="#scanRect" attributeName="height" from="0" to="{H}" dur="2.6s" fill="freeze" begin="0.4s"
           calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1"/>
  <g font-family="{FONT_STACK}" font-size="{text_w}" font-weight="700" font-variant-ligatures="none">""")

    for i, row in enumerate(lines):
        y = title_h + pad_y + (i + 1) * cell_h
        tsec = 0.35 + i * 0.045
        parts.append(f'<text x="{pad_x}" y="{y:.1f}" class="fin" style="animation-delay:{tsec:.2f}s">')
        for (ch, gi, nv) in row:
            if ch == " ":
                parts.append("<tspan xml:space=\"preserve\"> </tspan>")
                continue
            parts.append(f'<tspan class="g{gi}">{ch}</tspan>')
        parts.append("</text>")

    parts.append("</g></g></svg>")

    out = "".join(parts)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"[ascii] wrote {args.output}  ({W}x{H}px, {cols}x{rows} grid)  -> {os.path.getsize(args.output)/1024:.1f} KB")
    return 0


CSS = r"""
@keyframes fin {
  0%   { opacity: 0; transform: translateY(9px); filter: blur(1.5px); }
  60%  { opacity: 0.55; }
  100% { opacity: 1; transform: translateY(0); filter: blur(0); }
}
.fin { animation: fin .55s cubic-bezier(0.22, 1, 0.36, 1) both; }
.svg--static .fin { animation: none; opacity: 1; }
text { paint-order: stroke; }
.g0 { fill: #fbeeb6; } .g1 { fill: #f0d980; } .g2 { fill: #e6c24f; }
.g3 { fill: #d4af37; } .g4 { fill: #b68f2b; } .g5 { fill: #8f6f22; } .g6 { fill: #6f5620; }
"""


if __name__ == "__main__":
    sys.exit(main())