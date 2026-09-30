"""Person 2 scenario runner.

Calls the assurance core for dataset, model, and simulated detections, then
replaces the skipped shift and comparator modules with analytics results.
Person 1's run_scenario stays unchanged, including DISTRIBUTION_SHIFT as NOT_RUN.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from assurance.data_integrity import check_dataset
from assurance.hashing import canonical_json, sha256_text
from assurance.inference import InferenceResult, run_inference
from assurance.ledger import append_entry, verify_ledger
from assurance.model_integrity import check_model
from assurance.schemas import LedgerEntry, LedgerVerification, ModuleName, ModuleResult, ModuleStatus

from .comparator import RunSnapshot, compare_runs, findings_from_modules
from .features import FEATURE_ORDER
from .shift import BIN_COUNT, EDGE_DENSITY_EDGES, PSI_THRESHOLD, check_shift
from .status import AssuranceDecision, aggregate_status

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SHIFT_ROOT = FIXTURES / "shift"
REFERENCE_BATCH = SHIFT_ROOT / "reference"
CLEAN_DATASET = FIXTURES / "clean"
MODELS = FIXTURES / "models"
BASELINE_RUN_ID = "RUN-ANALYTICS-NONE-001"
SCENARIOS = ("NONE", "BRIGHTNESS", "BLUR", "CONTRAST", "COLOR_CAST", "RESOLUTION")


class AnalyticsRun(BaseModel):
    scenario: str
    modules: list[ModuleResult]
    inference: InferenceResult
    decision: AssuranceDecision
    ledger_entry: LedgerEntry
    ledger_verification: LedgerVerification


def run_analytics(
    scenario: str,
    ledger: list[LedgerEntry] | None = None,
    timestamp: str | None = None,
) -> AnalyticsRun:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario!r}. Expected one of {SCENARIOS}.")
    chain = ledger if ledger is not None else []
    manifest = json.loads((FIXTURES / "baseline_manifest.json").read_text(encoding="utf-8"))
    data_result = check_dataset(CLEAN_DATASET)
    model_path = MODELS / "baseline_model.bin"
    model_result = check_model(
        model_path,
        baseline_sha256=manifest["model_hash"],
        allowed_root=MODELS,
    )
    inference = run_inference(
        model_path,
        sorted((CLEAN_DATASET / "images").glob("*.png")),
        allowed_root=MODELS,
        config={"scenario": scenario, "workstream": "analytics"},
    )
    current_batch = REFERENCE_BATCH if scenario == "NONE" else SHIFT_ROOT / scenario.lower()
    current_shift = check_shift(REFERENCE_BATCH, current_batch)
    reference_shift = current_shift if scenario == "NONE" else check_shift(REFERENCE_BATCH, REFERENCE_BATCH)

    sequence = len(chain) + 1
    run_id = f"RUN-ANALYTICS-{scenario}-{sequence:03d}"
    current_config = _evaluation_config(scenario, inference.preprocessing)
    baseline_config = _evaluation_config("NONE", inference.preprocessing)
    baseline_snapshot = RunSnapshot(
        run_id=BASELINE_RUN_ID,
        dataset_hash=str(data_result.metrics.get("dataset_hash")),
        model_hash=str(model_result.metrics.get("sha256")),
        preprocessing=inference.preprocessing,
        config=baseline_config,
        detections=inference.images,
        findings=findings_from_modules([data_result, model_result, reference_shift]),
        simulated=inference.simulated,
    )
    current_snapshot = RunSnapshot(
        run_id=run_id,
        dataset_hash=baseline_snapshot.dataset_hash,
        model_hash=baseline_snapshot.model_hash,
        preprocessing=inference.preprocessing,
        config=current_config,
        detections=inference.images,
        findings=findings_from_modules([data_result, model_result, current_shift]),
        simulated=inference.simulated,
    )
    comparator = compare_runs(baseline_snapshot, current_snapshot)
    modules = [data_result, model_result, current_shift, comparator]
    required = [
        ModuleName.data_integrity,
        ModuleName.model_integrity,
        ModuleName.distribution_shift,
    ]
    notes: list[str] = []
    if comparator.status == ModuleStatus.NOT_RUN:
        reason = comparator.metrics.get("reason")
        if isinstance(reason, str):
            notes.append(reason)
    else:
        required.append(ModuleName.comparator)
    decision = aggregate_status(modules, required)
    if notes:
        decision = decision.model_copy(update={"notes": notes})

    when = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    config_hash = sha256_text(canonical_json(current_config))
    summary_hash = sha256_text(canonical_json(_summary_payload(modules, inference, decision)))
    entry = append_entry(
        chain,
        run_id=run_id,
        timestamp=when,
        dataset_hash=baseline_snapshot.dataset_hash,
        model_hash=baseline_snapshot.model_hash,
        config_hash=config_hash,
        summary_hash=summary_hash,
        baseline_run_id=None if scenario == "NONE" else BASELINE_RUN_ID,
    )
    return AnalyticsRun(
        scenario=scenario,
        modules=modules,
        inference=inference,
        decision=decision,
        ledger_entry=entry,
        ledger_verification=verify_ledger(chain),
    )


def analytics_to_handoff(run: AnalyticsRun) -> dict[str, Any]:
    inference = run.inference.model_dump(mode="json")
    inference.pop("timing_ms", None)
    entry = run.ledger_entry.model_dump(mode="json", by_alias=True)
    entry["isValid"] = run.ledger_verification.status == "VALID"
    return {
        "decision": run.decision.model_dump(mode="json"),
        "inference": inference,
        "ledger_entry": entry,
        "ledger_verification": run.ledger_verification.model_dump(mode="json", by_alias=True),
        "modules": [module.model_dump(mode="json") for module in run.modules],
        "scenario": run.scenario,
    }


def _evaluation_config(scenario: str, preprocessing: dict[str, Any]) -> dict[str, Any]:
    current_batch = "reference" if scenario == "NONE" else scenario.lower()
    return {
        "annotation_format": "coco",
        "checks": {
            "comparator": True,
            "data_integrity": True,
            "distribution_shift": True,
            "model_integrity": True,
        },
        "preprocessing": preprocessing,
        "scenario": scenario,
        "shift": {
            "bin_count": BIN_COUNT,
            "current_batch": current_batch,
            "edge_density_edges": list(EDGE_DENSITY_EDGES),
            "features": list(FEATURE_ORDER),
            "psi_threshold": PSI_THRESHOLD,
            "reference_batch": "reference",
        },
    }


def _summary_payload(
    modules: list[ModuleResult],
    inference: InferenceResult,
    decision: AssuranceDecision,
) -> dict[str, Any]:
    return {
        "decision": decision.status,
        "inference": {
            "adapter": inference.adapter,
            "executed": inference.executed,
            "images": [item.model_dump(mode="json") for item in inference.images],
            "input_set_hash": inference.input_set_hash,
            "model_hash": inference.model_hash,
            "simulated": inference.simulated,
        },
        "modules": [
            {
                "findings": [
                    {
                        "observed_value": finding.observed_value,
                        "severity": finding.severity.value,
                        "title": finding.title,
                    }
                    for finding in module.findings
                ],
                "module": module.module.value,
                "status": module.status.value,
            }
            for module in modules
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Person 2 analytics scenario")
    parser.add_argument("scenario", nargs="?", default="NONE", choices=SCENARIOS)
    args = parser.parse_args()
    run = run_analytics(args.scenario)
    print(json.dumps(analytics_to_handoff(run), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
