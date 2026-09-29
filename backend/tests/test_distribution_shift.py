from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.services.distribution_shift import extract_features, run_distribution_shift
from tests.test_data_integrity import make_coco_zip


def make_gradient_zip(tmp_path: Path) -> Path:
    image = Image.new("RGB", (20, 10))
    pixels = image.load()
    for x in range(20):
        for y in range(10):
            pixels[x, y] = (x * 12, y * 20, 80)
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    document = {"images": [{"id": 1, "file_name": "image.png", "width": 20, "height": 10}, {"id": 2, "file_name": "image2.png", "width": 20, "height": 10}], "categories": [], "annotations": []}
    archive = tmp_path / "gradient.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("annotations.json", json.dumps(document))
        output.writestr("image.png", image_bytes.getvalue())
        output.writestr("image2.png", image_bytes.getvalue())
    return archive


def test_feature_extraction_is_deterministic(tmp_path: Path) -> None:
    source = make_coco_zip(tmp_path)
    first = extract_features(source)
    second = extract_features(source)
    assert first == second
    assert first[0].brightness > 0
    assert first[0].rgb_mean > 0


def test_identical_reference_current_has_no_shift(tmp_path: Path) -> None:
    source = make_coco_zip(tmp_path)
    summary, finding = run_distribution_shift(source, source, {"thresholds": {"shiftThreshold": 1.0}}, "reference", "current")
    assert summary["status"] == "PASS"
    assert finding is None


def test_brightness_scenario_is_detectable_and_reproducible(tmp_path: Path) -> None:
    source = make_coco_zip(tmp_path)
    first, finding = run_distribution_shift(source, source, {"scenario": "BRIGHTNESS_SHIFT", "thresholds": {"shiftThreshold": 0.5}}, "reference", "current")
    second, _ = run_distribution_shift(source, source, {"scenario": "BRIGHTNESS_SHIFT", "thresholds": {"shiftThreshold": 0.5}}, "reference", "current")
    assert first == second
    assert first["status"] == "WARNING"
    assert finding is not None
    assert finding.method.startswith("Standardized mean difference")


def test_contrast_scenario_changes_feature_on_gradient(tmp_path: Path) -> None:
    source = make_gradient_zip(tmp_path)
    summary, _ = run_distribution_shift(source, source, {"scenario": "CONTRAST_SHIFT", "thresholds": {"shiftThreshold": 0.1}}, "reference", "current")
    assert summary["status"] == "WARNING"
    assert summary["affected_feature"] in {"contrast", "brightness", "rgb_mean"}


def test_insufficient_samples_is_not_run(tmp_path: Path) -> None:
    source = make_coco_zip(tmp_path)
    summary, finding = run_distribution_shift(source, source, {"thresholds": {"shiftMinSamples": 3}}, "reference", "current")
    assert summary["status"] == "NOT_RUN"
    assert finding is None


def test_distribution_run_persists_finding_and_evidence(client, tmp_path: Path) -> None:
    source = make_coco_zip(tmp_path)
    upload = client.post("/api/assets", data={"type": "DATASET"}, files={"file": ("shift.zip", source.read_bytes(), "application/zip")})
    assert upload.status_code == 201
    run = client.post("/api/runs", json={"dataset_asset_id": upload.json()["asset_id"], "checks": ["DISTRIBUTION_SHIFT"], "configuration": {"scenario": "BRIGHTNESS_SHIFT", "thresholds": {"shiftThreshold": 0.5}}})
    assert run.status_code == 201
    payload = run.json()
    assert payload["summary"]["checks"]["DISTRIBUTION_SHIFT"] == "WARNING"
    findings = client.get(f"/api/runs/{payload['id']}/findings").json()
    assert findings[0]["category"] == "DISTRIBUTION_SHIFT"
    evidence = client.get(f"/api/runs/{payload['id']}/evidence").json()
    assert evidence[0]["details"]["reference_sample_count"] == 2
