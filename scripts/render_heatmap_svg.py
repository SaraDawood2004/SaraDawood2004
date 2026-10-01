from pathlib import Path
from datetime import date, timedelta
import json
import re

import requests
from bs4 import BeautifulSoup


USERNAME = "SaraDawood2004"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"


def parse_count(text):
    if not text:
        return 0

    match = re.search(r"([\d,]+)\s+contribution", text)

    if match:
        return int(match.group(1).replace(",", ""))

    return 0


def fetch_page():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140 Safari/537.36"
        ),
        "Accept": "text/html",
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def extract_days(html):

    soup = BeautifulSoup(html, "html.parser")

    days = []

    # Current GitHub contribution calendar uses td[data-date]
    cells = soup.select("td[data-date]")

    for cell in cells:

        day = cell.get("data-date")

        if not day:
            continue

        level = cell.get("data-level", "0")

        try:
            level = int(level)
        except ValueError:
            level = 0

        text = cell.get("aria-label", "")
        count = parse_count(text)

        if count == 0:
            count = parse_count(cell.get_text(" ", strip=True))

        days.append({
            "date": day,
            "count": count,
            "level": level
        })

    return days


def calculate_stats(days):

    sorted_days = sorted(
        days,
        key=lambda x: x["date"]
    )

    # ---------------------------------------------------------
    # Current streak
    # ---------------------------------------------------------
    current_streak = 0

    today = date.today()

    lookup = {
        item["date"]: item["count"]
        for item in sorted_days
    }

    check = today

    while True:

        key = check.isoformat()

        if lookup.get(key, 0) > 0:
            current_streak += 1
            check -= timedelta(days=1)
        else:
            break

    # ---------------------------------------------------------
    # Longest streak
    # ---------------------------------------------------------
    longest_streak = 0
    running = 0

    for item in sorted_days:

        if item["count"] > 0:
            running += 1
            longest_streak = max(
                longest_streak,
                running
            )
        else:
            running = 0

    # ---------------------------------------------------------
    # Best day
    # ---------------------------------------------------------
    best_day = None

    if sorted_days:
        best_day = max(
            sorted_days,
            key=lambda x: x["count"]
        )

    # ---------------------------------------------------------
    # Monthly totals
    # ---------------------------------------------------------
    monthly = {}

    for item in sorted_days:

        month = item["date"][:7]

        monthly[month] = (
            monthly.get(month, 0)
            + item["count"]
        )

    total = sum(
        item["count"]
        for item in sorted_days
    )

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly
    }


def main():

    print(f"Fetching contributions for {USERNAME}...")

    html = fetch_page()

    days = extract_days(html)

    if not days:
        raise RuntimeError(
            "No contribution cells were found. "
            "GitHub may have changed its contribution page structure."
        )

    stats = calculate_stats(days)

    result = {
        "username": USERNAME,
        "generated_at": date.today().isoformat(),
        "days": days,
        "stats": stats
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("Contribution data saved.")
    print(f"Days: {len(days)}")
    print(f"Total: {stats['total']}")
    print(f"Current streak: {stats['current_streak']}")
    print(f"Longest streak: {stats['longest_streak']}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()