from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Asset, Evidence, Finding, LedgerEntry, Run, Workspace
from app.services.canonical import canonical_hash
from app.services.ledger import verify_ledger


def _tool_versions() -> dict[str, str]:
    import sys

    import fastapi
    import sqlalchemy
    from PIL import __version__ as pillow_version

    return {
        "python": sys.version.split()[0],
        "fastapi": fastapi.__version__,
        "sqlalchemy": sqlalchemy.__version__,
        "pillow": pillow_version,
    }


def build_report(db: Session, run: Run, comparator: dict[str, Any] | None = None) -> tuple[dict[str, Any], str]:
    workspace = db.get(Workspace, run.workspace_id)
    asset_ids = {
        asset_id for asset_id in (
            run.dataset_asset_id,
            run.reference_dataset_asset_id,
            run.current_dataset_asset_id,
            run.model_asset_id,
        ) if asset_id
    }
    assets = [asset for asset in db.scalars(select(Asset).where(Asset.id.in_(asset_ids))).all()] if asset_ids else []
    findings = db.scalars(select(Finding).where(Finding.run_id == run.id)).all()
    evidence = db.scalars(select(Evidence).join(Finding, Evidence.finding_id == Finding.id).where(Finding.run_id == run.id)).all()
    ledger = db.scalar(select(LedgerEntry).where(LedgerEntry.run_id == run.id))
    summary = json.loads(run.summary_json or "{}")
    configuration = json.loads(run.configuration_json or "{}")
    executed = configuration.get("checks", [])
    report = {
        "report_metadata": {"project": settings.app_name, "version": settings.version, "generated_at": (run.completed_at or run.created_at).isoformat(), "offline": True, "tools": _tool_versions()},
        "run_id": run.id,
        "run_state": run.state,
        "timestamp": run.created_at.isoformat(),
        "workspace": {"id": workspace.id if workspace else run.workspace_id, "name": workspace.name if workspace else "unknown"},
        "assets": [{"id": asset.id, "type": asset.type, "name": asset.original_name, "size_bytes": asset.size_bytes, "sha256": asset.sha256, "format": asset.format} for asset in assets],
        "dataset": summary.get("profile", {}),
        "model": summary.get("model", {}),
        "configuration": configuration.get("configuration", {}),
        "configuration_hash": run.configuration_hash,
        "executed_checks": executed,
        "skipped_checks": [name for name in ("DATA_INTEGRITY", "MODEL_INTEGRITY", "DISTRIBUTION_SHIFT", "COMPARATOR") if name not in executed],
        "not_run_checks": [name for name, status in (summary.get("checks") or {}).items() if status == "NOT_RUN"],
        "status": summary.get("status", "NOT_RUN"),
        "findings": [{"id": item.id, "category": item.category, "severity": item.severity, "status": item.status, "title": item.title, "description": item.description, "method": item.method, "observed_value": item.observed_value, "threshold": item.threshold, "confidence_note": item.confidence_note, "limitations": item.limitations, "evidence_refs": json.loads(item.details_json or "{}").get("evidence_refs", [])} for item in findings],
        "evidence": [{"id": item.id, "finding_id": item.finding_id, "sample_id": item.sample_id, "metric": item.metric, "expected_value": item.expected_value, "observed_value": item.observed_value, "details": json.loads(item.details_json or "{}")} for item in evidence],
        "distribution_shift": summary.get("distribution_shift", {"status": "NOT_RUN"}),
        "comparator": comparator or summary.get("comparator"),
        "provenance": {"ledger_entry": {"sequence": ledger.sequence, "current_hash": ledger.current_hash, "previous_hash": ledger.previous_hash, "timestamp": ledger.timestamp.isoformat() if ledger.timestamp else None} if ledger else None, "verification": verify_ledger(db)},
        "limitations": ["Offline local prototype.", "Disabled checks are represented as NOT_RUN.", "Deterministic findings do not establish malicious intent or production model performance."],
        "error": summary.get("error"),
    }
    return report, canonical_hash(report)
