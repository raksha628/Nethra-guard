"""Write Person 2 shift batches.

Reference images have an interior edge so blur and contrast change a measured
feature. Transformed copies live beside the reference. This script does not
rewrite fixtures/clean, fixtures/anomaly, or the expected handoff JSON.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent / "shift"
REFERENCE = ROOT / "reference"
FOLDERS = ("brightness", "blur", "contrast", "color_cast", "resolution")


def main() -> None:
    REFERENCE.mkdir(parents=True, exist_ok=True)
    for name in FOLDERS:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    for index in range(1, 5):
        image = _reference_image(index)
        image.save(REFERENCE / f"img_{index:02d}.png")
        _brightness(image).save(ROOT / "brightness" / f"img_{index:02d}.png")
        _blur(image).save(ROOT / "blur" / f"img_{index:02d}.png")
        _contrast(image).save(ROOT / "contrast" / f"img_{index:02d}.png")
        _color_cast(image).save(ROOT / "color_cast" / f"img_{index:02d}.png")
        _resolution(image).save(ROOT / "resolution" / f"img_{index:02d}.png")


def _reference_image(index: int) -> Image.Image:
    image = Image.new("RGB", (64, 48), (28, 36, 44))
    pixels = image.load()
    left = 10 + index
    top = 8
    right = 46
    bottom = 36
    for y in range(top, bottom):
        for x in range(left, right):
            pixels[x, y] = (200, 150, 30)
    for y in range(4, 44):
        pixels[6, y] = (245, 245, 245)
        pixels[7, y] = (245, 245, 245)
    return image


def _brightness(image: Image.Image) -> Image.Image:
    return image.point(lambda value: max(0, min(255, value + 90)))


def _blur(image: Image.Image) -> Image.Image:
    return image.filter(ImageFilter.GaussianBlur(radius=2.4))


def _contrast(image: Image.Image) -> Image.Image:
    return ImageEnhance.Contrast(image).enhance(2.6)


def _color_cast(image: Image.Image) -> Image.Image:
    red, green, blue = image.split()
    red = red.point(lambda value: min(255, int(value * 2)))
    return Image.merge("RGB", (red, green, blue))


def _resolution(image: Image.Image) -> Image.Image:
    return image.resize((20, 36), Image.Resampling.NEAREST)


if __name__ == "__main__":
    main()
