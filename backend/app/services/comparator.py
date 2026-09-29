from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Finding, Run


def _finding_identity(finding: Finding) -> tuple[str, str, str]:
    return (finding.category, finding.title, finding.affected_sample or "")


def compare_runs(db: Session, baseline: Run, current: Run) -> dict[str, Any]:
    baseline_config = json.loads(baseline.configuration_json or "{}")
    current_config = json.loads(current.configuration_json or "{}")
    baseline_checks = baseline_config.get("checks", [])
    current_checks = current_config.get("checks", [])
    compatibility_fields = {
        "dataset_identity": baseline.reference_dataset_asset_id == current.reference_dataset_asset_id,
        "model_identity": baseline.model_asset_id == current.model_asset_id,
        "preprocessing_configuration": baseline_config.get("configuration", {}).get("preprocessing") == current_config.get("configuration", {}).get("preprocessing"),
        "evaluation_configuration": [check for check in baseline_checks if check != "COMPARATOR"] == [check for check in current_checks if check != "COMPARATOR"],
        "scenario": baseline_config.get("configuration", {}).get("scenario", "NONE") == current_config.get("configuration", {}).get("scenario", "NONE"),
        "configuration_hash": baseline.configuration_hash == current.configuration_hash,
    }
    incompatible = [name for name, matched in compatibility_fields.items() if not matched and name not in {"model_identity", "scenario", "configuration_hash"}]
    baseline_findings = list(db.scalars(select(Finding).where(Finding.run_id == baseline.id)).all())
    current_findings = list(db.scalars(select(Finding).where(Finding.run_id == current.id)).all())
    baseline_by_key = {_finding_identity(item): item for item in baseline_findings}
    current_by_key = {_finding_identity(item): item for item in current_findings}
    changes: list[dict[str, Any]] = []
    for key in sorted(set(baseline_by_key) | set(current_by_key)):
        before, after = baseline_by_key.get(key), current_by_key.get(key)
        if before is None:
            changes.append({"finding_id": after.id, "category": after.category, "description": after.description, "type": "NEW", "current_status": after.status, "current_severity": after.severity})
        elif after is None:
            changes.append({"finding_id": before.id, "category": before.category, "description": before.description, "type": "CLEARED", "baseline_status": before.status, "baseline_severity": before.severity})
        elif before.status != after.status or before.severity != after.severity:
            changes.append({"finding_id": after.id, "category": after.category, "description": after.description, "type": "STATUS_CHANGE", "baseline_status": before.status, "current_status": after.status, "baseline_severity": before.severity, "current_severity": after.severity})
        else:
            changes.append({"finding_id": after.id, "category": after.category, "description": after.description, "type": "UNCHANGED", "baseline_status": before.status, "current_status": after.status})
    baseline_summary = json.loads(baseline.summary_json or "{}")
    current_summary = json.loads(current.summary_json or "{}")
    metric_deltas = []
    for key in ("image_count", "annotation_count", "duplicate_count", "invalid_annotation_count"):
        before = baseline_summary.get("profile", {}).get(key)
        after = current_summary.get("profile", {}).get(key)
        if before is not None or after is not None:
            metric_deltas.append({"metric": key, "baseline_value": before or 0, "current_value": after or 0, "delta": (after or 0) - (before or 0)})
    for key in ("observed_value", "threshold"):
        before = baseline_summary.get("distribution_shift", {}).get(key)
        after = current_summary.get("distribution_shift", {}).get(key)
        if before is not None or after is not None:
            metric_deltas.append({"metric": f"distribution_{key}", "baseline_value": before or 0, "current_value": after or 0, "delta": (after or 0) - (before or 0)})
    baseline_model_hash = baseline_summary.get("model", {}).get("current_sha256")
    current_model_hash = current_summary.get("model", {}).get("current_sha256")
    return {
        "baseline_run_id": baseline.id,
        "current_run_id": current.id,
        "compatibility": {"is_compatible": not incompatible, "fields": compatibility_fields, "mismatched_fields": incompatible, "reason": "Runs differ in required evaluation identity/configuration." if incompatible else None},
        "metric_deltas": metric_deltas,
        "finding_changes": changes,
        "model_hash_changed": bool(baseline_model_hash and current_model_hash and baseline_model_hash != current_model_hash) or baseline.model_asset_id != current.model_asset_id,
        "summary": "Runs are compatible for structured comparison." if not incompatible else "Runs are not directly comparable because required identities or configurations differ.",
    }
