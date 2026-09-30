"""Analytics runner. Person 1's skipped shift scenario stays skipped."""

from assurance.ledger import verify_ledger
from assurance.scenarios import run_scenario
from assurance.schemas import ModuleStatus
from analytics.runner import BASELINE_RUN_ID, run_analytics

HANDOFF_TIMESTAMP = "2026-01-01T00:00:00Z"


def _module(run, name: str):
    return next(module for module in run.modules if module.module.value == name)


def test_none_passes_with_a_stable_simulated_contract():
    run = run_analytics("NONE", timestamp=HANDOFF_TIMESTAMP)
    assert _module(run, "data_integrity").status == ModuleStatus.PASS
    assert _module(run, "model_integrity").status == ModuleStatus.PASS
    assert _module(run, "distribution_shift").status == ModuleStatus.PASS
    comparator = _module(run, "comparator")
    assert comparator.status == ModuleStatus.PASS
    assert comparator.metrics["mean_iou"] == 1.0
    assert comparator.metrics["detection_count_delta"] == 0
    assert comparator.metrics["simulated"] is True
    assert run.inference.simulated is True
    assert run.decision.status == "PASS"
    assert run.ledger_verification.status == "VALID"
    assert run.ledger_entry.run_id == BASELINE_RUN_ID
    assert run.ledger_entry.baseline_run_id is None


def test_brightness_is_review_and_the_ledger_detects_a_copied_edit():
    ledger = []
    baseline = run_analytics("NONE", ledger=ledger, timestamp=HANDOFF_TIMESTAMP)
    current = run_analytics("BRIGHTNESS", ledger=ledger, timestamp=HANDOFF_TIMESTAMP)
    shift = _module(current, "distribution_shift")
    assert shift.status == ModuleStatus.WARNING
    assert shift.metrics["affected_feature"] == "brightness"
    comparator = _module(current, "comparator")
    assert comparator.status == ModuleStatus.NOT_RUN
    assert comparator.metrics["comparable"] is False
    assert "config" in comparator.metrics["mismatched_fields"]
    assert "detection_count_delta" not in comparator.metrics
    assert current.decision.status == "REVIEW"
    assert current.decision.notes
    assert current.inference.simulated is True
    assert current.ledger_entry.baseline_run_id == baseline.ledger_entry.run_id == BASELINE_RUN_ID
    assert current.ledger_verification.status == "VALID"

    tampered = [entry.model_copy(deep=True) for entry in ledger]
    tampered[0] = tampered[0].model_copy(update={"dataset_hash": "f" * 64})
    failed = verify_ledger(tampered)
    assert failed.status == "FAILED"
    assert failed.first_invalid_sequence == 1
    assert verify_ledger(ledger).status == "VALID"


def test_person1_distribution_shift_scenario_stays_not_run():
    run = run_scenario("DISTRIBUTION_SHIFT", timestamp=HANDOFF_TIMESTAMP)
    assert {module.status for module in run.modules} == {ModuleStatus.NOT_RUN}
    assert run.inference is None
    assert run.ledger_entry is None
