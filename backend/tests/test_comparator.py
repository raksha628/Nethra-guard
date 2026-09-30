"""Comparator tests. Edited boxes are a labeled contract, not model outputs."""

import json
from pathlib import Path

import pytest

from analytics.comparator import RunSnapshot, SourcedFinding, compare_runs
from assurance.schemas import Detection, EvidenceRef, Finding, ImageDetections, ModuleStatus, Severity

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DELTA_KEYS = (
    "detection_count_delta",
    "mean_iou",
    "mean_confidence_delta",
    "class_change_count",
    "finding_changes",
)


def _images(payload: list[dict]) -> list[ImageDetections]:
    return [ImageDetections.model_validate(item) for item in payload]


def _snapshot(**overrides) -> RunSnapshot:
    detections = _images(json.loads((FIXTURES / "normalized_detections.json").read_text(encoding="utf-8")))
    base = dict(
        run_id="RUN-BASE",
        dataset_hash="a" * 64,
        model_hash="b" * 64,
        preprocessing={"color_order": "RGB", "resize": None},
        config={"scenario": "NONE", "annotation_format": "coco"},
        detections=detections,
        findings=[],
        simulated=True,
    )
    base.update(overrides)
    return RunSnapshot(**base)


def _finding(title: str, severity: Severity = Severity.MEDIUM, sample: str = "img_001.png") -> Finding:
    return Finding(
        severity=severity,
        title=title,
        method="Rule-based / deterministic check. Test fixture.",
        observed_value="1",
        threshold="0",
        evidence_refs=[
            EvidenceRef(id=title, sample_id=sample, file_hash="c" * 64, evidence_type="test")
        ],
        limitations="Test finding.",
    )


def test_identical_simulated_runs_have_no_deltas():
    result = compare_runs(_snapshot(), _snapshot(run_id="RUN-CURRENT"))
    assert result.status == ModuleStatus.PASS
    assert result.findings == []
    assert result.metrics["comparable"] is True
    assert result.metrics["simulated"] is True
    assert result.metrics["detection_count_delta"] == 0
    assert result.metrics["class_change_count"] == 0
    assert result.metrics["mean_confidence_delta"] == 0
    assert result.metrics["mean_iou"] == 1.0
    assert "simulated" in result.metrics["limitations"].lower() or "Simulated" in result.metrics["limitations"] or "not outputs" in result.metrics["limitations"]
    assert "mAP" not in result.metrics
    assert "precision" not in result.metrics


@pytest.mark.parametrize("field", ["dataset_hash", "model_hash", "preprocessing", "config"])
def test_incompatible_runs_omit_deltas(field: str):
    current = _snapshot(run_id="RUN-CURRENT")
    if field == "dataset_hash":
        current = current.model_copy(update={"dataset_hash": "d" * 64})
    elif field == "model_hash":
        current = current.model_copy(update={"model_hash": "e" * 64})
    elif field == "preprocessing":
        current = current.model_copy(update={"preprocessing": {"color_order": "BGR", "resize": None}})
    else:
        current = current.model_copy(update={"config": {"scenario": "OTHER", "annotation_format": "coco"}})
    result = compare_runs(_snapshot(), current)
    assert result.status == ModuleStatus.NOT_RUN
    assert result.metrics["comparable"] is False
    assert field in result.metrics["mismatched_fields"]
    assert result.findings == []
    for key in DELTA_KEYS:
        assert key not in result.metrics


def test_edited_contract_moves_count_class_confidence_and_iou():
    edited = json.loads((FIXTURES / "shift" / "simulated_detections_edited.json").read_text(encoding="utf-8"))
    assert edited["simulated"] is True
    current = _snapshot(run_id="RUN-EDITED", detections=_images(edited["images"]))
    result = compare_runs(_snapshot(), current)
    assert result.status == ModuleStatus.WARNING
    assert result.metrics["simulated"] is True
    assert result.metrics["detection_count_delta"] == -1
    assert result.metrics["class_change_count"] >= 1
    assert result.metrics["mean_confidence_delta"] != 0
    assert result.metrics["mean_iou"] < 1
    assert "mAP" not in result.metrics
    finding = result.findings[0]
    assert finding.severity == Severity.MEDIUM
    assert "not prove prediction drift" in finding.limitations or "not outputs" in finding.limitations


def test_finding_changes_cover_new_cleared_severity_and_unchanged():
    baseline = _snapshot(
        findings=[
            SourcedFinding(module="data_integrity", finding=_finding("Exact duplicate images")),
            SourcedFinding(module="data_integrity", finding=_finding("Class imbalance", Severity.LOW, "img_002.png")),
            SourcedFinding(module="model_integrity", finding=_finding("Kept finding", Severity.LOW, "model")),
        ]
    )
    current = _snapshot(
        run_id="RUN-CURRENT",
        findings=[
            SourcedFinding(module="data_integrity", finding=_finding("Class imbalance", Severity.HIGH, "img_002.png")),
            SourcedFinding(module="model_integrity", finding=_finding("Kept finding", Severity.LOW, "model")),
            SourcedFinding(module="distribution_shift", finding=_finding("Image feature distribution shift")),
        ],
    )
    result = compare_runs(baseline, current)
    kinds = {item["type"] for item in result.metrics["finding_changes"]}
    assert kinds == {"NEW", "CLEARED", "SEVERITY_CHANGE", "UNCHANGED"}
    assert result.status == ModuleStatus.WARNING
    assert baseline.findings[0].finding.severity == Severity.MEDIUM


def test_same_class_match_is_preferred_when_both_overlap():
    baseline = _snapshot(
        detections=[
            ImageDetections(
                image_id="img_001.png",
                detections=[
                    Detection(class_id=1, confidence=0.9, bbox_xyxy=[0, 0, 100, 100]),
                    Detection(class_id=2, confidence=0.8, bbox_xyxy=[5, 5, 105, 105]),
                ],
            )
        ]
    )
    current = _snapshot(
        run_id="RUN-CURRENT",
        detections=[
            ImageDetections(
                image_id="img_001.png",
                detections=[
                    Detection(class_id=1, confidence=0.9, bbox_xyxy=[4, 4, 104, 104]),
                    Detection(class_id=2, confidence=0.8, bbox_xyxy=[6, 6, 106, 106]),
                ],
            )
        ],
    )
    result = compare_runs(baseline, current)
    matched = [row for row in result.metrics["matches"] if row["matched"]]
    assert len(matched) == 2
    assert result.metrics["class_change_count"] == 0
    assert all(row["class_id_baseline"] == row["class_id_current"] for row in matched)
