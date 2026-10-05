"""Inference adapters.

The demo ships a deterministic fallback for the .bin stand-in. It does not
execute model weights. No ONNX or YOLO artifact is bundled, so those formats
are not claimed as supported.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from .hashing import canonical_json, sha256_file, sha256_text
from .model_integrity import ModelAdapter, UnsafeModelError
from .schemas import Detection, ImageDetections

SIMULATED_LIMITATION = (
    "Detections are produced by a deterministic fallback adapter and are labeled simulated. "
    "They are not outputs of the model weights. Do not use them as evidence of model behavior."
)
UNSUPPORTED_LIMITATION = (
    "No tested inference adapter supports this file. "
    "The deterministic fallback runs only for the demo .bin stand-in. "
    "ONNX and YOLO weights are not bundled and are not claimed as supported."
)

# Fixed boxes for the bundled demo image ids. Values are xyxy pixels.
FIXED_DETECTIONS: dict[str, list[Detection]] = {
    "img_001.png": [Detection(class_id=1, confidence=0.91, bbox_xyxy=[10, 10, 40, 30])],
    "img_002.png": [Detection(class_id=2, confidence=0.83, bbox_xyxy=[12, 8, 32, 48])],
    "img_003.png": [Detection(class_id=1, confidence=0.77, bbox_xyxy=[15, 10, 40, 35])],
    "img_004.png": [Detection(class_id=2, confidence=0.88, bbox_xyxy=[8, 10, 26, 40])],
    "img_001_dup.png": [Detection(class_id=2, confidence=0.64, bbox_xyxy=[10, 10, 30, 40])],
}


class InferenceResult(BaseModel):
    adapter: str
    simulated: bool
    executed: bool
    model_hash: str | None = None
    input_set_hash: str | None = None
    preprocessing: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    config_hash: str | None = None
    timing_ms: float | None = None
    limitations: str
    images: list[ImageDetections] = Field(default_factory=list)
    skipped_images: list[str] = Field(default_factory=list)
    images_meta: list[dict[str, Any]] = Field(default_factory=list)


class DeterministicAdapter(ModelAdapter):
    name = "deterministic_fallback"
    simulated = True

    def supports(self, model_path: Path) -> bool:
        return model_path.suffix.lower() == ".bin"

    def predict(
        self,
        model_path: Path,
        image_paths: list[Path],
        config: dict[str, Any],
    ) -> InferenceResult:
        if model_path.suffix.lower() in {".pkl", ".pickle"}:
            raise UnsafeModelError("Refusing to load pickle weights")
        started = time.perf_counter()
        images: list[ImageDetections] = []
        meta: list[dict[str, Any]] = []
        skipped: list[str] = []
        for path in image_paths:
            try:
                with Image.open(path) as handle:
                    handle.load()
                    width, height = handle.size
            except (OSError, UnidentifiedImageError, ValueError):
                skipped.append(path.name)
                continue
            digest = sha256_file(path)
            meta.append(
                {"image_id": path.name, "width": width, "height": height, "sha256": digest}
            )
            images.append(
                ImageDetections(
                    image_id=path.name,
                    detections=[item.model_copy() for item in FIXED_DETECTIONS.get(path.name, [])],
                )
            )
        images.sort(key=lambda item: item.image_id)
        meta.sort(key=lambda item: item["image_id"])
        skipped.sort()
        preprocessing = {
            "resize": None,
            "color_order": "RGB",
            "normalization": "none",
            "note": "The fallback records decoded size and returns fixed boxes. It does not run a detector.",
        }
        stored_config = {
            **{key: value for key, value in config.items() if key != "preprocessing"},
            "adapter": self.name,
            "simulated": True,
            "preprocessing": preprocessing,
        }
        input_rows = [{"image_id": row["image_id"], "sha256": row["sha256"]} for row in meta]
        elapsed_ms = (time.perf_counter() - started) * 1000
        return InferenceResult(
            adapter=self.name,
            simulated=True,
            executed=True,
            model_hash=sha256_file(model_path),
            input_set_hash=sha256_text(canonical_json({"images": input_rows})),
            preprocessing=preprocessing,
            config=stored_config,
            config_hash=sha256_text(canonical_json(stored_config)),
            timing_ms=elapsed_ms,
            limitations=SIMULATED_LIMITATION,
            images=images,
            skipped_images=skipped,
            images_meta=meta,
        )


def run_inference(
    model_path: Path,
    image_paths: list[Path],
    *,
    allowed_root: Path,
    config: dict[str, Any] | None = None,
) -> InferenceResult:
    root = allowed_root.resolve()
    try:
        resolved = model_path.resolve()
        resolved.relative_to(root)
    except ValueError:
        raise UnsafeModelError("Model path is outside the workspace root") from None

    adapter = DeterministicAdapter()
    if resolved.suffix.lower() in {".pkl", ".pickle"}:
        raise UnsafeModelError("Refusing to load pickle weights")
    if not adapter.supports(resolved):
        return InferenceResult(
            adapter="none",
            simulated=False,
            executed=False,
            limitations=UNSUPPORTED_LIMITATION,
            config=config or {},
        )
    return adapter.predict(resolved, image_paths, config or {})


def normalized_detections(result: InferenceResult) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in result.images]
