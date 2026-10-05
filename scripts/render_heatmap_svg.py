from pathlib import Path
from datetime import date, timedelta
import json
import calendar
import os


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"

USERNAME = "SaraDawood2004"

STATIC = os.getenv("STATIC", "0") == "1"


# GitHub contribution colors
COLORS = {
    0: "#161B22",
    1: "#0E4429",
    2: "#006D32",
    3: "#26A641",
    4: "#39D353",
}


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"Contribution data not found: {INPUT}\n"
            "Run fetch_contributions.py first."
        )

    with INPUT.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# PREPARE ONE YEAR
# ============================================================

def prepare_year(days, year):
    lookup = {
        item["date"]: item
        for item in days
    }

    first_day = date(
        year,
        1,
        1
    )

    last_day = date(
        year,
        12,
        31
    )

    # Move backwards to Sunday.
    start_date = first_day - timedelta(
        days=(first_day.weekday() + 1) % 7
    )

    # Move forwards to Saturday.
    end_date = last_day + timedelta(
        days=(
            6 - (
                (last_day.weekday() + 1) % 7
            )
        )
    )

    weeks = []

    current = start_date

    while current <= end_date:
        week = []

        for row in range(7):
            current_day = current + timedelta(
                days=row
            )

            item = lookup.get(
                current_day.isoformat()
            )

            if item:
                count = int(
                    item.get(
                        "count",
                        0
                    )
                )

                level = int(
                    item.get(
                        "level",
                        0
                    )
                )
            else:
                count = 0
                level = 0

            level = max(
                0,
                min(
                    4,
                    level
                )
            )

            week.append(
                {
                    "date": current_day.isoformat(),
                    "count": count,
                    "level": level
                }
            )

        weeks.append(week)

        current += timedelta(
            days=7
        )

    return weeks


# ============================================================
# XML ESCAPING
# ============================================================

def escape_xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ============================================================
# YEAR TOTAL
# ============================================================

def get_year_total(data, year):
    yearly_totals = data.get(
        "yearly_totals",
        {}
    )

    return int(
        yearly_totals.get(
            str(year),
            0
        )
    )


# ============================================================
# MONTH LABELS
# ============================================================

def get_month_labels(weeks, year):
    labels = []

    for month in range(
        1,
        13
    ):
        first_day = date(
            year,
            month,
            1
        )

        # Find the week containing
        # the first day of the month.
        for index, week in enumerate(weeks):
            week_start = date.fromisoformat(
                week[0]["date"]
            )

            week_end = date.fromisoformat(
                week[-1]["date"]
            )

            if (
                week_start
                <= first_day
                <= week_end
            ):
                labels.append(
                    {
                        "week": index,
                        "month": calendar.month_abbr[month]
                    }
                )

                break

    return labels


# ============================================================
# MAIN SVG GENERATOR
# ============================================================

def generate_svg(data):
    days = data.get(
        "days",
        []
    )

    if not days:
        raise RuntimeError(
            "No contribution data found."
        )

    years = data.get(
        "years",
        []
    )

    if not years:
        years = sorted(
            {
                item["date"][:4]
                for item in days
            }
        )

    years = [
        int(year)
        for year in years
    ]

    years.sort()

    # --------------------------------------------------------
    # Dimensions
    # --------------------------------------------------------

    CELL = 11
    GAP = 3

    LEFT = 45
    RIGHT = 25

    TOP = 55

    YEAR_TITLE_HEIGHT = 25

    CALENDAR_HEIGHT = (
        7 * (CELL + GAP)
    )

    YEAR_SPACING = 42

    LEGEND_HEIGHT = 35

    width = (
        LEFT
        + 53 * (CELL + GAP)
        + RIGHT
    )

    calendar_block_height = (
        YEAR_TITLE_HEIGHT
        + CALENDAR_HEIGHT
        + YEAR_SPACING
    )

    height = (
        TOP
        + len(years) * calendar_block_height
        + LEGEND_HEIGHT
    )

    # --------------------------------------------------------
    # SVG start
    # --------------------------------------------------------

    svg = []

    svg.append(
        f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}"
role="img"
aria-label="GitHub contribution history for {escape_xml(USERNAME)}"
>
'''
    )

    # --------------------------------------------------------
    # Background
    # --------------------------------------------------------

    svg.append(
        f'''
<rect
x="0"
y="0"
width="{width}"
height="{height}"
rx="12"
fill="#0D1117"
/>
'''
    )

    # --------------------------------------------------------
    # Main title
    # --------------------------------------------------------

    all_time_total = int(
        data.get(
            "total_contributions",
            0
        )
    )

    svg.append(
        f'''
<text
x="{LEFT}"
y="28"
fill="#C9D1D9"
font-family="Arial, Helvetica, sans-serif"
font-size="15"
font-weight="600"
>
GitHub Contribution History
</text>
'''
    )

    svg.append(
        f'''
<text
x="{LEFT}"
y="45"
fill="#8B949E"
font-family="Arial, Helvetica, sans-serif"
font-size="10"
>
{all_time_total} contributions across {len(years)} years
</text>
'''
    )

    # --------------------------------------------------------
    # Animation counter
    # --------------------------------------------------------

    animation_index = 0

    # --------------------------------------------------------
    # Render each year
    # --------------------------------------------------------

    for year_index, year in enumerate(years):
        weeks = prepare_year(
            days,
            year
        )

        year_total = get_year_total(
            data,
            year
        )

        block_top = (
            TOP
            + year_index
            * calendar_block_height
        )

        title_y = block_top + 14

        calendar_top = (
            block_top
            + YEAR_TITLE_HEIGHT
        )

        # ----------------------------------------------------
        # Year title
        # ----------------------------------------------------

        svg.append(
            f'''
<text
x="{LEFT}"
y="{title_y}"
fill="#39D353"
font-family="Arial, Helvetica, sans-serif"
font-size="13"
font-weight="600"
>
{year}
</text>
'''
        )

        svg.append(
            f'''
<text
x="{LEFT + 42}"
y="{title_y}"
fill="#8B949E"
font-family="Arial, Helvetica, sans-serif"
font-size="9"
>
{year_total} contributions
</text>
'''
        )

        # ----------------------------------------------------
        # Weekday labels
        # ----------------------------------------------------

        weekday_labels = {
            1: "Mon",
            3: "Wed",
            5: "Fri",
        }

        for row, label in weekday_labels.items():
            y = (
                calendar_top
                + row * (CELL + GAP)
                + 9
            )

            svg.append(
                f'''
<text
x="2"
y="{y}"
fill="#8B949E"
font-family="Arial, Helvetica, sans-serif"
font-size="8"
>
{label}
</text>
'''
            )

        # ----------------------------------------------------
        # Month labels
        # ----------------------------------------------------

        month_labels = get_month_labels(
            weeks,
            year
        )

        for label in month_labels:
            week_index = label["week"]

            x = (
                LEFT
                + week_index
                * (CELL + GAP)
            )

            svg.append(
                f'''
<text
x="{x}"
y="{calendar_top - 7}"
fill="#8B949E"
font-family="Arial, Helvetica, sans-serif"
font-size="8"
>
{escape_xml(label["month"])}
</text>
'''
            )

        # ----------------------------------------------------
        # Contribution cells
        # ----------------------------------------------------

        for week_index, week in enumerate(weeks):
            for row, item in enumerate(week):
                current_date = date.fromisoformat(
                    item["date"]
                )

                # Don't display days outside
                # the selected year.
                if current_date.year != year:
                    level = 0
                    count = 0
                else:
                    level = item["level"]
                    count = item["count"]

                x = (
                    LEFT
                    + week_index
                    * (CELL + GAP)
                )

                y = (
                    calendar_top
                    + row
                    * (CELL + GAP)
                )

                fill = COLORS.get(
                    level,
                    COLORS[0]
                )

                tooltip = (
                    f"{item['date']} - "
                    f"{count} contributions"
                )

                if STATIC:
                    rect = f'''
<rect
x="{x}"
y="{y}"
width="{CELL}"
height="{CELL}"
rx="2"
fill="{fill}"
opacity="1"
>
<title>{escape_xml(tooltip)}</title>
</rect>
'''
                else:
                    delay = (
                        animation_index
                        * 0.008
                    )

                    rect = f'''
<rect
x="{x}"
y="{y}"
width="{CELL}"
height="{CELL}"
rx="2"
fill="{fill}"
opacity="0"
>
<title>{escape_xml(tooltip)}</title>
<animate
attributeName="opacity"
values="0;1"
dur="0.25s"
begin="{delay:.3f}s"
fill="freeze"
/>
</rect>
'''

                svg.append(rect)

                animation_index += 1

    # --------------------------------------------------------
    # Bottom legend
    # --------------------------------------------------------

    legend_y = (
        height - 24
    )

    svg.append(
        f'''
<text
x="{LEFT}"
y="{legend_y + 9}"
fill="#8B949E"
font-family="Arial, Helvetica, sans-serif"
font-size="9"
>
Less
</text>
'''
    )

    legend_x = LEFT + 28

    for level in range(5):
        x = (
            legend_x
            + level
            * (CELL + GAP)
        )

        svg.append(
            f'''
<rect
x="{x}"
y="{legend_y}"
width="{CELL}"
height="{CELL}"
rx="2"
fill="{COLORS[level]}"
/>
'''
        )

    svg.append(
        f'''
<text
x="{legend_x + 5 * (CELL + GAP) + 3}"
y="{legend_y + 9}"
fill="#8B949E"
font-family="Arial, Helvetica, sans-serif"
font-size="9"
>
More
</text>
'''
    )

    # --------------------------------------------------------
    # Close SVG
    # --------------------------------------------------------

    svg.append(
        "</svg>"
    )

    return "\n".join(svg)


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print(
        "Reading all contribution data..."
    )

    data = load_data()

    print(
        "Rendering multi-year contribution history..."
    )

    svg = generate_svg(
        data
    )

    OUTPUT.write_text(
        svg,
        encoding="utf-8"
    )

    print()
    print(
        "Multi-year contribution heatmap created."
    )

    print(
        f"Years rendered: "
        f"{len(data.get('years', []))}"
    )

    print(
        f"Output: {OUTPUT}"
    )

    print(
        f"Static mode: {STATIC}"
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()