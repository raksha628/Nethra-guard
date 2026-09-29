from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings
from app.db.models import Asset, Workspace
from app.services.hash_service import calculate_sha256
from app.services.model_adapter import FROZEN_EVALUATION_SET, DeterministicFallbackAdapter, ModelAdapter, NormalizedPrediction, compare_predictions, normalize_predictions, select_adapter


@dataclass
class ModelEvidence:
    sample_id: str
    metric: str
    expected_value: str | None
    observed_value: str | None
    reference: str | None


@dataclass
class ModelFinding:
    severity: str
    title: str
    description: str
    method: str
    observed_value: str
    threshold: str
    confidence_note: str
    limitations: str
    remediation: str
    affected_sample: str | None
    evidence: list[ModelEvidence]

    @property
    def category(self) -> str:
        return "MODEL_INTEGRITY"

    @property
    def status(self) -> str:
        return "OPEN"


def _finding(title: str, description: str, method: str, observed: str, threshold: str, remediation: str, evidence: list[ModelEvidence], severity: str = "WARNING", sample: str | None = None) -> ModelFinding:
    return ModelFinding(severity, title, description, method, observed, threshold, "Deterministic comparison; no maliciousness conclusion is inferred.", "Model behavior depends on the selected adapter and fixed evaluation set; this prototype does not establish production performance.", remediation, sample, evidence)


def _controlled_copy(source: Path, model_asset_id: str) -> Path:
    destination = settings.workspace_root / "demo" / f"controlled_model_alternate_{model_asset_id}.bin"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    with destination.open("ab") as output:
        output.write(b"NETRA-GUARD-CONTROLLED-PROTOTYPE-MODEL-ALTERNATE")
    return destination


def _load_predictions(adapter: ModelAdapter, path: Path) -> tuple[ModelAdapter, list[NormalizedPrediction], list[str]]:
    errors = adapter.validate(path)
    if errors:
        return adapter, [], errors
    try:
        adapter.load(path)
        return adapter, adapter.run_inference(list(FROZEN_EVALUATION_SET)), []
    except Exception as exc:
        fallback = DeterministicFallbackAdapter()
        fallback.load(path)
        return fallback, fallback.run_inference(list(FROZEN_EVALUATION_SET)), [f"selected adapter unavailable: {exc.__class__.__name__}; deterministic fallback used"]


def run_model_integrity(current_asset: Asset, current_path: Path, baseline_asset: Asset | None, baseline_path: Path | None, workspace: Workspace, configuration: dict[str, Any]) -> tuple[dict[str, Any], list[ModelFinding]]:
    scenario = str(configuration.get("scenario", "NONE"))
    effective_current_path = _controlled_copy(current_path, current_asset.id) if scenario == "MODEL_MISMATCH" else current_path
    current_hash = calculate_sha256(effective_current_path)
    current_adapter, current_predictions, current_adapter_notes = _load_predictions(select_adapter(effective_current_path), effective_current_path)
    findings: list[ModelFinding] = []
    baseline_hash = workspace.baseline_model_sha256
    baseline_predictions: list[NormalizedPrediction] = []
    baseline_adapter_notes: list[str] = []

    if baseline_asset and baseline_path:
        baseline_hash = baseline_hash or calculate_sha256(baseline_path)
        baseline_adapter, baseline_predictions, baseline_adapter_notes = _load_predictions(select_adapter(baseline_path), baseline_path)
        if current_hash != baseline_hash:
            findings.append(_finding(
                "Model artifact differs from registered baseline.",
                "The current model artifact has a different SHA-256 digest than the registered baseline.",
                "Exact SHA-256 comparison against the registered model baseline",
                current_hash,
                baseline_hash,
                "Review and approve the model change or restore the registered baseline. A hash difference alone does not prove malicious tampering.",
                [ModelEvidence("model-artifact", "sha256", baseline_hash, current_hash, f"baseline:{baseline_hash};current:{current_hash}")],
            ))
    else:
        findings.append(_finding("Model baseline is not registered.", "Model Integrity could not compare the current artifact because no baseline model is registered.", "Required baseline lookup", current_hash, "registered baseline SHA-256", "Register this model as the workspace baseline before comparison.", [ModelEvidence("model-artifact", "baseline", "registered", "not registered", f"current:{current_hash}")]))

    adapter_notes = current_adapter_notes + baseline_adapter_notes
    if adapter_notes:
        findings.append(_finding("Model metadata or format problem", "The selected model adapter could not validate or execute the model artifact natively; deterministic fallback behavior was used.", "ModelAdapter validation and deterministic fallback selection", "; ".join(adapter_notes), "adapter validation succeeds", "Use a supported model format with its model-specific preprocessing adapter, or review the fallback result as limited prototype evidence.", [ModelEvidence("model-adapter", "adapter", "native adapter", current_adapter.metadata().adapter, f"model:{current_asset.original_name}")], severity="WARNING"))

    comparison = compare_predictions(baseline_predictions, current_predictions, settings.model_confidence_delta_threshold, settings.model_iou_threshold) if baseline_predictions else []
    for change in comparison:
        findings.append(_finding(
            f"Model prediction {change['type'].replace('_', ' ')} detected",
            f"Fixed evaluation sample {change['sample_id']} changed between baseline and current model outputs.",
            "Normalized prediction comparison on the frozen evaluation set",
            str(change),
            f"confidence delta <= {settings.model_confidence_delta_threshold:g}; IoU >= {settings.model_iou_threshold:g}",
            "Review the changed prediction and confirm whether the model update is intended.",
            [ModelEvidence(change["sample_id"], change["type"], str(change.get("baseline")), str(change.get("current")), f"baseline:{baseline_hash};current:{current_hash}")],
            sample=change["sample_id"],
        ))

    summary = {
        "baseline_asset_id": baseline_asset.id if baseline_asset else None,
        "baseline_sha256": baseline_hash,
        "current_asset_id": current_asset.id,
        "current_sha256": current_hash,
        "hash_match": bool(baseline_hash and baseline_hash == current_hash),
        "controlled_scenario": scenario == "MODEL_MISMATCH",
        "adapter": current_adapter.metadata().__dict__,
        "evaluation_set": [sample.sample_id for sample in FROZEN_EVALUATION_SET],
        "preprocessing": FROZEN_EVALUATION_SET[0].preprocessing,
        "baseline_predictions": normalize_predictions(baseline_predictions),
        "current_predictions": normalize_predictions(current_predictions),
        "prediction_changes": comparison,
        "thresholds": {"confidence_delta": settings.model_confidence_delta_threshold, "iou": settings.model_iou_threshold},
    }
    return summary, findings
