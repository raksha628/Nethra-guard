"""Write Person 2 shift fixtures.

These images are separate from fixtures/clean and fixtures/anomaly.
The reference batch has an interior checker so blur and contrast are measurable.
Flat color images would leave those transforms at zero.

Run from the backend directory:

    python fixtures/build_shift_fixtures.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SHIFT = ROOT / "fixtures" / "shift"
SIZE = (96, 72)
CELL = 8
TARGET_BRIGHTNESS = 112

# Same geometry, different channel steps. Luminance stays in one PSI bin while
# the red, green, and blue means stay spread across bins.
SPECS = (
    ("img_s01.png", (70, 150, 90), (80, 20, 20)),
    ("img_s02.png", (140, 60, 100), (20, 50, 20)),
    ("img_s03.png", (100, 130, 50), (40, 30, 40)),
    ("img_s04.png", (50, 100, 160), (50, 25, 25)),
)


def main() -> None:
    _reset()
    reference = SHIFT / "reference"
    for name, background, delta in SPECS:
        painted = _checker(background, delta)
        _write(reference / name, _tune_brightness(painted))
    _write_batch("brightness", _brightness)
    _write_batch("blur", _blur)
    _write_batch("contrast", _contrast)
    _write_batch("color_cast", _color_cast)
    _write_batch("resolution", _resolution)


def _reset() -> None:
    """Remove generated batch directories only. Do not touch Person 1 fixtures."""
    if SHIFT.exists():
        for child in SHIFT.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
    SHIFT.mkdir(parents=True, exist_ok=True)


def _write_batch(name: str, transform) -> None:
    source = SHIFT / "reference"
    target = SHIFT / name
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*.png")):
        with Image.open(path) as handle:
            image = transform(handle.convert("RGB"))
        _write(target / path.name, image)


def _checker(background: tuple[int, int, int], delta: tuple[int, int, int]) -> Image.Image:
    foreground = tuple(min(255, channel + shift) for channel, shift in zip(background, delta))
    image = Image.new("RGB", SIZE, background)
    pixels = image.load()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            if ((x // CELL) + (y // CELL)) % 2 == 0:
                pixels[x, y] = foreground
    return image


def _tune_brightness(image: Image.Image) -> Image.Image:
    measured = ImageStat.Stat(image.convert("L")).mean[0]
    delta = int(round(TARGET_BRIGHTNESS - measured))
    return _add(image, delta, delta, delta)


def _brightness(image: Image.Image) -> Image.Image:
    return _add(image, 30, 30, 30)


def _blur(image: Image.Image) -> Image.Image:
    return image.filter(ImageFilter.GaussianBlur(radius=3.0))


def _contrast(image: Image.Image) -> Image.Image:
    return ImageEnhance.Contrast(image).enhance(1.7)


def _color_cast(image: Image.Image) -> Image.Image:
    return _add(image, 40, 0, 0)


def _add(image: Image.Image, red_add: int, green_add: int, blue_add: int) -> Image.Image:
    red, green, blue = image.split()
    red = red.point(lambda value, shift=red_add: min(255, max(0, int(value) + shift)))
    green = green.point(lambda value, shift=green_add: min(255, max(0, int(value) + shift)))
    blue = blue.point(lambda value, shift=blue_add: min(255, max(0, int(value) + shift)))
    return Image.merge("RGB", (red, green, blue))


def _resolution(image: Image.Image) -> Image.Image:
    return image.resize((SIZE[0] // 2, SIZE[1] // 2), Image.Resampling.NEAREST)


def _write(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


if __name__ == "__main__":
    main()
