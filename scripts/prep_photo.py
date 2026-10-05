from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


ROOT = Path(__file__).resolve().parent.parent

DEFAULT_INPUT = ROOT / "source-photo.jpeg"
DEFAULT_OUTPUT = ROOT / "data" / "prepped_photo.png"


def prepare_photo(input_path: Path, output_path: Path):
    if not input_path.exists():
        print(f"ERROR: Photo not found: {input_path}")
        print()
        print("Put your photo in the repository root and name it:")
        print("source-photo.jpg")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {input_path}")

    image = Image.open(input_path).convert("RGBA")

    # ---------------------------------------------------------
    # Remove background if rembg is available
    # ---------------------------------------------------------
    if REMBG_AVAILABLE:
        print("Removing background with rembg...")
        try:
            image = remove(image)
        except Exception as exc:
            print(f"Background removal failed: {exc}")
            print("Continuing without background removal.")
    else:
        print("rembg is not available.")
        print("Continuing without background removal.")

    # ---------------------------------------------------------
    # Composite on white background
    # ---------------------------------------------------------
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)

    rgb = np.array(white.convert("RGB"))

    # ---------------------------------------------------------
    # Convert to grayscale
    # ---------------------------------------------------------
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # ---------------------------------------------------------
    # Improve local contrast using CLAHE
    # ---------------------------------------------------------
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # ---------------------------------------------------------
    # Light smoothing to reduce image noise
    # ---------------------------------------------------------
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------
    result = Image.fromarray(enhanced)
    result.save(output_path)

    print()
    print("Photo preparation complete.")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    prepare_photo(input_file, output_file)