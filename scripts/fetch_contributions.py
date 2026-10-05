from pathlib import Path
from datetime import date, timedelta
import json

import requests


# ============================================================
# CONFIGURATION
# ============================================================

USERNAME = "SaraDawood2004"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"

URL = (
    f"https://github-contributions-api.jogruber.de/v4/"
    f"{USERNAME}?y=all"
)


# ============================================================
# FETCH ALL CONTRIBUTION HISTORY
# ============================================================

def fetch_contributions():
    print()
    print(
        f"Fetching ALL GitHub contribution history "
        f"for {USERNAME}..."
    )

    print(f"URL: {URL}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "contributions" not in data:
        raise RuntimeError(
            "The contribution API did not return "
            "a contributions array."
        )

    return data


# ============================================================
# CALCULATE STREAKS
# ============================================================

def calculate_streaks(days):
    active_dates = {
        item["date"]
        for item in days
        if item.get("count", 0) > 0
    }

    if not active_dates:
        return 0, 0

    sorted_dates = sorted(
        date.fromisoformat(day)
        for day in active_dates
    )

    # --------------------------------------------------------
    # Current streak
    # --------------------------------------------------------

    current_streak = 0
    today = date.today()
    check = today

    # GitHub's streak logic allows today to be inactive
    # while yesterday can still be the current streak.
    if check.isoformat() not in active_dates:
        check -= timedelta(days=1)

    while check.isoformat() in active_dates:
        current_streak += 1
        check -= timedelta(days=1)

    # --------------------------------------------------------
    # Longest streak
    # --------------------------------------------------------

    longest_streak = 0
    running = 0
    previous = None

    for current in sorted_dates:
        if (
            previous is not None
            and current == previous + timedelta(days=1)
        ):
            running += 1
        else:
            running = 1

        longest_streak = max(
            longest_streak,
            running
        )

        previous = current

    return current_streak, longest_streak


# ============================================================
# CALCULATE YEARLY STATISTICS
# ============================================================

def calculate_year_stats(days):
    yearly = {}

    for item in days:
        year = item["date"][:4]

        if year not in yearly:
            yearly[year] = {
                "total": 0,
                "active_days": 0
            }

        count = int(
            item.get("count", 0)
        )

        yearly[year]["total"] += count

        if count > 0:
            yearly[year]["active_days"] += 1

    return yearly


# ============================================================
# MAIN
# ============================================================

def main():
    data = fetch_contributions()

    raw_days = data.get(
        "contributions",
        []
    )

    if not raw_days:
        raise RuntimeError(
            "No contribution data was returned."
        )

    # --------------------------------------------------------
    # Normalize contribution data
    # --------------------------------------------------------

    days = []

    for item in raw_days:
        contribution_date = item.get("date")

        if not contribution_date:
            continue

        count = int(
            item.get("count", 0)
        )

        level = int(
            item.get("level", 0)
        )

        days.append(
            {
                "date": contribution_date,
                "count": count,
                "level": level
            }
        )

    # Oldest → newest
    days.sort(
        key=lambda x: x["date"]
    )

    # --------------------------------------------------------
    # Yearly totals returned by the API
    # --------------------------------------------------------

    api_year_totals = {
        str(year): int(total)
        for year, total in data.get(
            "total",
            {}
        ).items()
        if str(year).isdigit()
    }

    # --------------------------------------------------------
    # Calculate additional statistics
    # --------------------------------------------------------

    current_streak, longest_streak = calculate_streaks(
        days
    )

    yearly_stats = calculate_year_stats(
        days
    )

    years = sorted(
        {
            item["date"][:4]
            for item in days
        }
    )

    # --------------------------------------------------------
    # Find highest contribution day
    # --------------------------------------------------------

    best_day = max(
        days,
        key=lambda item: item["count"]
    )

    # --------------------------------------------------------
    # Build final JSON
    # --------------------------------------------------------

    result = {
        "username": USERNAME,

        "generated_at": date.today().isoformat(),

        "years": years,

        "total_contributions": sum(
            api_year_totals.values()
        ),

        "yearly_totals": api_year_totals,

        "days": days,

        "stats": {
            "total": sum(
                api_year_totals.values()
            ),

            "current_streak": current_streak,

            "longest_streak": longest_streak,

            "best_day": best_day,

            "yearly": yearly_stats
        }
    }

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Terminal output
    # --------------------------------------------------------

    print()
    print("========================================")
    print(" GitHub Contribution History")
    print("========================================")

    print(
        f"Years found: {len(years)}"
    )

    print(
        f"Range: {years[0]} → {years[-1]}"
    )

    print()

    for year in years:
        total = api_year_totals.get(
            year,
            0
        )

        active_days = yearly_stats.get(
            year,
            {}
        ).get(
            "active_days",
            0
        )

        print(
            f"{year}: "
            f"{total} contributions "
            f"({active_days} active days)"
        )

    print()

    print(
        f"All-time contributions: "
        f"{sum(api_year_totals.values())}"
    )

    print(
        f"Current streak: "
        f"{current_streak}"
    )

    print(
        f"Longest streak: "
        f"{longest_streak}"
    )

    print(
        f"Best day: "
        f"{best_day['date']} "
        f"({best_day['count']} contributions)"
    )

    print()

    print(
        f"Output: {OUTPUT}"
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()