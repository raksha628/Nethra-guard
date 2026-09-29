from __future__ import annotations

import copy
import json
from pathlib import Path

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import LedgerEntry
from app.services.canonical import canonical_hash, canonical_json
from app.services.ledger import GENESIS_HASH, verify_ledger_entries
from tests.test_data_integrity import make_coco_zip


def upload_dataset(client, tmp_path: Path) -> dict:
    archive = make_coco_zip(tmp_path)
    response = client.post("/api/assets", data={"type": "DATASET"}, files={"file": ("dataset.zip", archive.read_bytes(), "application/zip")})
    assert response.status_code == 201
    return response.json()


def create_run(client, dataset_id: str) -> dict:
    response = client.post("/api/runs", json={"dataset_asset_id": dataset_id, "checks": ["DATA_INTEGRITY"], "configuration": {"scenario": "NONE", "preprocessing": "fixed-v1"}})
    assert response.status_code == 201
    return response.json()


def test_canonical_configuration_hash_is_order_independent() -> None:
    first = {"checks": ["DATA_INTEGRITY"], "configuration": {"scenario": "NONE", "threshold": 1}}
    second = {"configuration": {"threshold": 1, "scenario": "NONE"}, "checks": ["DATA_INTEGRITY"]}
    assert canonical_json(first) == canonical_json(second)
    assert canonical_hash(first) == canonical_hash(second)


def test_ledger_is_created_and_tamper_copy_is_detected(client, tmp_path: Path) -> None:
    dataset = upload_dataset(client, tmp_path)
    create_run(client, dataset["asset_id"])
    ledger = client.get("/api/ledger").json()
    assert ledger["verification"]["status"] == "VALID"
    with SessionLocal() as session:
        entry = session.scalar(select(LedgerEntry).order_by(LedgerEntry.sequence))
        copied = [{"sequence": entry.sequence, "previous_hash": entry.previous_hash, "current_hash": entry.current_hash, "payload_json": entry.payload_json}]
    tampered = copy.deepcopy(copied)
    payload = json.loads(tampered[0]["payload_json"])
    payload["run_id"] = "tampered-run"
    tampered[0]["payload_json"] = canonical_json(payload)
    assert verify_ledger_entries(copied)["status"] == "VALID"
    invalid = verify_ledger_entries(tampered)
    assert invalid["status"] == "INVALID"
    assert invalid["first_broken_sequence"] == 1


def test_report_is_canonical_and_hashed(client, tmp_path: Path) -> None:
    dataset = upload_dataset(client, tmp_path)
    run = create_run(client, dataset["asset_id"])
    first = client.get(f"/api/runs/{run['id']}/report").json()
    second = client.get(f"/api/runs/{run['id']}/report").json()
    assert first["report_hash"] == second["report_hash"]
    assert first["report"]["configuration_hash"]
    assert first["report"]["provenance"]["verification"]["status"] == "VALID"
    assert "MODEL_INTEGRITY" in first["report"]["skipped_checks"]


def test_comparator_returns_compatibility_and_deltas(client, tmp_path: Path) -> None:
    dataset = upload_dataset(client, tmp_path)
    baseline = create_run(client, dataset["asset_id"])
    current = create_run(client, dataset["asset_id"])
    comparison = client.get(f"/api/runs/{current['id']}/compare", params={"baseline_run_id": baseline["id"]})
    assert comparison.status_code == 200
    payload = comparison.json()
    assert payload["compatibility"]["is_compatible"] is True
    assert isinstance(payload["metric_deltas"], list)
    assert payload["baseline_run_id"] == baseline["id"]
    assert payload["current_run_id"] == current["id"]
