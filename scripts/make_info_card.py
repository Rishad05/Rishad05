#!/usr/bin/env python3
"""
make_info_card.py
-----------------
Generates `info-card.svg` — a neofetch / terminal system-info card that
visually matches the height of the ASCII portrait card:

  * macOS traffic-light dots + "The Cipher Stack" title bar.
  * Gold key labels, silver value labels (system-info style).
  * CSS keyframe staggered fade-in per line.

Usage:
    python scripts/make_info_card.py [--output info-card.svg]
    python scripts/make_info_card.py --height 480 [--width 490]

The card height defaults to the height of a sibling `hxni-ascii.svg` so the
two cards tile perfectly in the README table.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

FONT_STACK = "JetBrains Mono, ui-monospace, Cascadia Code, Consolas, 'Courier New', monospace"

DATA = [
    ("OS",        "void / cyber", ""),
    ("Host",      "Iftakher Uddin Rishad", ""),
    ("Role",      "Software Engineer", ""),
    ("Location",  "Dhaka, Bangladesh", ""),
    ("Frontend",  "React  TypeScript  Vite  Tailwind  Bootstrap", ""),
    ("Backend",   "PHP  Laravel  Node.js  Express  Prisma  MySQL", ""),
    ("DB",        "PostgreSQL  REST APIs", ""),
    ("Tools",     "Git  GitHub  VS Code  Postman  Vercel  Netlify", ""),
    ("Socials",   "LinkedIn  Instagram  Facebook", ""),
    ("URL",       "my-portfolio05.web.app", "link"),
    ("GitHub",    "github.com/Rishad05", "link"),
]


def read_ascii_height() -> int:
    """Match the height of hxni-ascii.svg when present."""
    if not os.path.exists("hxni-ascii.svg"):
        return 0
    try:
        with open("hxni-ascii.svg", "r", encoding="utf-8") as f:
            head = f.read(2000)
        m = re.search(r'viewBox="0 0 \d+ (\d+)"', head)
        if m:
            return int(m.group(1))
    except Exception:  # noqa: BLE001
        pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build info-card.svg terminal info card.")
    ap.add_argument("--output", default="info-card.svg")
    ap.add_argument("--width", type=int, default=490)
    ap.add_argument("--height", type=int, default=0, help="Match hxni-ascii.svg by default.")
    args = ap.parse_args()

    H = args.height or read_ascii_height() or 500
    W = args.width

    pad_x = 24
    title_h = 34
    key_w = 96
    fs_val = 12.8
    fs_key = 12.8
    line_h = 30
    start_y = title_h + 34
    end_y = H - 24

    # Vertically centre the rows in the available space.
    n = len(DATA)
    total = n * line_h
    top = start_y + max(0, (end_y - start_y - total) // 2)

    # Longest value -> shrink font if it would overflow the card.
    max_val = max(len(v) for _, v, _ in DATA)
    while (key_w + max_val * fs_val * 0.62) > (W - pad_x * 2):
        fs_val -= 0.3
        fs_key = fs_val
        line_h = 30
    fs_line = str(f"{fs_key * 1.0}px")

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="System information for Iftakher Uddin Rishad">'
    )
    p.append(f"""<defs>
  <linearGradient id="icBg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0b0f14"/><stop offset="0.55" stop-color="#080c11"/><stop offset="1" stop-color="#04060a"/>
  </linearGradient>
  <linearGradient id="icEdge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#16303a"/><stop offset="0.5" stop-color="#22d3ee" stop-opacity="0.6"/><stop offset="1" stop-color="#16303a"/>
  </linearGradient>
  <linearGradient id="icTitle" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#b8f1ff"/><stop offset="0.5" stop-color="#22d3ee"/><stop offset="1" stop-color="#b8f1ff"/>
  </linearGradient>
  <linearGradient id="icAccentBar" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#14323a"/>
  </linearGradient>
  <filter id="icShadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="6" stdDeviation="14" flood-color="#000000" flood-opacity="0.7"/>
  </filter>
  <style>{CSS}</style>
</defs>""")

    p.append(f"""
<g filter="url(#icShadow)">
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="16" fill="url(#icBg)" stroke="url(#icEdge)" stroke-width="1.5"/>
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="16" fill="none" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1"/>
</g>
<g>
  <circle cx="{pad_x}" cy="{title_h*0.5}" r="5.2" fill="#ff5f57"/>
  <circle cx="{pad_x+17}" cy="{title_h*0.5}" r="5.2" fill="#febc2e"/>
  <circle cx="{pad_x+34}" cy="{title_h*0.5}" r="5.2" fill="#28c840"/>
  <text x="{pad_x+50}" y="{title_h*0.5+5}" font-family="{FONT_STACK}" font-size="{fs_val*1.2}px" font-weight="700"
        fill="url(#icTitle)" letter-spacing="3">Iftakher Uddin Rishad</text>
  <line x1="{pad_x}" y1="{title_h+2}" x2="{W-pad_x}" y2="{title_h+2}" stroke="#ffffff" stroke-opacity="0.06"/>
</g>""")

    # Neonfetch colour swatch (left block)
    sw = 26
    sun = ["#ff5f57", "#febc2e", "#28c840"]
    x0 = pad_x + 2
    y0 = top - 6
    for i, c in enumerate(sun):
        p.append(f'<rect x="{x0 + i*sw}" y="{y0}" width="{sw-4}" height="10" rx="2.5" fill="{c}" opacity="0.9"/>')
    x0 += 3 * sw
    for c in ["#3794ff", "#b06ceb", "#ff5fa8"]:
        p.append(f'<rect x="{x0}" y="{y0}" width="{sw-4}" height="10" rx="2.5" fill="{c}" opacity="0.9"/>')
        x0 += sw

    p.append(f'<rect x="{pad_x}" y="{y0+16}" width="{W-pad_x*2 + 4}" height="2" rx="1" fill="url(#icAccentBar)" opacity="0.85"/>')

    # Rows
    for i, (key, val, kind) in enumerate(DATA):
        y = top + (i + 1) * line_h
        dg = 0.30 + i * 0.085
        key_col = "#22d3ee"
        if kind == "link":
            key_col = "#57dcf5"
        val_fill = "#c9c9d2" if kind != "link" else "#9fd3ff"
        p.append(f'<g class="icrow" style="animation-delay:{dg:.2f}s">')
        p.append(
            f'<text x="{pad_x}" y="{y}" font-family="{FONT_STACK}" font-size="{fs_line}" font-weight="700" '
            f'fill="{key_col}">{key}</text>'
        )
        p.append(
            f'<text x="{pad_x + key_w}" y="{y}" font-family="{FONT_STACK}" font-size="{fs_line}" font-weight="400" '
            f'fill="{val_fill}">{val}</text>'
        )
        p.append("</g>")

    # Blinking block cursor on the last line.
    curb = top + (n + 1) * line_h - 2
    p.append(
        f'<rect class="cursor" x="{pad_x + key_w - 14}" y="{curb - 14}" width="9" height="16" rx="1.5" fill="#22d3ee"/>'
    )

    p.append("</svg>")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("".join(p))
    print(f"[infocard] wrote {args.output}  ({W}x{H}px) -> {os.path.getsize(args.output)/1024:.1f} KB")
    return 0


CSS = r"""
@keyframes fin {
  0%   { opacity: 0; transform: translateX(-10px); filter: blur(1px); }
  100% { opacity: 1; transform: translateX(0);    filter: blur(0); }
}
.icrow { animation: fin .5s cubic-bezier(0.22,1,0.36,1) both; }
@keyframes blinkk { 0%,49% { opacity: 1; } 50%,100% { opacity: 0; } }
.cursor { animation: blinkk 1.1s steps(1) infinite; }
"""


if __name__ == "__main__":
    sys.exit(main())