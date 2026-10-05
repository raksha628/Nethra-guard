import json
import shutil
from pathlib import Path

from PIL import Image

from assurance.data_integrity import check_dataset
from assurance.hashing import sha256_file
from assurance.schemas import ModuleStatus, Severity

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _titles(result):
    return [finding.title for finding in result.findings]


def test_clean_fixture_passes_with_known_counts():
    result = check_dataset(FIXTURES / "clean")
    assert result.status == ModuleStatus.PASS
    assert result.findings == []
    assert result.metrics["annotation_format"] == "coco"
    assert result.metrics["declared_image_count"] == 4
    assert result.metrics["readable_image_count"] == 4
    assert result.metrics["annotation_count"] == 4
    assert result.metrics["class_counts"] == {"person": 2, "vehicle": 2}
    assert not any(finding.severity == Severity.CRITICAL for finding in result.findings)


def test_anomaly_fixture_reports_duplicate_missing_file_and_bad_box():
    result = check_dataset(FIXTURES / "anomaly")
    titles = _titles(result)
    assert result.status == ModuleStatus.FAIL
    assert "Exact duplicate images" in titles
    assert "Missing image file" in titles
    assert "Bounding box outside image bounds" in titles
    assert "Invalid class id" in titles
    duplicate = next(finding for finding in result.findings if finding.title == "Exact duplicate images")
    assert {ref.sample_id for ref in duplicate.evidence_refs} == {"img_001.png", "img_001_dup.png"}
    assert duplicate.evidence_refs[0].file_hash == sha256_file(FIXTURES / "anomaly" / "images" / "img_001.png")


def test_duplicates_alone_are_a_warning():
    destination = Path(__file__).parent / "_tmp_duplicate"
    shutil.rmtree(destination, ignore_errors=True)
    shutil.copytree(FIXTURES / "clean", destination)
    shutil.copyfile(destination / "images" / "img_001.png", destination / "images" / "img_005.png")
    document = json.loads((destination / "annotations.json").read_text(encoding="utf-8"))
    document["images"].append({"file_name": "img_005.png", "height": 80, "id": 5, "width": 100})
    document["annotations"].append(
        {"bbox": [10, 10, 20, 20], "category_id": 1, "id": 5, "image_id": 5, "iscrowd": 0}
    )
    (destination / "annotations.json").write_text(json.dumps(document), encoding="utf-8")
    try:
        result = check_dataset(destination)
    finally:
        shutil.rmtree(destination)
    assert result.status == ModuleStatus.WARNING
    assert "Exact duplicate images" in _titles(result)
    assert not any(finding.severity == Severity.CRITICAL for finding in result.findings)


def test_malformed_json_fails():
    root = Path(__file__).parent / "_tmp_malformed"
    shutil.rmtree(root, ignore_errors=True)
    (root / "images").mkdir(parents=True)
    (root / "annotations.json").write_text("{", encoding="utf-8")
    try:
        result = check_dataset(root)
    finally:
        shutil.rmtree(root)
    assert result.status == ModuleStatus.FAIL
    assert _titles(result) == ["Malformed annotations"]


def test_corrupt_image_fails():
    root = Path(__file__).parent / "_tmp_corrupt"
    shutil.rmtree(root, ignore_errors=True)
    (root / "images").mkdir(parents=True)
    (root / "images" / "bad.png").write_bytes(b"not-an-image")
    document = {
        "annotations": [{"bbox": [1, 1, 2, 2], "category_id": 1, "id": 1, "image_id": 1}],
        "categories": [{"id": 1, "name": "vehicle"}],
        "images": [{"file_name": "bad.png", "height": 10, "id": 1, "width": 10}],
    }
    (root / "annotations.json").write_text(json.dumps(document), encoding="utf-8")
    try:
        result = check_dataset(root)
    finally:
        shutil.rmtree(root)
    assert result.status == ModuleStatus.FAIL
    assert "Corrupt or unreadable image" in _titles(result)


def test_annotation_path_cannot_escape_the_dataset(tmp_path: Path):
    images = tmp_path / "images"
    images.mkdir()
    secret = tmp_path / "secret.png"
    Image.new("RGB", (100, 80), (1, 2, 3)).save(secret, format="PNG")
    secret_hash = sha256_file(secret)
    document = {
        "annotations": [],
        "categories": [{"id": 1, "name": "vehicle"}],
        "images": [{"file_name": "../secret.png", "height": 80, "id": 1, "width": 100}],
    }
    (tmp_path / "annotations.json").write_text(json.dumps(document), encoding="utf-8")
    result = check_dataset(tmp_path)
    assert result.status == ModuleStatus.FAIL
    assert "Annotation path is not allowed" in _titles(result)
    assert secret_hash not in json.dumps(result.model_dump(mode="json"))
