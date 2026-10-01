from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "info-card.svg"

WIDTH = 490
HEIGHT = 410

BG = "#0D1117"
BORDER = "#30363D"
PRIMARY = "#00C6FF"
TEXT = "#E6EDF3"
MUTED = "#8B949E"
ACCENT = "#69F0A0"


ROWS = [
    ("role", "AI & Data Science Student"),
    ("focus", "Full-Stack Development"),
    ("ai", "AI / ML / Generative AI"),
    ("data", "Data Science & Analytics"),
    ("stack", "Python • C++ • Java • JS • SQL"),
    ("web", "React • Next.js • Node.js • FastAPI"),
    ("llm", "LLMs • RAG • LangChain • LangGraph"),
    ("cloud", "Docker • AWS • GitHub Actions"),
    ("research", "Fairness-aware Machine Learning"),
]


def escape(text):
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def create_card():

    static_mode = os.getenv("STATIC", "0") == "1"

    svg = [
        f'''
        <svg xmlns="http://www.w3.org/2000/svg"
             width="{WIDTH}"
             height="{HEIGHT}"
             viewBox="0 0 {WIDTH} {HEIGHT}">
        ''',

        f'''
        <rect
            x="1"
            y="1"
            width="{WIDTH - 2}"
            height="{HEIGHT - 2}"
            rx="14"
            fill="{BG}"
            stroke="{BORDER}"
            stroke-width="2"/>
        ''',

        # Header
        f'''
        <text
            x="24"
            y="36"
            font-family="JetBrains Mono, Consolas, monospace"
            font-size="18"
            font-weight="700"
            fill="{PRIMARY}">
            sara@github
        </text>

        <text
            x="24"
            y="61"
            font-family="JetBrains Mono, Consolas, monospace"
            font-size="13"
            fill="{MUTED}">
            ─────────────────────────────────────
        </text>

        <text
            x="24"
            y="88"
            font-family="JetBrains Mono, Consolas, monospace"
            font-size="13"
            fill="{ACCENT}">
            $ whoami
        </text>
        '''
    ]

    start_y = 120

    for index, (key, value) in enumerate(ROWS):

        y = start_y + index * 29

        delay = 0.4 + index * 0.15

        if static_mode:
            opacity = "1"
            animation = ""
        else:
            opacity = "0"

            animation = f'''
            <animate
                attributeName="opacity"
                from="0"
                to="1"
                dur="0.5s"
                begin="{delay:.2f}s"
                fill="freeze"/>
            '''

        svg.append(
            f'''
            <g opacity="{opacity}">
                <text
                    x="24"
                    y="{y}"
                    font-family="JetBrains Mono, Consolas, monospace"
                    font-size="12"
                    font-weight="600"
                    fill="{PRIMARY}">
                    {escape(key)}
                </text>

                <text
                    x="105"
                    y="{y}"
                    font-family="JetBrains Mono, Consolas, monospace"
                    font-size="12"
                    fill="{TEXT}">
                    {escape(value)}
                </text>

                {animation}
            </g>
            '''
        )

    svg.append(
        f'''
        <text
            x="24"
            y="{HEIGHT - 28}"
            font-family="JetBrains Mono, Consolas, monospace"
            font-size="12"
            fill="{MUTED}">
            status: <tspan fill="{ACCENT}">building • learning • innovating</tspan>
        </text>

        </svg>
        '''
    )

    OUTPUT.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    create_card()