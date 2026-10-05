"""Image features for distribution shift.

RGB means and standard deviations, luminance brightness and contrast, width,
height, and edge density. Edge density is the share of adjacent pixels whose
luminance jump exceeds a fixed cutoff. Pillow only; no OpenCV or NumPy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from assurance.hashing import sha256_file

EDGE_THRESHOLD = 24.0
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


@dataclass(frozen=True)
class ImageFeatures:
    sample_id: str
    sha256: str
    width: int
    height: int
    red_mean: float
    green_mean: float
    blue_mean: float
    red_std: float
    green_std: float
    blue_std: float
    brightness: float
    contrast: float
    edge_density: float


def feature_names() -> list[str]:
    return [
        "red_mean",
        "green_mean",
        "blue_mean",
        "red_std",
        "green_std",
        "blue_std",
        "brightness",
        "contrast",
        "width",
        "height",
        "edge_density",
    ]


def feature_value(features: ImageFeatures, name: str) -> float:
    return float(getattr(features, name))


def extract_directory(directory: Path) -> tuple[list[ImageFeatures], list[str]]:
    """Return readable features and the names of files that could not be decoded."""
    if not directory.is_dir():
        return [], []
    readable: list[ImageFeatures] = []
    skipped: list[str] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        extracted = extract_image(path)
        if extracted is None:
            skipped.append(path.name)
        else:
            readable.append(extracted)
    return readable, skipped


def extract_image(path: Path) -> ImageFeatures | None:
    try:
        with Image.open(path) as handle:
            rgb = handle.convert("RGB")
            rgb.load()
            width, height = rgb.size
            raw = rgb.tobytes()
            pixels = [tuple(raw[index : index + 3]) for index in range(0, len(raw), 3)]
    except (OSError, UnidentifiedImageError, ValueError):
        return None
    if width <= 0 or height <= 0 or not pixels:
        return None
    red = [pixel[0] for pixel in pixels]
    green = [pixel[1] for pixel in pixels]
    blue = [pixel[2] for pixel in pixels]
    luminance = [_luminance(pixel[0], pixel[1], pixel[2]) for pixel in pixels]
    red_mean = _mean(red)
    green_mean = _mean(green)
    blue_mean = _mean(blue)
    brightness = _mean(luminance)
    return ImageFeatures(
        sample_id=path.name,
        sha256=sha256_file(path),
        width=width,
        height=height,
        red_mean=red_mean,
        green_mean=green_mean,
        blue_mean=blue_mean,
        red_std=_std(red, red_mean),
        green_std=_std(green, green_mean),
        blue_std=_std(blue, blue_mean),
        brightness=brightness,
        contrast=_std(luminance, brightness),
        edge_density=_edge_density(luminance, width, height),
    )


def _luminance(red: int, green: int, blue: int) -> float:
    return 0.299 * red + 0.587 * green + 0.114 * blue


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float], average: float) -> float:
    return math.sqrt(sum((value - average) ** 2 for value in values) / len(values))


def _edge_density(luminance: list[float], width: int, height: int) -> float:
    strong = 0
    total = 0
    for y in range(height):
        row = y * width
        for x in range(width - 1):
            total += 1
            if abs(luminance[row + x] - luminance[row + x + 1]) >= EDGE_THRESHOLD:
                strong += 1
        if y + 1 < height:
            below = row + width
            for x in range(width):
                total += 1
                if abs(luminance[row + x] - luminance[below + x]) >= EDGE_THRESHOLD:
                    strong += 1
    if total == 0:
        return 0.0
    return strong / total
