from analytics.runner import run_analytics
from assurance.ledger import verify_ledger
from assurance.scenarios import run_scenario


def _module(run, name: str):
    return next(module for module in run.modules if module.module.value == name)


def test_none_compares_reference_to_reference_and_passes_shift():
    run = run_analytics("NONE", timestamp="2026-01-02T00:00:00Z")
    assert _module(run, "distribution_shift").status.value == "PASS"
    assert _module(run, "distribution_shift").metrics["psi"] < 0.01
    assert run.inference is not None and run.inference.simulated is True
    assert _module(run, "comparator").metrics["simulated"] is True
    assert _module(run, "comparator").metrics["mean_iou"] == 1
    assert run.status == "PASS"
    assert run.ledger_verification.status == "VALID"
    assert run.ledger_entry is not None
    assert run.ledger_entry.baseline_run_id == "RUN-BASELINE-NONE"


def test_brightness_run_is_review_and_ledger_tamper_fails_only_the_copy():
    ledger = []
    run = run_analytics("BRIGHTNESS", ledger=ledger, timestamp="2026-01-02T00:00:00Z")
    assert _module(run, "distribution_shift").status.value == "WARNING"
    assert "brightness" in _module(run, "distribution_shift").metrics["features_at_max_psi"]
    assert run.status == "REVIEW"
    assert run.ledger_verification.status == "VALID"
    assert verify_ledger(ledger).status == "VALID"

    tampered = [entry.model_copy(deep=True) for entry in ledger]
    tampered[0].summary_hash = "f" * 64
    assert verify_ledger(tampered).status == "FAILED"
    assert verify_ledger(tampered).first_invalid_sequence == 1
    assert verify_ledger(ledger).status == "VALID"


def test_person_1_distribution_shift_scenario_stays_not_run():
    run = run_scenario("DISTRIBUTION_SHIFT", timestamp="2026-01-01T00:00:00Z")
    assert run.inference is None
    assert run.ledger_entry is None
    assert {module.status.value for module in run.modules} == {"NOT_RUN"}
