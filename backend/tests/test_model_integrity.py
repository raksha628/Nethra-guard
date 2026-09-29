from __future__ import annotations

from pathlib import Path

from app.services.model_adapter import DeterministicFallbackAdapter, EvaluationSample, compare_predictions, normalize_predictions


def upload_model(client, name: str, content: bytes):
    response = client.post("/api/assets", data={"type": "MODEL"}, files={"file": (name, content, "application/octet-stream")})
    assert response.status_code == 201
    return response.json()


def test_model_sha256_and_baseline_registration(client) -> None:
    model = upload_model(client, "model.pt", b"baseline-model-v1")
    baseline = client.post("/api/workspace/baseline-model", json={"asset_id": model["asset_id"]})
    assert baseline.status_code == 200
    assert baseline.json()["sha256"] == model["sha256"]


def test_unchanged_model_passes_model_integrity(client) -> None:
    model = upload_model(client, "model.pt", b"baseline-model-v1")
    assert client.post("/api/workspace/baseline-model", json={"asset_id": model["asset_id"]}).status_code == 200
    run = client.post("/api/runs", json={"model_asset_id": model["asset_id"], "checks": ["MODEL_INTEGRITY"]})
    assert run.status_code == 201
    assert run.json()["status"] == "PASS"
    assert run.json()["summary"]["checks"]["DATA_INTEGRITY"] == "NOT_RUN"
    assert run.json()["summary"]["checks"]["MODEL_INTEGRITY"] == "PASS"


def test_changed_model_creates_non_malicious_hash_finding_and_evidence(client) -> None:
    baseline = upload_model(client, "baseline.pt", b"baseline-model-v1")
    current = upload_model(client, "current.pt", b"current-model-v2")
    assert client.post("/api/workspace/baseline-model", json={"asset_id": baseline["asset_id"]}).status_code == 200
    run = client.post("/api/runs", json={"model_asset_id": current["asset_id"], "checks": ["MODEL_INTEGRITY"]})
    assert run.status_code == 201
    assert run.json()["status"] == "WARNING"
    findings = client.get(f"/api/runs/{run.json()['id']}/findings").json()
    mismatch = next(item for item in findings if item["title"] == "Model artifact differs from registered baseline.")
    assert "does not prove malicious tampering" in mismatch["remediation"]
    evidence = client.get(f"/api/runs/{run.json()['id']}/evidence").json()
    assert any(item["finding_id"] == mismatch["id"] for item in evidence)


def test_controlled_model_scenario_changes_hash(client) -> None:
    model = upload_model(client, "model.pt", b"baseline-model-v1")
    assert client.post("/api/workspace/baseline-model", json={"asset_id": model["asset_id"]}).status_code == 200
    run = client.post("/api/runs", json={"model_asset_id": model["asset_id"], "checks": ["MODEL_INTEGRITY"], "configuration": {"scenario": "MODEL_MISMATCH"}})
    assert run.json()["summary"]["model"]["controlled_scenario"] is True
    assert run.json()["summary"]["model"]["hash_match"] is False


def test_fallback_adapter_and_prediction_comparison() -> None:
    adapter = DeterministicFallbackAdapter()
    path = Path(__file__).parent / "fixtures" / "fallback-model.pt"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"adapter-test-model")
    try:
        assert adapter.validate(path) == []
        adapter.load(path)
        samples = [EvaluationSample("sample-1")]
        predictions = adapter.run_inference(samples)
        assert predictions[0].sample_id == "sample-1"
        assert normalize_predictions(predictions)[0]["detection_count"] == 1
        changed = DeterministicFallbackAdapter()
        path.write_bytes(b"adapter-test-model-changed")
        changed.load(path)
        assert compare_predictions(predictions, changed.run_inference(samples))
    finally:
        path.unlink(missing_ok=True)
