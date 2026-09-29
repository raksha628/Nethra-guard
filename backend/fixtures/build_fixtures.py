"""Create the tiny offline COCO fixtures and refresh handoff JSON.

Run from the backend directory:

    python fixtures/build_fixtures.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "fixtures"
CLEAN_IMAGES = FIXTURES / "clean" / "images"
ANOMALY_IMAGES = FIXTURES / "anomaly" / "images"
MODELS = FIXTURES / "models"

BASELINE_BYTES = b"NETRA-GUARD baseline model stand-in v1\n"
ALTERED_BYTES = b"NETRA-GUARD altered model stand-in v1\n"

COLORS = {
    "img_001.png": (20, 80, 140),
    "img_002.png": (180, 60, 40),
    "img_003.png": (40, 140, 80),
    "img_004.png": (200, 180, 40),
}


def main() -> None:
    _reset()
    for name, color in COLORS.items():
        _write_png(CLEAN_IMAGES / name, color)
    _write_json(FIXTURES / "clean" / "annotations.json", _clean_annotations())

    for name in ("img_001.png", "img_002.png", "img_004.png"):
        shutil.copyfile(CLEAN_IMAGES / name, ANOMALY_IMAGES / name)
    shutil.copyfile(CLEAN_IMAGES / "img_001.png", ANOMALY_IMAGES / "img_001_dup.png")
    _write_json(FIXTURES / "anomaly" / "annotations.json", _anomaly_annotations())

    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / "baseline_model.bin").write_bytes(BASELINE_BYTES)
    (MODELS / "altered_model.bin").write_bytes(ALTERED_BYTES)

    from assurance.data_integrity import fingerprint_dataset
    from assurance.hashing import sha256_file

    manifest = {
        "altered_model_file": "models/altered_model.bin",
        "annotation_format": "coco",
        "anomaly_dataset": "anomaly",
        "clean_dataset": "clean",
        "dataset_hash": fingerprint_dataset(FIXTURES / "clean"),
        "model_file": "models/baseline_model.bin",
        "model_hash": sha256_file(MODELS / "baseline_model.bin"),
    }
    _write_json(FIXTURES / "baseline_manifest.json", manifest)

    from assurance.scenarios import export_handoff

    export_handoff(FIXTURES)


def _reset() -> None:
    for relative in ("clean", "anomaly", "models"):
        path = FIXTURES / relative
        if path.exists():
            shutil.rmtree(path)
    for name in (
        "baseline_manifest.json",
        "expected_clean.json",
        "expected_anomaly.json",
        "normalized_detections.json",
    ):
        generated = FIXTURES / name
        if generated.exists():
            generated.unlink()
    CLEAN_IMAGES.mkdir(parents=True, exist_ok=True)
    ANOMALY_IMAGES.mkdir(parents=True, exist_ok=True)


def _write_png(path: Path, color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (100, 80), color)
    image.save(path, format="PNG")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _categories() -> list[dict[str, object]]:
    return [{"id": 1, "name": "vehicle"}, {"id": 2, "name": "person"}]


def _image(image_id: int, file_name: str) -> dict[str, object]:
    return {"file_name": file_name, "height": 80, "id": image_id, "width": 100}


def _box(annotation_id: int, image_id: int, category_id: int, bbox: list[int]) -> dict[str, object]:
    return {
        "bbox": bbox,
        "category_id": category_id,
        "id": annotation_id,
        "image_id": image_id,
        "iscrowd": 0,
    }


def _clean_annotations() -> dict[str, object]:
    return {
        "annotations": [
            _box(1, 1, 1, [10, 10, 30, 20]),
            _box(2, 2, 2, [12, 8, 20, 40]),
            _box(3, 3, 1, [15, 10, 25, 25]),
            _box(4, 4, 2, [8, 10, 18, 30]),
        ],
        "categories": _categories(),
        "images": [
            _image(1, "img_001.png"),
            _image(2, "img_002.png"),
            _image(3, "img_003.png"),
            _image(4, "img_004.png"),
        ],
        "info": {"description": "NETRA-Guard clean COCO fixture"},
    }


def _anomaly_annotations() -> dict[str, object]:
    return {
        "annotations": [
            _box(1, 1, 1, [10, 10, 30, 20]),
            _box(2, 2, 2, [10, 10, 20, 30]),
            _box(3, 4, 1, [70, 50, 40, 40]),
            _box(4, 5, 99, [10, 10, 20, 20]),
        ],
        "categories": _categories(),
        "images": [
            _image(1, "img_001.png"),
            _image(2, "img_001_dup.png"),
            _image(3, "img_003.png"),
            _image(4, "img_002.png"),
            _image(5, "img_004.png"),
        ],
        "info": {"description": "NETRA-Guard controlled dataset anomaly fixture"},
    }


if __name__ == "__main__":
    main()
