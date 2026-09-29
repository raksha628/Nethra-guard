from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.services.coco_parser import CocoDatasetParser


def make_coco_zip(tmp_path: Path, *, duplicate: bool = False, invalid_bbox: bool = False) -> Path:
    first = BytesIO()
    Image.new("RGB", (20, 10), "red").save(first, format="PNG")
    second = first.getvalue() if duplicate else None
    if second is None:
        second_stream = BytesIO()
        Image.new("RGB", (20, 10), "blue").save(second_stream, format="PNG")
        second = second_stream.getvalue()
    document = {
        "images": [
            {"id": 1, "file_name": "images/one.png", "width": 20, "height": 10},
            {"id": 2, "file_name": "images/two.png", "width": 20, "height": 10},
        ],
        "categories": [{"id": 1, "name": "vehicle"}],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 1, "bbox": [1, 1, 5, 4]},
            {"id": 2, "image_id": 2, "category_id": 1, "bbox": [18, 1, 5, 4] if invalid_bbox else [2, 1, 5, 4]},
        ],
    }
    archive = tmp_path / "dataset.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("annotations/instances.json", json.dumps(document))
        output.writestr("images/one.png", first.getvalue())
        output.writestr("images/two.png", second)
    return archive


def test_clean_coco_profile_has_expected_counts(tmp_path: Path) -> None:
    profile = CocoDatasetParser().parse(make_coco_zip(tmp_path))
    assert profile.image_count == 2
    assert profile.annotation_count == 2
    assert profile.class_frequencies == {"vehicle": 2}
    assert profile.invalid_annotation_count == 0
    assert profile.duplicate_count == 0
    assert profile.sample_coverage == 1.0


def test_duplicate_images_are_detected_by_sha256(tmp_path: Path) -> None:
    profile = CocoDatasetParser().parse(make_coco_zip(tmp_path, duplicate=True))
    assert profile.duplicate_count == 1
    assert profile.images[1].sha256 == profile.images[0].sha256


def test_invalid_bbox_is_reported(tmp_path: Path) -> None:
    profile = CocoDatasetParser().parse(make_coco_zip(tmp_path, invalid_bbox=True))
    assert any(issue.code == "INVALID_BBOX" for issue in profile.issues)


def test_malformed_annotation_is_reported(tmp_path: Path) -> None:
    archive = make_coco_zip(tmp_path)
    rewritten = tmp_path / "malformed.zip"
    with zipfile.ZipFile(archive) as source, zipfile.ZipFile(rewritten, "w") as output:
        document = json.loads(source.read("annotations/instances.json"))
        document["annotations"][0].pop("bbox")
        output.writestr("annotations/instances.json", json.dumps(document))
        output.writestr("images/one.png", source.read("images/one.png"))
        output.writestr("images/two.png", source.read("images/two.png"))
    profile = CocoDatasetParser().parse(rewritten)
    assert any(issue.code == "MALFORMED_ANNOTATION" for issue in profile.issues)


def test_run_creation_findings_and_evidence(client, tmp_path: Path) -> None:
    archive = make_coco_zip(tmp_path, invalid_bbox=True)
    upload = client.post("/api/assets", data={"type": "DATASET"}, files={"file": ("dataset.zip", archive.read_bytes(), "application/zip")})
    assert upload.status_code == 201
    run = client.post("/api/runs", json={"dataset_asset_id": upload.json()["asset_id"], "checks": ["DATA_INTEGRITY"]})
    assert run.status_code == 201
    run_payload = run.json()
    assert run_payload["state"] == "COMPLETED"
    assert run_payload["status"] == "FAIL"
    findings = client.get(f"/api/runs/{run_payload['id']}/findings")
    assert findings.status_code == 200
    assert any(item["title"] == "Invalid Bbox" for item in findings.json())
    evidence = client.get(f"/api/runs/{run_payload['id']}/evidence")
    assert evidence.status_code == 200
    assert evidence.json()[0]["sample_id"]
    assert "C:\\" not in evidence.text


def test_clean_run_returns_pass(client, tmp_path: Path) -> None:
    archive = make_coco_zip(tmp_path)
    upload = client.post("/api/assets", data={"type": "DATASET"}, files={"file": ("clean.zip", archive.read_bytes(), "application/zip")})
    run = client.post("/api/runs", json={"dataset_asset_id": upload.json()["asset_id"], "checks": ["DATA_INTEGRITY"]})
    assert run.json()["status"] == "PASS"
    assert run.json()["findings_count"] == 1
