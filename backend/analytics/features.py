"""Image features for distribution shift.

The same function runs on the reference batch and the current batch.
Features are measurements of the fixture pixels, not model outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageStat, UnidentifiedImageError

from assurance.hashing import sha256_file

FEATURE_ORDER = (
    "r_mean",
    "g_mean",
    "b_mean",
    "r_std",
    "g_std",
    "b_std",
    "brightness",
    "contrast",
    "width",
    "height",
    "edge_density",
)


@dataclass(frozen=True)
class ImageFeatures:
    sample_id: str
    file_hash: str
    r_mean: float
    g_mean: float
    b_mean: float
    r_std: float
    g_std: float
    b_std: float
    brightness: float
    contrast: float
    width: float
    height: float
    edge_density: float

    def as_map(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in FEATURE_ORDER}


def extract_features(path: Path) -> ImageFeatures | None:
    """Return features for one readable image, or None when decode fails."""
    try:
        with Image.open(path) as handle:
            handle.load()
            rgb = handle.convert("RGB")
            width, height = rgb.size
            color = ImageStat.Stat(rgb)
            luma = ImageStat.Stat(rgb.convert("L"))
    except (OSError, UnidentifiedImageError, ValueError):
        return None
    means = color.mean
    deviations = color.stddev
    return ImageFeatures(
        sample_id=path.name,
        file_hash=sha256_file(path),
        r_mean=round(float(means[0]), 6),
        g_mean=round(float(means[1]), 6),
        b_mean=round(float(means[2]), 6),
        r_std=round(float(deviations[0]), 6),
        g_std=round(float(deviations[1]), 6),
        b_std=round(float(deviations[2]), 6),
        brightness=round(float(luma.mean[0]), 6),
        contrast=round(float(luma.stddev[0]), 6),
        width=float(width),
        height=float(height),
        edge_density=round(_edge_density(rgb), 6),
    )


def extract_batch(directory: Path) -> tuple[list[ImageFeatures], list[str]]:
    """Read PNG files in name order. Unreadable files are returned as skipped names."""
    if not directory.is_dir():
        return [], []
    features: list[ImageFeatures] = []
    skipped: list[str] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".png":
            continue
        extracted = extract_features(path)
        if extracted is None:
            skipped.append(path.name)
        else:
            features.append(extracted)
    features.sort(key=lambda item: item.sample_id)
    return features, skipped


def _edge_density(image: Image.Image) -> float:
    """Mean absolute adjacent-pixel difference on luminance, scaled to 0–1.

    This is a pixel measurement. Blur lowers it when the image has an edge.
    Flat images stay near zero, which is why the shift fixtures are not flat.
    """
    gray = image.convert("L")
    width, height = gray.size
    if width < 2 or height < 2:
        return 0.0
    reader = gray.get_flattened_data if hasattr(gray, "get_flattened_data") else gray.getdata
    pixels = list(reader())
    total = 0
    count = 0
    for y in range(height):
        row = y * width
        for x in range(width - 1):
            total += abs(pixels[row + x] - pixels[row + x + 1])
            count += 1
    for y in range(height - 1):
        row = y * width
        below = row + width
        for x in range(width):
            total += abs(pixels[row + x] - pixels[below + x])
            count += 1
    return (total / count) / 255.0
