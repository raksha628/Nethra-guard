"""Controlled Person 1 scenarios.

NONE, DATA_ANOMALY, and MODEL_MISMATCH run dataset and model checks.
DISTRIBUTION_SHIFT and the comparator stay NOT_RUN. This workstream does not
compute shift or baseline metric deltas.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .data_integrity import check_dataset, fingerprint_dataset
from .hashing import canonical_json, sha256_text
from .inference import InferenceResult, normalized_detections, run_inference
from .ledger import append_entry, verify_ledger
from .model_integrity import check_model
from .schemas import LedgerEntry, LedgerVerification, ModuleName, ModuleResult, not_run

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
HANDOFF_TIMESTAMP = "2026-01-01T00:00:00Z"
SCENARIOS = ("NONE", "DATA_ANOMALY", "MODEL_MISMATCH", "DISTRIBUTION_SHIFT")

SHIFT_REASON = (
    "Distribution shift is owned by the analytics workstream and is not executed in this module."
)
COMPARATOR_REASON = (
    "Baseline comparison is owned by the analytics workstream and is not executed in this module."
)
OTHER_SCENARIO_REASON = (
    "This scenario is not executed by the data, model, and inference workstream."
)


class ScenarioRun(BaseModel):
    scenario: str
    modules: list[ModuleResult]
    inference: InferenceResult | None = None
    ledger_entry: LedgerEntry | None = None
    ledger_verification: LedgerVerification


def run_scenario(
    scenario: str,
    ledger: list[LedgerEntry] | None = None,
    timestamp: str | None = None,
) -> ScenarioRun:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario!r}. Expected one of {SCENARIOS}.")
    chain = ledger if ledger is not None else []
    if scenario == "DISTRIBUTION_SHIFT":
        modules = [
            not_run(ModuleName.data_integrity, OTHER_SCENARIO_REASON),
            not_run(ModuleName.model_integrity, OTHER_SCENARIO_REASON),
            not_run(ModuleName.distribution_shift, SHIFT_REASON),
            not_run(ModuleName.comparator, COMPARATOR_REASON),
        ]
        return ScenarioRun(
            scenario=scenario,
            modules=modules,
            inference=None,
            ledger_entry=None,
            ledger_verification=verify_ledger(chain),
        )

    manifest = json.loads((FIXTURES / "baseline_manifest.json").read_text(encoding="utf-8"))
    dataset_dir = FIXTURES / ("anomaly" if scenario == "DATA_ANOMALY" else "clean")
    model_name = "altered_model.bin" if scenario == "MODEL_MISMATCH" else "baseline_model.bin"
    model_path = FIXTURES / "models" / model_name
    allowed_root = FIXTURES / "models"

    data_result = check_dataset(dataset_dir)
    model_result = check_model(
        model_path,
        baseline_sha256=manifest["model_hash"],
        allowed_root=allowed_root,
    )
    inference = run_inference(
        model_path,
        _image_paths(dataset_dir),
        allowed_root=allowed_root,
        config={"scenario": scenario},
    )
    modules = [
        data_result,
        model_result,
        not_run(ModuleName.distribution_shift, SHIFT_REASON),
        not_run(ModuleName.comparator, COMPARATOR_REASON),
    ]
    run_config = {
        "annotation_format": "coco",
        "checks": {
            "comparator": False,
            "data_integrity": True,
            "distribution_shift": False,
            "model_integrity": True,
        },
        "preprocessing": inference.preprocessing,
        "scenario": scenario,
    }
    config_hash = sha256_text(canonical_json(run_config))
    summary_hash = sha256_text(canonical_json(_summary_payload(modules, inference)))
    when = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sequence = len(chain) + 1
    entry = append_entry(
        chain,
        run_id=f"RUN-{scenario}-{sequence:03d}",
        timestamp=when,
        dataset_hash=str(data_result.metrics.get("dataset_hash") or fingerprint_dataset(dataset_dir)),
        model_hash=str(model_result.metrics.get("sha256") or ""),
        config_hash=config_hash,
        summary_hash=summary_hash,
        baseline_run_id=None,
    )
    return ScenarioRun(
        scenario=scenario,
        modules=modules,
        inference=inference,
        ledger_entry=entry,
        ledger_verification=verify_ledger(chain),
    )


def scenario_to_handoff(run: ScenarioRun) -> dict[str, Any]:
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
        "scenario": run.scenario,
    }


def export_handoff(fixtures_dir: Path | None = None) -> None:
    root = fixtures_dir or FIXTURES
    clean = run_scenario("NONE", timestamp=HANDOFF_TIMESTAMP)
    anomaly = run_scenario("DATA_ANOMALY", timestamp=HANDOFF_TIMESTAMP)
    _write_json(root / "expected_clean.json", scenario_to_handoff(clean))
    _write_json(root / "expected_anomaly.json", scenario_to_handoff(anomaly))
    assert clean.inference is not None
    _write_json(root / "normalized_detections.json", normalized_detections(clean.inference))


def _image_paths(dataset_dir: Path) -> list[Path]:
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


def _summary_payload(modules: list[ModuleResult], inference: InferenceResult) -> dict[str, Any]:
    return {
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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Person 1 assurance scenario")
    parser.add_argument("scenario", nargs="?", default="NONE", choices=SCENARIOS)
    args = parser.parse_args()
    run = run_scenario(args.scenario)
    print(json.dumps(scenario_to_handoff(run), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
