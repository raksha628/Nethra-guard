import json
from pathlib import Path

import pytest

from assurance.inference import DeterministicAdapter, normalized_detections, run_inference
from assurance.model_integrity import UnsafeModelError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
MODELS = FIXTURES / "models"


def _clean_images() -> list[Path]:
    return sorted((FIXTURES / "clean" / "images").glob("*.png"))


def _without_timing(result) -> dict:
    payload = result.model_dump(mode="json")
    payload.pop("timing_ms", None)
    return payload


def test_fallback_is_deterministic_and_labeled_simulated():
    first = run_inference(
        MODELS / "baseline_model.bin",
        _clean_images(),
        allowed_root=MODELS,
        config={"scenario": "NONE"},
    )
    second = run_inference(
        MODELS / "baseline_model.bin",
        _clean_images(),
        allowed_root=MODELS,
        config={"scenario": "NONE"},
    )
    assert first.simulated is True
    assert first.executed is True
    assert first.limitations.startswith("Detections are produced by a deterministic fallback")
    assert _without_timing(first) == _without_timing(second)
    expected = json.loads((FIXTURES / "normalized_detections.json").read_text(encoding="utf-8"))
    assert normalized_detections(first) == expected
    assert [item["image_id"] for item in expected] == [
        "img_001.png",
        "img_002.png",
        "img_003.png",
        "img_004.png",
    ]


def test_pickle_and_untested_formats_are_not_executed(tmp_path: Path):
    pickle_path = tmp_path / "weights.pkl"
    pickle_path.write_bytes(b"pickle-bytes")
    with pytest.raises(UnsafeModelError):
        run_inference(pickle_path, [], allowed_root=tmp_path)
    with pytest.raises(UnsafeModelError):
        DeterministicAdapter().predict(pickle_path, [], {})

    onnx_path = tmp_path / "model.onnx"
    onnx_path.write_bytes(b"not-a-real-model")
    refused = run_inference(onnx_path, [], allowed_root=tmp_path)
    assert refused.executed is False
    assert refused.simulated is False
    assert refused.images == []
