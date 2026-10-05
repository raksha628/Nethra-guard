import json
from pathlib import Path

from analytics.comparator import RunRecord, compare_runs
from assurance.schemas import EvidenceRef, Finding, Severity

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
PREPROCESSING = {"color_order": "RGB", "normalization": "none", "resize": None}
CONFIGURATION = {"adapter": "deterministic_fallback", "scenario": "NONE"}


def _record(detections, **overrides) -> RunRecord:
    payload = {
        "dataset_hash": "a" * 64,
        "model_hash": "b" * 64,
        "preprocessing": PREPROCESSING,
        "configuration": CONFIGURATION,
        "detections": detections,
        "findings": [],
        "simulated": True,
    }
    payload.update(overrides)
    return RunRecord(**payload)


def _baseline_detections() -> list[dict]:
    return json.loads((FIXTURES / "normalized_detections.json").read_text(encoding="utf-8"))


def _edited_detections() -> list[dict]:
    payload = json.loads((FIXTURES / "shift" / "simulated_detections_edited.json").read_text(encoding="utf-8"))
    assert payload["simulated"] is True
    return payload["images"]


def _finding(title: str, severity: Severity, evidence_id: str) -> Finding:
    return Finding(
        severity=severity,
        title=title,
        method="rule",
        observed_value="1",
        threshold="0",
        evidence_refs=[EvidenceRef(id=evidence_id, sample_id="img_001.png", evidence_type="test")],
        limitations="test fixture",
    )


def test_compatible_identical_detections_have_no_misleading_deltas():
    detections = _baseline_detections()
    result = compare_runs(_record(detections), _record(detections))
    assert result.status.value == "PASS"
    assert result.metrics["comparable"] is True
    assert result.metrics["simulated"] is True
    assert result.metrics["detection_count_delta"] == 0
    assert result.metrics["mean_confidence_delta"] == 0
    assert result.metrics["mean_iou"] == 1
    assert result.metrics["class_changes"] == []
    assert result.findings == []


def test_dataset_model_preprocessing_or_config_mismatch_omits_deltas():
    detections = _baseline_detections()
    baseline = _record(detections)
    cases = [
        {"dataset_hash": "c" * 64},
        {"model_hash": "d" * 64},
        {"preprocessing": {**PREPROCESSING, "resize": 32}},
        {"configuration": {**CONFIGURATION, "scenario": "OTHER"}},
    ]
    for overrides in cases:
        result = compare_runs(baseline, _record(detections, **overrides))
        assert result.status.value == "NOT_RUN"
        assert result.metrics["comparable"] is False
        assert result.metrics["mismatched_fields"]
        assert "detection_count_delta" not in result.metrics
        assert "mean_iou" not in result.metrics
        assert result.findings == []


def test_simulated_detection_edit_moves_count_confidence_class_and_iou():
    result = compare_runs(_record(_baseline_detections()), _record(_edited_detections()))
    assert result.metrics["simulated"] is True
    assert result.metrics["detection_count_delta"] != 0
    assert result.metrics["mean_confidence_delta"] not in (None, 0)
    assert result.metrics["class_changes"]
    assert result.metrics["mean_iou"] is not None and result.metrics["mean_iou"] < 1
    assert result.status.value == "WARNING"


def test_finding_new_and_cleared_are_listed_without_rewriting_inputs():
    kept = _finding("Kept", Severity.LOW, "kept")
    cleared = _finding("Cleared", Severity.MEDIUM, "cleared")
    appeared = _finding("Appeared", Severity.HIGH, "appeared")
    changed = _finding("Changed", Severity.LOW, "changed")
    changed_now = _finding("Changed", Severity.CRITICAL, "changed")
    baseline = _record(_baseline_detections(), findings=[kept, cleared, changed])
    current = _record(_baseline_detections(), findings=[kept, appeared, changed_now])
    before = [item.model_dump() for item in baseline.findings]
    result = compare_runs(baseline, current)
    changes = {item["title"]: item["change"] for item in result.metrics["finding_changes"]}
    assert changes == {
        "Kept": "UNCHANGED",
        "Cleared": "CLEARED",
        "Appeared": "NEW",
        "Changed": "SEVERITY_CHANGE",
    }
    assert [item.model_dump() for item in baseline.findings] == before
