from pathlib import Path
from datetime import date, timedelta
import json
import re

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

USERNAME = "SaraDawood2004"

ROOT = Path(__file__).resolve().parent.parent

OUTPUT = ROOT / "data" / "contributions.json"

URL = (
    f"https://github.com/users/"
    f"{USERNAME}/contributions"
)


# ============================================================
# FETCH GITHUB PAGE
# ============================================================

def fetch_page():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
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


# ============================================================
# FIND TOTAL CONTRIBUTIONS
# ============================================================

def extract_total_contributions(soup):

    # GitHub usually contains something similar to:
    #
    # "106 contributions in the last year"
    #
    # Search the entire page text.

    page_text = soup.get_text(
        " ",
        strip=True
    )

    patterns = [
        r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year",
        r"([\d,]+)\s+contributions?",
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            page_text,
            re.IGNORECASE
        )

        if matches:

            numbers = []

            for value in matches:

                try:
                    numbers.append(
                        int(
                            value.replace(",", "")
                        )
                    )
                except ValueError:
                    pass

            if numbers:

                # The yearly total is normally
                # the largest matching value.
                return max(numbers)

    return 0


# ============================================================
# EXTRACT CONTRIBUTION CALENDAR
# ============================================================

def extract_days(soup):

    days = []

    cells = soup.select(
        "td[data-date]"
    )

    for cell in cells:

        day = cell.get(
            "data-date"
        )

        if not day:
            continue

        level = cell.get(
            "data-level",
            "0"
        )

        try:

            level = int(level)

        except (
            ValueError,
            TypeError
        ):

            level = 0

        # IMPORTANT:
        #
        # data-level is NOT the exact number of
        # contributions.
        #
        # It represents GitHub's contribution
        # intensity from 0 to 4.
        #
        # We therefore store it separately.

        days.append(
            {
                "date": day,
                "count": 0,
                "level": level
            }
        )

    return days


# ============================================================
# CALCULATE STREAKS FROM CONTRIBUTION LEVEL
# ============================================================

def calculate_streaks(days):

    sorted_days = sorted(
        days,
        key=lambda x: x["date"]
    )

    active_dates = {
        item["date"]
        for item in sorted_days
        if item["level"] > 0
    }

    # --------------------------------------------------------
    # Current streak
    # --------------------------------------------------------

    current_streak = 0

    today = date.today()

    check = today

    # If today's contribution is zero,
    # GitHub streak may actually end yesterday.
    #
    # So check today first, then yesterday.

    if check.isoformat() not in active_dates:

        check -= timedelta(
            days=1
        )

    while check.isoformat() in active_dates:

        current_streak += 1

        check -= timedelta(
            days=1
        )

    # --------------------------------------------------------
    # Longest streak
    # --------------------------------------------------------

    longest_streak = 0
    running = 0

    previous_date = None

    for item in sorted_days:

        if item["level"] <= 0:

            running = 0
            previous_date = None

            continue

        current_date = date.fromisoformat(
            item["date"]
        )

        if (
            previous_date is not None
            and current_date
            == previous_date + timedelta(days=1)
        ):

            running += 1

        else:

            running = 1

        longest_streak = max(
            longest_streak,
            running
        )

        previous_date = current_date

    return (
        current_streak,
        longest_streak
    )


# ============================================================
# MONTHLY ACTIVITY
# ============================================================

def calculate_monthly_activity(days):

    monthly = {}

    for item in days:

        month = item["date"][:7]

        if month not in monthly:

            monthly[month] = {
                "active_days": 0,
                "activity_level": 0
            }

        if item["level"] > 0:

            monthly[month]["active_days"] += 1

        monthly[month]["activity_level"] += (
            item["level"]
        )

    return monthly


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        f"Fetching contributions for "
        f"{USERNAME}..."
    )

    print(
        f"URL: {URL}"
    )

    # --------------------------------------------------------
    # Fetch page
    # --------------------------------------------------------

    html = fetch_page()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # --------------------------------------------------------
    # Extract total
    # --------------------------------------------------------

    total = extract_total_contributions(
        soup
    )

    # --------------------------------------------------------
    # Extract calendar
    # --------------------------------------------------------

    days = extract_days(
        soup
    )

    if not days:

        raise RuntimeError(
            "No contribution calendar cells "
            "were found."
        )

    # --------------------------------------------------------
    # Calculate streaks
    # --------------------------------------------------------

    (
        current_streak,
        longest_streak
    ) = calculate_streaks(
        days
    )

    # --------------------------------------------------------
    # Monthly activity
    # --------------------------------------------------------

    monthly = calculate_monthly_activity(
        days
    )

    # --------------------------------------------------------
    # Best activity day
    #
    # Since GitHub does not expose exact counts
    # in the current calendar cells, use the
    # highest activity level.
    # --------------------------------------------------------

    best_day = None

    if days:

        best_day = max(
            days,
            key=lambda x: x["level"]
        )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    result = {

        "username": USERNAME,

        "generated_at":
            date.today().isoformat(),

        "total_contributions":
            total,

        "days":
            days,

        "stats": {

            "total":
                total,

            "current_streak":
                current_streak,

            "longest_streak":
                longest_streak,

            "best_day":
                best_day,

            "monthly_totals":
                monthly
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

    print(
        "Contribution data saved."
    )

    print(
        f"Days: {len(days)}"
    )

    print(
        f"Total contributions: {total}"
    )

    print(
        f"Current streak: "
        f"{current_streak}"
    )

    print(
        f"Longest streak: "
        f"{longest_streak}"
    )

    if best_day:

        print(
            f"Highest activity day: "
            f"{best_day['date']} "
            f"(level {best_day['level']})"
        )

    print(
        f"Output: {OUTPUT}"
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()