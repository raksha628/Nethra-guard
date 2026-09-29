import json
from pathlib import Path

from assurance.scenarios import HANDOFF_TIMESTAMP, run_scenario, scenario_to_handoff
from assurance.schemas import ModuleStatus

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _module(run, name: str):
    return next(module for module in run.modules if module.module.value == name)


def test_clean_scenario_matches_handoff():
    run = run_scenario("NONE", timestamp=HANDOFF_TIMESTAMP)
    expected = json.loads((FIXTURES / "expected_clean.json").read_text(encoding="utf-8"))
    assert scenario_to_handoff(run) == expected
    assert _module(run, "data_integrity").status == ModuleStatus.PASS
    assert _module(run, "model_integrity").status == ModuleStatus.PASS
    assert _module(run, "distribution_shift").status == ModuleStatus.NOT_RUN
    assert _module(run, "comparator").status == ModuleStatus.NOT_RUN
    assert run.ledger_verification.status == "VALID"
    assert run.ledger_entry is not None
    assert run.ledger_entry.previous_hash == "0" * 64
    manifest = json.loads((FIXTURES / "baseline_manifest.json").read_text(encoding="utf-8"))
    assert run.ledger_entry.dataset_hash == manifest["dataset_hash"]
    assert run.ledger_entry.model_hash == manifest["model_hash"]


def test_anomaly_scenario_matches_handoff_and_fails_data_only():
    run = run_scenario("DATA_ANOMALY", timestamp=HANDOFF_TIMESTAMP)
    expected = json.loads((FIXTURES / "expected_anomaly.json").read_text(encoding="utf-8"))
    assert scenario_to_handoff(run) == expected
    assert _module(run, "data_integrity").status == ModuleStatus.FAIL
    assert _module(run, "model_integrity").status == ModuleStatus.PASS
    assert _module(run, "distribution_shift").status == ModuleStatus.NOT_RUN


def test_model_mismatch_fails_the_model_and_passes_the_dataset():
    run = run_scenario("MODEL_MISMATCH", timestamp=HANDOFF_TIMESTAMP)
    assert _module(run, "data_integrity").status == ModuleStatus.PASS
    model = _module(run, "model_integrity")
    assert model.status == ModuleStatus.FAIL
    assert model.findings[0].title == "SHA-256 hash differs from registered baseline"
    assert "does not prove malicious tampering" in model.findings[0].limitations
    assert run.inference is not None and run.inference.simulated is True
    assert _module(run, "comparator").status == ModuleStatus.NOT_RUN


def test_distribution_shift_scenario_is_not_run():
    run = run_scenario("DISTRIBUTION_SHIFT", timestamp=HANDOFF_TIMESTAMP)
    assert run.inference is None
    assert run.ledger_entry is None
    assert {module.status for module in run.modules} == {ModuleStatus.NOT_RUN}
    assert _module(run, "distribution_shift").metrics["reason"].startswith("Distribution shift")
