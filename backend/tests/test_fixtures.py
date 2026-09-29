import json
from pathlib import Path

from assurance.data_integrity import fingerprint_dataset
from assurance.hashing import sha256_file

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_clean_and_anomaly_fixtures_load_offline():
    clean = FIXTURES / "clean"
    anomaly = FIXTURES / "anomaly"
    annotations = json.loads((clean / "annotations.json").read_text(encoding="utf-8"))
    anomaly_doc = json.loads((anomaly / "annotations.json").read_text(encoding="utf-8"))
    manifest = json.loads((FIXTURES / "baseline_manifest.json").read_text(encoding="utf-8"))

    assert annotations["images"]
    assert len(list((clean / "images").glob("*.png"))) == 4
    names = {image["file_name"] for image in anomaly_doc["images"]}
    assert "img_003.png" in names
    assert not (anomaly / "images" / "img_003.png").exists()
    assert (anomaly / "images" / "img_001_dup.png").exists()
    assert (FIXTURES / "models" / "baseline_model.bin").is_file()
    assert (FIXTURES / "models" / "altered_model.bin").is_file()
    assert manifest["annotation_format"] == "coco"
    assert manifest["dataset_hash"] == fingerprint_dataset(clean)
    assert manifest["model_hash"] == sha256_file(FIXTURES / "models" / "baseline_model.bin")
    assert sha256_file(FIXTURES / "models" / "altered_model.bin") != manifest["model_hash"]
