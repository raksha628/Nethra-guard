from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.services.hash_service import calculate_sha256


@dataclass(frozen=True)
class EvaluationSample:
    sample_id: str
    preprocessing: str = "RGB decode; fixed 64x64 nearest-neighbor resize"


@dataclass(frozen=True)
class NormalizedPrediction:
    sample_id: str
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]
    detection_count: int = 1


@dataclass(frozen=True)
class ModelMetadata:
    adapter: str
    format: str
    framework: str
    deterministic_fallback: bool
    preprocessing: str
    details: dict[str, Any]


class ModelAdapter(Protocol):
    def load(self, model_path: Path) -> None: ...
    def validate(self, model_path: Path) -> list[str]: ...
    def run_inference(self, samples: list[EvaluationSample]) -> list[NormalizedPrediction]: ...
    def metadata(self) -> ModelMetadata: ...


FROZEN_EVALUATION_SET = (
    EvaluationSample("fixed-sample-001"),
    EvaluationSample("fixed-sample-002"),
    EvaluationSample("fixed-sample-003"),
)


class DeterministicFallbackAdapter:
    def __init__(self) -> None:
        self.model_path: Path | None = None
        self.model_hash = ""

    def load(self, model_path: Path) -> None:
        self.model_path = model_path
        self.model_hash = calculate_sha256(model_path)

    def validate(self, model_path: Path) -> list[str]:
        if not model_path.is_file():
            return ["model file is not available"]
        if model_path.stat().st_size == 0:
            return ["model file is empty"]
        return []

    def run_inference(self, samples: list[EvaluationSample]) -> list[NormalizedPrediction]:
        if not self.model_hash:
            raise RuntimeError("model must be loaded before inference")
        predictions: list[NormalizedPrediction] = []
        for sample in samples:
            digest = hashlib.sha256(f"{self.model_hash}:{sample.sample_id}:{sample.preprocessing}".encode("utf-8")).digest()
            class_name = f"class-{digest[0] % 3}"
            confidence = round(0.5 + (digest[1] / 255) * 0.49, 4)
            x = round((digest[2] / 255) * 0.35, 4)
            y = round((digest[3] / 255) * 0.35, 4)
            width = round(0.25 + (digest[4] / 255) * 0.35, 4)
            height = round(0.25 + (digest[5] / 255) * 0.35, 4)
            predictions.append(NormalizedPrediction(sample.sample_id, class_name, confidence, (x, y, width, height)))
        return predictions

    def metadata(self) -> ModelMetadata:
        return ModelMetadata("deterministic-fallback", "unknown", "none", True, FROZEN_EVALUATION_SET[0].preprocessing, {"reason": "No compatible runtime was selected for the uploaded artifact"})


def select_adapter(model_path: Path) -> ModelAdapter:
    # User-provided model artifacts are untrusted. Formats backed by pickle or
    # executable graphs must not be deserialized or run in the API process.
    # The hash-seeded fallback is explicitly labelled prototype evidence.
    return DeterministicFallbackAdapter()


def normalize_predictions(predictions: list[NormalizedPrediction]) -> list[dict[str, Any]]:
    return [{"sample_id": item.sample_id, "class": item.class_name, "confidence": item.confidence, "bbox": list(item.bbox), "detection_count": item.detection_count} for item in predictions]


def box_iou(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> float:
    first_x2, first_y2 = first[0] + first[2], first[1] + first[3]
    second_x2, second_y2 = second[0] + second[2], second[1] + second[3]
    intersection = max(0.0, min(first_x2, second_x2) - max(first[0], second[0])) * max(0.0, min(first_y2, second_y2) - max(first[1], second[1]))
    union = first[2] * first[3] + second[2] * second[3] - intersection
    return round(intersection / union, 6) if union else 0.0


def compare_predictions(baseline: list[NormalizedPrediction], current: list[NormalizedPrediction], confidence_delta_threshold: float = 0.15, iou_threshold: float = 0.5) -> list[dict[str, Any]]:
    baseline_by_sample = {item.sample_id: item for item in baseline}
    current_by_sample = {item.sample_id: item for item in current}
    changes: list[dict[str, Any]] = []
    for sample_id in sorted(set(baseline_by_sample) | set(current_by_sample)):
        before, after = baseline_by_sample.get(sample_id), current_by_sample.get(sample_id)
        if before is None or after is None:
            changes.append({"sample_id": sample_id, "type": "detection_count_change", "baseline": before.detection_count if before else 0, "current": after.detection_count if after else 0})
            continue
        iou = box_iou(before.bbox, after.bbox)
        confidence_delta = round(after.confidence - before.confidence, 6)
        if before.class_name != after.class_name:
            changes.append({"sample_id": sample_id, "type": "class_change", "baseline": before.class_name, "current": after.class_name})
        if abs(confidence_delta) > confidence_delta_threshold:
            changes.append({"sample_id": sample_id, "type": "confidence_delta", "baseline": before.confidence, "current": after.confidence, "delta": confidence_delta, "threshold": confidence_delta_threshold})
        if iou < iou_threshold:
            changes.append({"sample_id": sample_id, "type": "bounding_box_change", "baseline": list(before.bbox), "current": list(after.bbox), "iou": iou, "threshold": iou_threshold})
    return changes
