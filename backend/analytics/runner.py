"""Person 2 scenario entry. Separate from assurance.scenarios.run_scenario.

NONE compares the reference batch to itself, so shift passes.
BRIGHTNESS, BLUR, CONTRAST, COLOR_CAST, and RESOLUTION compare the owned
transformed batches. Person 1 still runs on the clean dataset and baseline model.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from assurance.data_integrity import check_dataset, fingerprint_dataset
from assurance.hashing import canonical_json, sha256_text
from assurance.inference import InferenceResult, normalized_detections, run_inference
from assurance.ledger import append_entry, verify_ledger
from assurance.model_integrity import check_model
from assurance.scenarios import FIXTURES
from assurance.schemas import LedgerEntry, LedgerVerification, ModuleResult

from .comparator import RunRecord, compare_runs
from .features import feature_names
from .shift import BIN_COUNT, PSI_CUTOFF, check_shift
from .status import aggregate_status

SHIFT_ROOT = FIXTURES / "shift"
REFERENCE_DIR = SHIFT_ROOT / "reference"
SCENARIOS = ("NONE", "BRIGHTNESS", "BLUR", "CONTRAST", "COLOR_CAST", "RESOLUTION")
BATCH_DIRECTORIES = {
    "NONE": REFERENCE_DIR,
    "BRIGHTNESS": SHIFT_ROOT / "brightness",
    "BLUR": SHIFT_ROOT / "blur",
    "CONTRAST": SHIFT_ROOT / "contrast",
    "COLOR_CAST": SHIFT_ROOT / "color_cast",
    "RESOLUTION": SHIFT_ROOT / "resolution",
}


class AnalyticsRun(BaseModel):
    scenario: str
    status: str
    reasons: list[str]
    modules: list[ModuleResult]
    inference: InferenceResult | None = None
    ledger_entry: LedgerEntry | None = None
    ledger_verification: LedgerVerification


def shift_config(scenario: str) -> dict[str, Any]:
    current_name = "reference" if scenario == "NONE" else scenario.lower()
    return {
        "batch_names": {"current": current_name, "reference": "reference"},
        "bin_count": BIN_COUNT,
        "features": feature_names(),
        "preprocessing": "image-features-v1",
        "psi_cutoff": PSI_CUTOFF,
        "scenario": scenario,
    }


def run_analytics(
    scenario: str,
    ledger: list[LedgerEntry] | None = None,
    timestamp: str | None = None,
) -> AnalyticsRun:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario!r}. Expected one of {SCENARIOS}.")
    chain = ledger if ledger is not None else []
    manifest = json.loads((FIXTURES / "baseline_manifest.json").read_text(encoding="utf-8"))
    dataset_dir = FIXTURES / "clean"
    model_path = FIXTURES / "models" / "baseline_model.bin"
    allowed_root = FIXTURES / "models"
    data_result = check_dataset(dataset_dir)
    model_result = check_model(
        model_path,
        baseline_sha256=manifest["model_hash"],
        allowed_root=allowed_root,
    )
    inference = run_inference(
        model_path,
        _clean_image_paths(dataset_dir),
        allowed_root=allowed_root,
        config={"scenario": "NONE", "source": "analytics"},
    )
    shift_result = check_shift(REFERENCE_DIR, BATCH_DIRECTORIES[scenario])
    stored_detections = json.loads((FIXTURES / "normalized_detections.json").read_text(encoding="utf-8"))
    shared_configuration = {"adapter": inference.adapter, "scenario": "NONE"}
    dataset_hash = str(data_result.metrics.get("dataset_hash") or fingerprint_dataset(dataset_dir))
    model_hash = str(model_result.metrics.get("sha256") or "")
    baseline_record = RunRecord(
        dataset_hash=dataset_hash,
        model_hash=model_hash,
        preprocessing=inference.preprocessing,
        configuration=shared_configuration,
        detections=stored_detections,
        findings=[],
        simulated=True,
    )
    current_record = RunRecord(
        dataset_hash=dataset_hash,
        model_hash=model_hash,
        preprocessing=inference.preprocessing,
        configuration=shared_configuration,
        detections=normalized_detections(inference),
        findings=[],
        simulated=inference.simulated,
    )
    comparator_result = compare_runs(baseline_record, current_record)
    modules = [data_result, model_result, shift_result, comparator_result]
    status = aggregate_status(modules)
    config_hash = sha256_text(canonical_json(shift_config(scenario)))
    summary_hash = sha256_text(canonical_json(_summary_payload(modules, status, inference)))
    when = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sequence = len(chain) + 1
    entry = append_entry(
        chain,
        run_id=f"RUN-SHIFT-{scenario}-{sequence:03d}",
        timestamp=when,
        dataset_hash=dataset_hash,
        model_hash=model_hash,
        config_hash=config_hash,
        summary_hash=summary_hash,
        baseline_run_id="RUN-BASELINE-NONE",
    )
    return AnalyticsRun(
        scenario=scenario,
        status=str(status["status"]),
        reasons=list(status["reasons"]),
        modules=modules,
        inference=inference,
        ledger_entry=entry,
        ledger_verification=verify_ledger(chain),
    )


def analytics_to_handoff(run: AnalyticsRun) -> dict[str, Any]:
    inference: dict[str, Any] | None = None
    if run.inference is not None:
        inference = run.inference.model_dump(mode="json")
        inference.pop("timing_ms", None)
    entry = None
    if run.ledger_entry is not None:
        entry = run.ledger_entry.model_dump(mode="json", by_alias=True)
        entry["isValid"] = run.ledger_verification.status == "VALID"
    return {
        "inference": inference,
        "ledger_entry": entry,
        "ledger_verification": run.ledger_verification.model_dump(mode="json", by_alias=True),
        "modules": [module.model_dump(mode="json") for module in run.modules],
        "reasons": run.reasons,
        "scenario": run.scenario,
        "status": run.status,
    }


def _summary_payload(
    modules: list[ModuleResult],
    status: dict[str, object],
    inference: InferenceResult,
) -> dict[str, Any]:
    return {
        "reasons": list(status["reasons"]),
        "simulated": inference.simulated,
        "status": status["status"],
        "modules": [
            {
                "module": module.module.value,
                "psi": module.metrics.get("psi"),
                "status": module.status.value,
            }
            for module in modules
        ],
    }


def _clean_image_paths(dataset_dir: Path) -> list[Path]:
    payload = json.loads((dataset_dir / "annotations.json").read_text(encoding="utf-8"))
    images_dir = dataset_dir / "images"
    paths: list[Path] = []
    for image in payload["images"]:
        file_name = image.get("file_name")
        if not isinstance(file_name, str):
            continue
        relative = Path(file_name)
        if relative.is_absolute() or ".." in relative.parts:
            continue
        paths.append(images_dir / file_name)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Person 2 analytics scenario")
    parser.add_argument("scenario", nargs="?", default="NONE", choices=SCENARIOS)
    args = parser.parse_args()
    run = run_analytics(args.scenario)
    print(json.dumps(analytics_to_handoff(run), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
