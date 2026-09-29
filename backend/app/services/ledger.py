from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset, Finding, LedgerEntry, Run
from app.services.canonical import canonical_hash, canonical_json

GENESIS_HASH = "0" * 64
ACTOR_LABEL = "Analyst Workstation (Local)"


def _entry_payload(sequence: int, run: Run, previous_hash: str, dataset_hash: str, model_hash: str, summary_hash: str) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "run_id": run.id,
        "timestamp": (run.completed_at or datetime.now(timezone.utc)).isoformat(),
        "actor_label": ACTOR_LABEL,
        "dataset_hash": dataset_hash,
        "model_hash": model_hash,
        "config_hash": run.configuration_hash or "",
        "summary_hash": summary_hash,
        "previous_hash": previous_hash,
    }


def append_run_entry(db: Session, run: Run) -> LedgerEntry:
    latest = db.scalar(select(LedgerEntry).order_by(LedgerEntry.sequence.desc()))
    sequence = (latest.sequence + 1) if latest else 1
    previous_hash = latest.current_hash if latest else GENESIS_HASH
    dataset = db.get(Asset, run.current_dataset_asset_id or run.dataset_asset_id) if (run.current_dataset_asset_id or run.dataset_asset_id) else None
    model = db.get(Asset, run.model_asset_id) if run.model_asset_id else None
    summary = json.loads(run.summary_json or "{}")
    payload = _entry_payload(sequence, run, previous_hash, dataset.sha256 if dataset else "", model.sha256 if model else "", canonical_hash(summary))
    current_hash = canonical_hash({"entry": payload, "previous_hash": previous_hash})
    entry = LedgerEntry(
        id=f"ledger_{uuid4().hex}", sequence=sequence, run_id=run.id, timestamp=datetime.fromisoformat(payload["timestamp"]), actor_label=ACTOR_LABEL,
        dataset_hash=payload["dataset_hash"], model_hash=payload["model_hash"], config_hash=payload["config_hash"], summary_hash=payload["summary_hash"],
        previous_hash=previous_hash, current_hash=current_hash, entry_hash=current_hash, payload_json=canonical_json(payload),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_ledger(db: Session) -> dict[str, Any]:
    entries = db.scalars(select(LedgerEntry).order_by(LedgerEntry.sequence)).all()
    return verify_ledger_entries([
        {"sequence": item.sequence, "previous_hash": item.previous_hash, "current_hash": item.current_hash, "payload_json": item.payload_json}
        for item in entries
    ])


def verify_ledger_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    expected_previous = GENESIS_HASH
    for expected_sequence, entry in enumerate(entries, start=1):
        if entry["sequence"] != expected_sequence:
            return {"status": "INVALID", "first_broken_sequence": entry["sequence"], "reason": "Ledger sequence is not contiguous."}
        if entry["previous_hash"] != expected_previous:
            return {"status": "INVALID", "first_broken_sequence": entry["sequence"], "reason": "Previous hash does not match the verified prior entry."}
        payload = json.loads(entry["payload_json"])
        recomputed = canonical_hash({"entry": payload, "previous_hash": entry["previous_hash"]})
        if recomputed != entry["current_hash"]:
            return {"status": "INVALID", "first_broken_sequence": entry["sequence"], "reason": "Current hash does not match canonical ledger content."}
        expected_previous = recomputed
    return {"status": "VALID", "entries": len(entries), "first_broken_sequence": None, "reason": None}
