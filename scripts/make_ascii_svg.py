from pathlib import Path
import os

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent

INPUT_IMAGE = ROOT / "data" / "prepped_photo.png"
OUTPUT_SVG = ROOT / "avi-ascii.svg"

# Number of ASCII characters
COLUMNS = 100
ROWS = 53

# Bright -> dark
RAMP = " .`:-=+*cs#%@"

# Terminal-style colors
TEXT_COLOR = "#B8C7D9"
BACKGROUND_COLOR = "#0D1117"

FONT_SIZE = 9
CHAR_WIDTH = 7.2
LINE_HEIGHT = 9.5

SVG_WIDTH = int(COLUMNS * CHAR_WIDTH)
SVG_HEIGHT = int(ROWS * LINE_HEIGHT + 20)


def brightness_to_character(value):
    index = int((value / 255) * (len(RAMP) - 1))
    return RAMP[index]


def load_image():
    if not INPUT_IMAGE.exists():
        raise FileNotFoundError(
            f"Prepared image not found: {INPUT_IMAGE}\n"
            "Run prep_photo.py first."
        )

    image = Image.open(INPUT_IMAGE).convert("L")

    # Resize while keeping the desired ASCII proportions
    image = image.resize(
        (COLUMNS, ROWS),
        Image.Resampling.LANCZOS
    )

    return np.array(image)


def escape_xml(text):
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def create_svg():
    pixels = load_image()

    static_mode = os.getenv("STATIC", "0") == "1"

    svg = []

    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        width="{SVG_WIDTH}"
        height="{SVG_HEIGHT}"
        viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">'''
    )

    svg.append(
        f'''
        <rect width="100%" height="100%" rx="12"
              fill="{BACKGROUND_COLOR}"/>
        '''
    )

    # Define one clip path for each row
    for row in range(ROWS):
        y = 16 + row * LINE_HEIGHT

        svg.append(
            f'''
            <clipPath id="rowClip{row}">
                <rect x="0" y="{y - LINE_HEIGHT}"
                      width="{SVG_WIDTH}"
                      height="{LINE_HEIGHT + 4}"/>
            </clipPath>
            '''
        )

    # ---------------------------------------------------------
    # ASCII rows
    # ---------------------------------------------------------
    for row in range(ROWS):

        y = 16 + row * LINE_HEIGHT

        chars = ""

        for col in range(COLUMNS):
            char = brightness_to_character(pixels[row, col])
            chars += char

        chars = escape_xml(chars)

        delay = 0.15 + row * 0.055

        if static_mode:
            animation = ""
        else:
            animation = f'''
            <animate
                attributeName="x"
                from="-{SVG_WIDTH}"
                to="0"
                dur="1.15s"
                begin="{delay:.2f}s"
                fill="freeze"
                calcMode="spline"
                keySplines="0.4 0 0.2 1"
            />
            '''

        svg.append(
            f'''
            <g clip-path="url(#rowClip{row})">
                <text
                    x="0"
                    y="{y}"
                    xml:space="preserve"
                    font-family="JetBrains Mono, Consolas, monospace"
                    font-size="{FONT_SIZE}px"
                    font-weight="500"
                    fill="{TEXT_COLOR}"
                    letter-spacing="0">
                    {chars}
                </text>
            </g>
            '''
        )

    # Subtle terminal cursor
    if not static_mode:
        svg.append(
            f'''
            <rect
                x="0"
                y="{SVG_HEIGHT - 10}"
                width="7"
                height="8"
                fill="{TEXT_COLOR}"
                opacity="0.8">
                <animate
                    attributeName="opacity"
                    values="0.8;0;0.8"
                    dur="0.8s"
                    repeatCount="3"/>
            </rect>
            '''
        )

    svg.append("</svg>")

    OUTPUT_SVG.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"Created: {OUTPUT_SVG}")


if __name__ == "__main__":
    create_svg()