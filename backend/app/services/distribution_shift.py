from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageStat

from app.config import settings
from app.services.coco_parser import CocoDatasetParser


@dataclass(frozen=True)
class ImageFeatures:
    sample_id: str
    brightness: float
    contrast: float
    rgb_mean: float
    width: float
    height: float


@dataclass(frozen=True)
class ShiftEvidence:
    sample_id: str
    metric: str
    expected_value: str | None
    observed_value: str | None
    reference: str | None
    details: dict[str, Any]


@dataclass(frozen=True)
class ShiftFinding:
    category: str
    severity: str
    status: str
    title: str
    description: str
    method: str
    observed_value: str
    threshold: str
    confidence_note: str
    limitations: str
    remediation: str
    affected_sample: str | None
    evidence: list[ShiftEvidence]


def _scenario_image(image: Image.Image, scenario: str) -> Image.Image:
    if scenario in {"DISTRIBUTION_SHIFT", "BRIGHTNESS_SHIFT"}:
        return ImageEnhance.Brightness(image).enhance(0.55)
    if scenario == "CONTRAST_SHIFT":
        return ImageEnhance.Contrast(image).enhance(2.2)
    if scenario == "BLUR_SHIFT":
        return image.filter(ImageFilter.GaussianBlur(radius=3.0))
    if scenario == "RESIZE_SHIFT":
        smaller = image.resize((max(1, image.width // 2), max(1, image.height // 2)), Image.Resampling.BILINEAR)
        return smaller.resize(image.size, Image.Resampling.BILINEAR)
    if scenario == "COLOR_CAST_SHIFT":
        red, green, blue = image.split()
        red = red.point(lambda value: min(255, int(value * 1.35)))
        return Image.merge("RGB", (red, green, blue))
    return image


def extract_features(source: Path, scenario: str = "NONE") -> list[ImageFeatures]:
    profile = CocoDatasetParser().parse(source)
    features: list[ImageFeatures] = []
    for record in profile.images:
        if not record.data or not record.readable:
            continue
        with Image.open(BytesIO(record.data)).convert("RGB") as image:
            transformed = _scenario_image(image, scenario)
            stats = ImageStat.Stat(transformed)
            luminance = transformed.convert("L")
            luminance_stats = ImageStat.Stat(luminance)
            features.append(ImageFeatures(
                sample_id=record.image_id,
                brightness=round(sum(luminance_stats.mean), 6),
                contrast=round(luminance_stats.stddev[0], 6),
                rgb_mean=round(sum(stats.mean) / 3, 6),
                width=float(transformed.width),
                height=float(transformed.height),
            ))
    return features


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: list[float], mean: float) -> float:
    return (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5 if values else 0.0


def _standardized_mean_difference(reference: list[float], current: list[float]) -> float:
    reference_mean = _mean(reference)
    current_mean = _mean(current)
    pooled = (((_stddev(reference, reference_mean) ** 2) + (_stddev(current, current_mean) ** 2)) / 2) ** 0.5
    return round(abs(current_mean - reference_mean) / max(pooled, 1e-9), 6)


def _stats(values: list[float]) -> dict[str, float]:
    mean = _mean(values)
    return {"mean": round(mean, 6), "stddev": round(_stddev(values, mean), 6), "min": round(min(values), 6), "max": round(max(values), 6)} if values else {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}


def run_distribution_shift(reference_path: Path, current_path: Path, configuration: dict[str, Any], reference_name: str, current_name: str) -> tuple[dict[str, Any], ShiftFinding | None]:
    reference_features = extract_features(reference_path, "NONE")
    scenario = str(configuration.get("scenario", "NONE"))
    current_features = extract_features(current_path, scenario)
    thresholds = configuration.get("thresholds", {})
    minimum = int(thresholds.get("shiftMinSamples", settings.shift_min_samples))
    threshold = float(thresholds.get("shiftThreshold", configuration.get("shiftThreshold", settings.shift_threshold)))
    enabled_features = tuple(thresholds.get("shiftFeatures", settings.shift_features))
    if len(reference_features) < minimum or len(current_features) < minimum:
        return {
            "status": "NOT_RUN", "method": "Standardized mean difference", "threshold": threshold,
            "reference_sample_count": len(reference_features), "current_sample_count": len(current_features),
            "scenario": scenario, "enabled_features": list(enabled_features),
            "limitations": f"At least {minimum} readable samples are required in each batch.",
        }, None

    supported_features = {"brightness", "contrast", "rgb_mean", "width", "height"}
    reference_by_feature = {feature: [getattr(item, feature) for item in reference_features] for feature in enabled_features if feature in supported_features}
    current_by_feature = {feature: [getattr(item, feature) for item in current_features] for feature in enabled_features if feature in supported_features}
    if not reference_by_feature:
        return {
            "status": "NOT_RUN", "method": "Standardized mean difference", "threshold": threshold,
            "reference_sample_count": len(reference_features), "current_sample_count": len(current_features),
            "scenario": scenario, "enabled_features": list(enabled_features),
            "limitations": "No supported image-statistics features were selected.",
        }, None
    scores = {feature: _standardized_mean_difference(reference_by_feature[feature], current_by_feature[feature]) for feature in reference_by_feature}
    affected_feature, observed = max(scores.items(), key=lambda item: item[1])
    shifted = observed > threshold
    status = "WARNING" if shifted else "PASS"
    summary = {
        "status": status, "method": "Standardized mean difference", "metric": "standardized_mean_difference",
        "affected_feature": affected_feature, "observed_value": observed, "threshold": threshold,
        "reference_sample_count": len(reference_features), "current_sample_count": len(current_features),
        "reference_dataset": reference_name, "current_dataset": current_name, "scenario": scenario,
        "enabled_features": list(enabled_features), "feature_scores": scores,
        "reference_statistics": {feature: _stats(values) for feature, values in reference_by_feature.items()},
        "current_statistics": {feature: _stats(values) for feature, values in current_by_feature.items()},
        "limitations": "This deterministic image-statistics comparison does not establish cause, impact, or malicious activity.",
    }
    if not shifted:
        return summary, None
    evidence = ShiftEvidence("distribution-batch", affected_feature, str(threshold), str(observed), f"reference:{reference_name};current:{current_name}", summary)
    finding = ShiftFinding(
        category="DISTRIBUTION_SHIFT", severity="WARNING", status="OPEN", title="Distribution shift detected",
        description=f"The {affected_feature} feature differs between the reference and current image batches.",
        method="Standardized mean difference over deterministic image-level features",
        observed_value=str(observed), threshold=str(threshold),
        confidence_note="Deterministic statistical result; this is not an ML confidence score.",
        limitations=summary["limitations"], remediation="Review the affected batch and confirm whether the observed shift is expected.",
        affected_sample=None, evidence=[evidence],
    )
    return summary, finding
