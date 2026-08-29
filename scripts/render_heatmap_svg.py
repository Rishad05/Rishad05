#!/usr/bin/env python3
"""
render_heatmap_svg.py
---------------------
Renders `contrib-heatmap.svg` — a high-resolution, custom-themed
contribution heatmap (github-style calendar) in gold-on-void.

Input : data/contributions.json (produced by fetch_contributions.py)
Output: contrib-heatmap.svg (~860px wide)

Usage:
    python scripts/render_heatmap_svg.py [--input data/contributions.json]
                                          [--output contrib-heatmap.svg]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

FONT_STACK = "Inter, ui-sans-serif, 'Segoe UI', system-ui, sans-serif"
MONO_STACK = "JetBrains Mono, ui-monospace, Consolas, monospace"

# Gold gradient ramp for contribution levels (0 .. 4).
LEVELS = [
    "#14161c",   # level 0 — void
    "#3a2c12",   # level 1
    "#6b4a15",   # level 2
    "#a17c1c",   # level 3
    "#e9c256",   # level 4 — bright gold
]


def fmt(n: int) -> str:
    return f"{n:,}"


class Layout:
    PAD = 20
    WD = 32            # weekday label column
    HEADER = 96
    MONTH = 20
    CELL = 13
    STEP = 15
    GAP_M = 6
    GAP_G = 10
    FOOTER = 44


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the contribution heatmap SVG.")
    ap.add_argument("--input", default=os.path.join("data", "contributions.json"))
    ap.add_argument("--output", default="contrib-heatmap.svg")
    ap.add_argument("--width", type=int, default=860)
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"[heatmap] ERROR: {args.input} not found. Run fetch_contributions.py first.", file=sys.stderr)
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    daily_by_date = {d["date"]: d for d in data.get("daily", [])}
    cbd = data.get("counts_by_date", {})
    today = date.today()

    # Anchor the grid: GitHub-style 52-week window ending at the most recent
    # recorded day. Columns run Sunday -> Saturday.
    last_day = datetime.strptime(data.get("last_day", today.isoformat()), "%Y-%m-%d").date()
    one_year_back = last_day - timedelta(days=364)
    grid_start = one_year_back - timedelta(days=one_year_back.weekday())  # previous Sunday
    days_span = (last_day - grid_start).days
    weeks = days_span // 7 + 1
    if weeks % 4 != 0:
        weeks = ((weeks // 4) + 1) * 4

    L = Layout()
    GRID_W = weeks * L.STEP
    GRID_H = 7 * L.CELL + 6 * (L.STEP - L.CELL)
    W = args.width
    gridX = L.PAD + L.WD
    center_extra = (W - (gridX + GRID_W + L.PAD)) // 2
    totalH = L.HEADER + L.MONTH + L.GAP_M + GRID_H + L.GAP_G + L.FOOTER + L.PAD

    # ------------------------------------------------------------ stats
    total = data.get("total_contributions", sum(cbd.values()))
    streak = data.get("current_streak_days", 0)
    longest = data.get("longest_streak_days", 0)
    best = data.get("best_day", {"date": "--", "count": 0})
    year_txt = data.get("year_total_display", fmt(total))

    # --------------------------------------------------------------- header
    stats_chips = [
        ("TOTAL", fmt(int(total))),
        ("CURRENT STREAK", f"{streak} days"),
        ("LONGEST", f"{longest} days"),
        ("BEST DAY", f"{best.get('count', 0)} commits"),
    ]

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}" height="{totalH}" viewBox="0 0 {W} {totalH}" role="img" '
        f'aria-label="Contribution heatmap for @Rishad05 — {fmt(int(total))} contributions in the last year">'
    )
    p.append(f"""<defs>
  <linearGradient id="hmBg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0c0c0e"/><stop offset="0.6" stop-color="#09090b"/><stop offset="1" stop-color="#050506"/>
  </linearGradient>
  <linearGradient id="hmTitle" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#d4af37"/><stop offset="1" stop-color="#fdf4c9"/>
  </linearGradient>
  <linearGradient id="hmBar" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#6b4a15"/><stop offset="0.5" stop-color="#e9c256"/><stop offset="1" stop-color="#6b4a15"/>
  </linearGradient>
  <path id="hmCell" d="M4 0 h5 a4 4 0 0 1 4 4 v5 a4 4 0 0 1 -4 4 h-5 a4 4 0 0 1 -4 -4 v-5 a4 4 0 0 1 4 -4 z"/>
  <filter id="hmShadow" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="0" dy="8" stdDeviation="18" flood-color="#000" flood-opacity="0.65"/>
  </filter>
  <style>
    @keyframes hmgrid {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    .g-cell {{ animation: hmgrid .8s ease-out both; }}
    .g-cell:hover {{ stroke: #ffe9a8; stroke-width: 1; }}
  </style>
</defs>""")

    # --------------------------------------------------------------- card
    p.append(f"""
<g filter="url(#hmShadow)">
  <rect x="4" y="4" width="{W-8}" height="{totalH-8}" rx="18" fill="url(#hmBg)" stroke="#2b2b31" stroke-width="1"/>
</g>
<g>
  <text x="{gridX + center_extra}" y="42" font-family="{FONT_STACK}" font-size="26" font-weight="800" fill="url(#hmTitle)" letter-spacing="1">Contribution Activity</text>
  <text x="{gridX + center_extra}" y="66" font-family="{MONO_STACK}" font-size="12.5" fill="#8b8b95">@Rishad05 &#160;&#183;&#160; {year_txt} contributions in the last year &#160;&#183;&#160; {best.get('date','--')}</text>
  <rect x="{gridX + center_extra}" y="76" width="150" height="3" rx="1.5" fill="url(#hmBar)"/>
</g>""")

    # Stats chips (top-right)
    chip_y = 30
    cx = gridX + center_extra + GRID_W
    for label, value in stats_chips:
        tw = len(value) * 7.2 + 34
        p.append(f'<rect x="{cx - tw}" y="{chip_y}" width="{tw}" height="30" rx="8" fill="#101114" stroke="#26262b" stroke-width="1"/>')
        p.append(f'<text x="{cx - tw + 12}" y="{chip_y + 12}" font-family="{MONO_STACK}" font-size="8.5" fill="#77777f" letter-spacing="0.5">{label}</text>')
        p.append(f'<text x="{cx - tw + 12}" y="{chip_y + 25}" font-family="{MONO_STACK}" font-size="13" font-weight="700" fill="#e6c24f">{value}</text>')
        cx -= tw + 10

    # ------------------------------------------------------------- month labels
    month_anchor = L.HEADER + L.MONTH//2 + 2
    p.append(f'<text x="{gridX + center_extra}" y="{month_anchor}" font-family="{MONO_STACK}" font-size="11" fill="#8b8b95">{last_day.strftime("%B %Y")}</text>')

    # ------------------------------------------------------------ weekday labels
    dow_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    wx = gridX - 8
    for d, lab in dow_labels.items():
        p.append(f'<text x="{wx}" y="{L.HEADER + L.MONTH + L.GAP_M + d * L.STEP + L.CELL - 3}" text-anchor="end" font-family="{MONO_STACK}" font-size="9.5" fill="#7d7d87">{lab}</text>')

    # ------------------------------------------------------------ cells
    gy = L.HEADER + L.MONTH + L.GAP_M
    max_lev = 4
    for d in range(days_span + 1):
        dt = (grid_start + timedelta(days=d)).isoformat()
        if dt in daily_by_date:
            lev = daily_by_date[dt]["level"]
            count = daily_by_date[dt]["count"]
        else:
            lev, count = 0, 0
        wk = d // 7
        dw = d % 7
        x = gridX + center_extra + wk * L.STEP
        y = gy + dw * L.STEP
        idx = min(int(lev * (max_lev / 3)), max_lev)  # GitHub levels max at 3 -> bright gold
        fill = LEVELS[idx]
        opacity = 1.0
        if dt > last_day.isoformat():
            opacity = 0.35
        delay = 0.02 * wk + 0.004 * dw
        t = f'{dt} : {count} contribution' + ('' if count == 1 else 's')
        p.append(f'<use href="#hmCell" class="g-cell" x="{x}" y="{y}" width="{L.CELL}" height="{L.CELL}" fill="{fill}" opacity="{opacity:.2f}" style="animation-delay:{delay:.2f}s" transform="translate(0,0)"><title>{t}</title></use>')

    # ------------------------------------------------------------ footer legend
    fy = gy + GRID_H + L.GAP_G
    p.append(f'<text x="{gridX + center_extra}" y="{fy + 16}" font-family="{MONO_STACK}" font-size="10.5" fill="#7d7d87">Less</text>')
    lx = gridX + center_extra + 38
    for lv in range(5):
        p.append(f'<use href="#hmCell" x="{lx}" y="{fy + 6}" width="{L.CELL}" height="{L.CELL}" fill="{LEVELS[lv]}"><title>level {lv}</title></use>')
        lx += L.STEP
    p.append(f'<text x="{lx + 4}" y="{fy + 16}" font-family="{MONO_STACK}" font-size="10.5" fill="#7d7d87">More</text>')
    p.append(f'<text x="{gridX + center_extra + GRID_W}" y="{fy + 16}" text-anchor="end" font-family="{MONO_STACK}" font-size="10.5" fill="#5f5f68">last 365 days · auto-rendered daily · Rishad05</text>')

    p.append("</svg>")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("".join(p))
    print(f"[heatmap] wrote {args.output}  ({W}x{totalH}px, {weeks} weeks) -> {os.path.getsize(args.output)/1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())