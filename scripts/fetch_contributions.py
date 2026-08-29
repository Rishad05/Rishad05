#!/usr/bin/env python3
"""
fetch_contributions.py
----------------------
Scrapes the public GitHub contribution calendar for a user WITHOUT any
API key (GitHub renders the calendar as HTML on the profile page).

Computes and persists into `data/contributions.json`:

  * raw per-day counts + level
  * total contributions (last year)
  * current streak, longest streak
  * best day, active days, level histogram
  * last-year date range

Usage:
    python scripts/fetch_contributions.py [username]
Dependencies: requests, beautifulsoup4 (--no-cache-dir install).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

GITHUB_USER = os.environ.get("GITHUB_USER", "Rishad05")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_calendar_html(username: str, conv) -> str:
    """Fetch the contributions fragment; fall back to the profile page."""
    url = f"https://github.com/users/{username}/contributions"
    try:
        r = conv.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        if 'data-date' in r.text or '<rect' in r.text or "contribution-calendar" in r.text:
            return r.text
    except Exception as exc:  # noqa: BLE001
        print(f"[fetch] fragment failed ({type(exc).__name__}), trying profile page ...")
    r = conv.get(f"https://github.com/{username}", headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r.text


def parse_calendar(html: str):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Year-navigation titles that contain "X contributions" / streaks.
    year_text = " ".join(t.get_text(" ", strip=True) for t in soup.select(".js-year-link"))
    m = re.search(r"([\d,]+)\s+contributions? in the last year", year_text)
    year_total: int | None = int(m.group(1).replace(",", "")) if m else None

    # Per-day rectangles (all years shown in the fragment).
    daily = []
    for rect in soup.find_all("rect", attrs={"data-date": True}):
        dt = rect.get("data-date")
        level = int(rect.get("data-level", rect.get("aria-level", 0)) or 0)
        count_attr = rect.get("data-count")
        try:
            count = int(count_attr) if count_attr is not None else level
        except (TypeError, ValueError):
            count = level
        daily.append({"date": dt, "count": count, "level": level})

    if not daily:
        # New GitHub layout: <td class="ContributionCalendar-day" data-date data-level>,
        # with the real count in a sibling <tool-tip> ("N contributions on <date>.").
        for td in soup.find_all("td", attrs={"data-date": True}):
            dt = td.get("data-date")
            level = int(td.get("data-level") or 0)
            count = level  # fallback when the tool-tip can't be parsed
            try:
                tip = soup.find("tool-tip", attrs={"for": td.get("id")})
                if tip is not None:
                    m2 = re.search(r"([\d,]+)\s+contributions?", tip.get_text(" ", strip=True))
                    if m2:
                        count = int(m2.group(1).replace(",", ""))
            except Exception:  # noqa: BLE001
                pass
            daily.append({"date": dt, "count": count, "level": level})

    return year_total, daily


def analyse(daily: list[dict], year_total: int | None):
    records = {d["date"]: d["count"] for d in daily}
    if not records:
        return None

    dates = sorted(records)
    first, last = dates[0], dates[-1]
    total = sum(records.values())

    counts_by_date = {}
    for d in dates:
        counts_by_date[d] = records[d]

    # Streaks (rolling forward from the earliest recorded date).
    current_streak = 0
    longest_streak = 0
    run = 0
    cursor = datetime.strptime(first, "%Y-%m-%d").date()
    end = datetime.strptime(last, "%Y-%m-%d").date()
    today = date.today()
    while cursor <= end:
        if counts_by_date.get(cursor.strftime("%Y-%m-%d"), 0) > 0:
            run += 1
            longest_streak = max(longest_streak, run)
        else:
            run = 0
        cursor += timedelta(days=1)

    # Current streak: count consecutive contribution days ending today
    # (or yesterday if today hasn't landed yet).
    probe = today
    if counts_by_date.get(probe.strftime("%Y-%m-%d"), 0) == 0:
        past = today - timedelta(days=1)
        if all(counts_by_date.get((past - timedelta(days=k)).strftime("%Y-%m-%d"), 0) > 0 for k in range(2)):
            probe = past
    current_streak = 0
    while probe >= datetime.strptime(first, "%Y-%m-%d").date():
        if counts_by_date.get(probe.strftime("%Y-%m-%d"), 0) > 0:
            current_streak += 1
            probe -= timedelta(days=1)
        else:
            break

    best = max(dates, key=lambda d: (counts_by_date[d], d))
    active = sum(1 for c in records.values() if c > 0)

    level_hist = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
    for d in daily:
        level_hist[str(min(4, max(0, d["level"])))] += 1

    return {
        "first_day": first,
        "last_day": last,
        "total_contributions": max(total, year_total or 0),
        "year_total_display": f"{year_total:,}" if year_total else f"{total:,}",
        "current_streak_days": current_streak,
        "longest_streak_days": longest_streak,
        "best_day": {"date": best, "count": counts_by_date[best]},
        "active_days": active,
        "level_histogram": level_hist,
        "counts_by_date": {k: v for k, v in sorted(counts_by_date.items())},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Scrape a GitHub contribution calendar (no API key).")
    ap.add_argument("username", nargs="?", default=GITHUB_USER)
    ap.add_argument("--output", default=os.path.join("data", "contributions.json"))
    args = ap.parse_args()

    import requests

    session = requests.Session()
    print(f"[fetch] scraping calendar for @{args.username} ...")
    try:
        html = fetch_calendar_html(args.username, session)
    except Exception as exc:  # noqa: BLE001
        print(f"[fetch] ERROR: could not reach GitHub: {exc}", file=sys.stderr)
        return 1

    year_total, daily = parse_calendar(html)
    print(f"[fetch] parsed {len(daily)} calendar days (year total ~ {year_total})")

    metrics = analyse(daily, year_total)
    if not metrics:
        print("[fetch] ERROR: no calendar data parsed.", file=sys.stderr)
        return 1

    payload = {
        "username": args.username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fetched_on": date.today().isoformat(),
        **metrics,
        "daily": [
            {"date": d["date"], "count": d["count"], "level": d["level"]}
            for d in sorted(daily, key=lambda x: x["date"])
        ],
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(
        f"[fetch] saved {args.output}: total={metrics['total_contributions']:,} | "
        f"current_streak={metrics['current_streak_days']}d | "
        f"longest_streak={metrics['longest_streak_days']}d | "
        f"best={metrics['best_day']['date']} ({metrics['best_day']['count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())