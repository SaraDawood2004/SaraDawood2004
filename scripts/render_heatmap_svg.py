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


# GitHub-style colors
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
# PREPARE 53-WEEK CALENDAR
# ============================================================

def prepare_calendar(data):

    days = data.get(
        "days",
        []
    )

    if not days:

        raise RuntimeError(
            "No contribution days found."
        )

    lookup = {
        item["date"]: item
        for item in days
    }

    # --------------------------------------------------------
    # GitHub's calendar is approximately 53 weeks.
    # --------------------------------------------------------

    end_date = max(
        date.fromisoformat(
            item["date"]
        )
        for item in days
    )

    start_date = end_date - timedelta(
        days=364
    )

    # Align start to Sunday.
    start_date -= timedelta(
        days=(start_date.weekday() + 1) % 7
    )

    # Align end to Saturday.
    end_date += timedelta(
        days=(6 - ((end_date.weekday() + 1) % 7))
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

                level = int(
                    item.get(
                        "level",
                        0
                    )
                )

            else:

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
                    "date":
                        current_day.isoformat(),

                    "level":
                        level
                }
            )

        weeks.append(
            week
        )

        current += timedelta(
            days=7
        )

    return weeks


# ============================================================
# SVG ESCAPING
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
# MONTH LABELS
# ============================================================

def get_month_labels(weeks):

    labels = []

    previous_month = None

    for index, week in enumerate(weeks):

        first_day = date.fromisoformat(
            week[0]["date"]
        )

        # Check all days in the week.
        for item in week:

            current_day = date.fromisoformat(
                item["date"]
            )

            month = current_day.month

            if (
                month != previous_month
                and current_day.day <= 7
            ):

                labels.append(
                    {
                        "week":
                            index,

                        "month":
                            calendar.month_abbr[
                                month
                            ]
                    }
                )

                previous_month = month

                break

    return labels


# ============================================================
# SVG GENERATION
# ============================================================

def generate_svg(data):

    weeks = prepare_calendar(
        data
    )

    stats = data.get(
        "stats",
        {}
    )

    total = data.get(
        "total_contributions",
        stats.get("total", 0)
    )

    current_streak = stats.get(
        "current_streak",
        0
    )

    longest_streak = stats.get(
        "longest_streak",
        0
    )

    # --------------------------------------------------------
    # Dimensions
    # --------------------------------------------------------

    CELL = 11
    GAP = 4

    LEFT = 35
    TOP = 32
    RIGHT = 20
    BOTTOM = 45

    WIDTH = (
        LEFT
        + len(weeks) * (CELL + GAP)
        + RIGHT
    )

    HEIGHT = (
        TOP
        + 7 * (CELL + GAP)
        + BOTTOM
    )

    # --------------------------------------------------------
    # SVG
    # --------------------------------------------------------

    svg = []

    svg.append(
        f'''<svg
        xmlns="http://www.w3.org/2000/svg"
        width="{WIDTH}"
        height="{HEIGHT}"
        viewBox="0 0 {WIDTH} {HEIGHT}"
        role="img"
        aria-label="{escape_xml(total)} GitHub contributions in the last year"
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
            width="{WIDTH}"
            height="{HEIGHT}"
            rx="10"
            fill="#0D1117"
        />
        '''
    )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    svg.append(
        f'''
        <text
            x="{LEFT}"
            y="18"
            fill="#C9D1D9"
            font-family="Arial, Helvetica, sans-serif"
            font-size="12"
            font-weight="600"
        >
            {escape_xml(total)} contributions in the last year
        </text>
        '''
    )

    # --------------------------------------------------------
    # Weekday labels
    # --------------------------------------------------------

    weekday_labels = {
        1: "Mon",
        3: "Wed",
        5: "Fri",
    }

    for row, label in weekday_labels.items():

        y = (
            TOP
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
                font-size="9"
            >
                {label}
            </text>
            '''
        )

    # --------------------------------------------------------
    # Month labels
    # --------------------------------------------------------

    month_labels = get_month_labels(
        weeks
    )

    for label in month_labels:

        week_index = label["week"]

        x = (
            LEFT
            + week_index * (CELL + GAP)
        )

        svg.append(
            f'''
            <text
                x="{x}"
                y="{TOP - 8}"
                fill="#8B949E"
                font-family="Arial, Helvetica, sans-serif"
                font-size="9"
            >
                {escape_xml(label["month"])}
            </text>
            '''
        )

    # --------------------------------------------------------
    # Contribution squares
    # --------------------------------------------------------

    animation_index = 0

    for week_index, week in enumerate(weeks):

        for row, item in enumerate(week):

            level = item["level"]

            x = (
                LEFT
                + week_index * (CELL + GAP)
            )

            y = (
                TOP
                + row * (CELL + GAP)
            )

            fill = COLORS.get(
                level,
                COLORS[0]
            )

            tooltip = (
                f"{item['date']} — "
                f"activity level {level}"
            )

            if STATIC:

                animation = ""

            else:

                delay = (
                    animation_index * 0.012
                )

                animation = f'''
                <animate
                    attributeName="opacity"
                    values="0;1"
                    dur="0.35s"
                    begin="{delay:.3f}s"
                    fill="freeze"
                />
                '''

            svg.append(
                f'''
                <g>
                    <title>
                        {escape_xml(tooltip)}
                    </title>

                    <rect
                        x="{x}"
                        y="{y}"
                        width="{CELL}"
                        height="{CELL}"
                        rx="2"
                        fill="{fill}"
                        opacity="0"
                    >
                        {animation}
                    </rect>
                </g>
                '''
            )

            animation_index += 1

    # --------------------------------------------------------
    # Footer statistics
    # --------------------------------------------------------

    footer_y = (
        TOP
        + 7 * (CELL + GAP)
        + 22
    )

    svg.append(
        f'''
        <text
            x="{LEFT}"
            y="{footer_y}"
            fill="#8B949E"
            font-family="Arial, Helvetica, sans-serif"
            font-size="9"
        >
            Current streak: {current_streak}
        </text>
        '''
    )

    svg.append(
        f'''
        <text
            x="{LEFT + 105}"
            y="{footer_y}"
            fill="#8B949E"
            font-family="Arial, Helvetica, sans-serif"
            font-size="9"
        >
            Longest streak: {longest_streak}
        </text>
        '''
    )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    legend_x = WIDTH - 165
    legend_y = footer_y - 8

    svg.append(
        f'''
        <text
            x="{legend_x - 25}"
            y="{legend_y + 9}"
            fill="#8B949E"
            font-family="Arial, Helvetica, sans-serif"
            font-size="9"
        >
            Less
        </text>
        '''
    )

    for level in range(5):

        x = (
            legend_x
            + level * (CELL + GAP)
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
            x="{legend_x + 5 * (CELL + GAP) + 2}"
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

    return "\n".join(
        svg
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Reading contribution data..."
    )

    data = load_data()

    print(
        "Rendering contribution heatmap..."
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
        "Contribution heatmap created."
    )

    print(
        f"Output: {OUTPUT}"
    )

    print(
        f"Static mode: {STATIC}"
    )

    print()


if __name__ == "__main__":
    main()