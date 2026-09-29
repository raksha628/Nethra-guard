from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.services.file_storage import safe_filename, validate_extension
from app.schemas.common import AssetType
from app.services.canonical import canonical_hash


def test_health_endpoint(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["offline"] is True


def test_database_and_demo_workspace_initialize(client) -> None:
    response = client.get("/api/demo/workspace")
    assert response.status_code == 200
    assert response.json()["name"] == "default-ws-01"
    assert (settings.workspace_root / "uploads").exists()


def test_allowed_file_validation_and_safe_name() -> None:
    name = safe_filename("vehicle data.zip", AssetType.DATASET)
    assert name.startswith("dataset_")
    assert ".." not in name
    assert validate_extension("weights.ONNX", AssetType.MODEL) == ".onnx"


def test_rejected_extension(client) -> None:
    response = client.post("/api/assets", data={"type": "MODEL"}, files={"file": ("script.exe", b"bad", "application/octet-stream")})
    assert response.status_code == 415


def test_size_validation(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "max_upload_size_bytes", 3)
    response = client.post("/api/assets", data={"type": "DATASET"}, files={"file": ("data.json", b"four", "application/json")})
    assert response.status_code == 413


def test_path_traversal_is_not_persisted(client) -> None:
    response = client.post("/api/assets", data={"type": "DATASET"}, files={"file": ("../../escape.json", b"{}", "application/json")})
    assert response.status_code == 400
    assert not (Path(settings.workspace_root).parent / "escape.json").exists()


def test_unknown_workspace_does_not_fall_back_to_demo(client) -> None:
    response = client.post("/api/assets", data={"type": "DATASET", "workspace_id": "missing-workspace"}, files={"file": ("dataset.json", b"{}", "application/json")})
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


def test_asset_registration_returns_hash_and_metadata(client) -> None:
    content = b'{"images": []}'
    response = client.post("/api/assets", data={"type": "DATASET"}, files={"file": ("dataset.json", content, "application/json")})
    assert response.status_code == 201
    payload = response.json()
    assert payload["original_name"] == "dataset.json"
    assert payload["size"] == len(content)
    assert len(payload["sha256"]) == 64
    assert payload["registration_metadata"]["source"] == "local_upload"


def test_full_demo_assurance_workflow(client) -> None:
    demo = client.get("/api/demo/workspace").json()
    dataset_id = demo["dataset"]["asset_id"]
    model_id = demo["model"]["asset_id"]
    checks = ["DATA_INTEGRITY", "MODEL_INTEGRITY", "DISTRIBUTION_SHIFT", "COMPARATOR"]

    baseline = client.post("/api/runs", json={
        "workspace_id": demo["workspace_id"], "dataset_asset_id": dataset_id, "model_asset_id": model_id,
        "checks": checks, "configuration": {"scenario": "NONE", "thresholds": {"shiftThreshold": 0.5}},
    }).json()
    assert baseline["state"] == "COMPLETED"

    anomaly = client.post("/api/runs", json={
        "workspace_id": demo["workspace_id"], "dataset_asset_id": dataset_id, "model_asset_id": model_id,
        "checks": checks, "configuration": {"scenario": "DATA_ANOMALY", "thresholds": {"shiftThreshold": 0.5}},
    }).json()
    anomaly_findings = client.get(f"/api/runs/{anomaly['id']}/findings").json()
    assert any(item["category"] == "DATA_INTEGRITY" for item in anomaly_findings)
    assert client.get(f"/api/runs/{anomaly['id']}/evidence").json()
    comparison = client.get(f"/api/runs/{anomaly['id']}/compare", params={"baseline_run_id": baseline["id"]}).json()
    assert comparison["compatibility"]["is_compatible"]
    assert any(item["type"] == "NEW" for item in comparison["finding_changes"])

    changed_model = client.post("/api/runs", json={
        "workspace_id": demo["workspace_id"], "dataset_asset_id": dataset_id, "model_asset_id": model_id,
        "checks": checks, "configuration": {"scenario": "MODEL_MISMATCH", "thresholds": {"shiftThreshold": 0.5}},
    }).json()
    assert changed_model["summary"]["model"]["current_sha256"] != changed_model["summary"]["model"]["baseline_sha256"]
    model_findings = client.get(f"/api/runs/{changed_model['id']}/findings").json()
    assert any("registered baseline" in item["description"] for item in model_findings)

    shifted = client.post("/api/runs", json={
        "workspace_id": demo["workspace_id"], "dataset_asset_id": dataset_id, "model_asset_id": model_id,
        "checks": checks, "configuration": {"scenario": "BRIGHTNESS_SHIFT", "thresholds": {"shiftThreshold": 0.1}},
    }).json()
    assert shifted["summary"]["distribution_shift"]["status"] == "WARNING"
    assert shifted["summary"]["distribution_shift"]["threshold"] == 0.1
    assert client.get(f"/api/runs/{shifted['id']}/evidence").json()

    ledger = client.get("/api/ledger").json()
    assert ledger["verification"]["status"] == "VALID"
    assert client.post("/api/ledger/verify").json()["status"] == "VALID"
    report = client.get(f"/api/runs/{shifted['id']}/report", params={"baseline_run_id": baseline["id"]}).json()
    assert report["report_hash"] == canonical_hash(report["report"])
    assert report["report"]["configuration_hash"]
    assert report["report"]["provenance"]["verification"]["status"] == "VALID"
