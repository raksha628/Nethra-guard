"""Compare two assurance runs when their inputs and settings match.

Detections join on image_id. Boxes are bbox_xyxy. A mismatch of dataset hash,
model hash, preprocessing, or configuration is not comparable: the module is
NOT_RUN and no detection deltas are reported. Precision, recall, and mAP are
not computed.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from assurance.hashing import canonical_json
from assurance.schemas import (
    EvidenceRef,
    Finding,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    Severity,
)

COMPARISON_FIELDS = ("dataset_hash", "model_hash", "preprocessing", "configuration")
NOT_COMPARABLE_REASON = (
    "Runs are not comparable because dataset hash, model hash, preprocessing, or configuration differ."
)
DELTA_LIMITATION = (
    "Detection and finding deltas describe a difference between two runs. "
    "They are not precision, recall, or mAP, and they do not prove the model failed."
)


class RunRecord(BaseModel):
    dataset_hash: str
    model_hash: str
    preprocessing: dict[str, Any]
    configuration: dict[str, Any]
    detections: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    simulated: bool = True


def compare_runs(baseline: RunRecord, current: RunRecord) -> ModuleResult:
    mismatched = _mismatched_fields(baseline, current)
    if mismatched:
        return ModuleResult(
            module=ModuleName.comparator,
            status=ModuleStatus.NOT_RUN,
            metrics={
                "comparable": False,
                "reason": NOT_COMPARABLE_REASON,
                "mismatched_fields": mismatched,
                "simulated": baseline.simulated and current.simulated,
                "limitations": DELTA_LIMITATION,
            },
            findings=[],
        )

    detection_metrics = _detection_deltas(baseline.detections, current.detections)
    finding_changes = _finding_changes(baseline.findings, current.findings)
    changed = _has_material_change(detection_metrics, finding_changes)
    metrics: dict[str, Any] = {
        "comparable": True,
        "simulated": baseline.simulated and current.simulated,
        "mismatched_fields": [],
        "finding_changes": finding_changes,
        "limitations": DELTA_LIMITATION,
        **detection_metrics,
    }
    findings: list[Finding] = []
    status = ModuleStatus.PASS
    if changed:
        status = ModuleStatus.WARNING
        findings.append(
            Finding(
                severity=Severity.MEDIUM,
                title="Baseline and current run differ",
                method=(
                    "Greedy IoU matching on bbox_xyxy per image_id, preferring the same class_id. "
                    "Finding changes are NEW, CLEARED, UNCHANGED, or a severity change."
                ),
                observed_value=(
                    f"detection_count_delta={detection_metrics['detection_count_delta']}, "
                    f"mean_iou={detection_metrics['mean_iou']}, "
                    f"class_changes={len(detection_metrics['class_changes'])}"
                ),
                threshold="identical compatible runs",
                evidence_refs=[
                    EvidenceRef(
                        id="comparator-current",
                        sample_id="current-run",
                        file_hash=current.model_hash,
                        evidence_type="run_comparison",
                    )
                ],
                limitations=DELTA_LIMITATION,
            )
        )
    return ModuleResult(
        module=ModuleName.comparator,
        status=status,
        metrics=metrics,
        findings=findings,
    )


def box_iou_xyxy(first: list[float], second: list[float]) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    area_first = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    area_second = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = area_first + area_second - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def _mismatched_fields(baseline: RunRecord, current: RunRecord) -> list[str]:
    mismatched: list[str] = []
    if baseline.dataset_hash != current.dataset_hash:
        mismatched.append("dataset_hash")
    if baseline.model_hash != current.model_hash:
        mismatched.append("model_hash")
    if canonical_json(baseline.preprocessing) != canonical_json(current.preprocessing):
        mismatched.append("preprocessing")
    if canonical_json(baseline.configuration) != canonical_json(current.configuration):
        mismatched.append("configuration")
    return mismatched


def _detection_deltas(baseline: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_by_image = _by_image(baseline)
    current_by_image = _by_image(current)
    image_ids = sorted(set(baseline_by_image) | set(current_by_image))
    baseline_boxes = [box for image_id in image_ids for box in baseline_by_image.get(image_id, [])]
    current_boxes = [box for image_id in image_ids for box in current_by_image.get(image_id, [])]
    matched_ious: list[float] = []
    class_changes: list[dict[str, Any]] = []
    for image_id in image_ids:
        for pair in _match_image(baseline_by_image.get(image_id, []), current_by_image.get(image_id, [])):
            matched_ious.append(pair["iou"])
            if pair["baseline_class_id"] != pair["current_class_id"]:
                class_changes.append(
                    {
                        "image_id": image_id,
                        "baseline_class_id": pair["baseline_class_id"],
                        "current_class_id": pair["current_class_id"],
                        "iou": round(pair["iou"], 6),
                    }
                )
    baseline_confidence = _mean_confidence(baseline_boxes)
    current_confidence = _mean_confidence(current_boxes)
    confidence_delta = None
    if baseline_confidence is not None and current_confidence is not None:
        confidence_delta = round(current_confidence - baseline_confidence, 6)
    mean_iou = round(sum(matched_ious) / len(matched_ious), 6) if matched_ious else None
    return {
        "detection_count_baseline": len(baseline_boxes),
        "detection_count_current": len(current_boxes),
        "detection_count_delta": len(current_boxes) - len(baseline_boxes),
        "mean_confidence_baseline": baseline_confidence,
        "mean_confidence_current": current_confidence,
        "mean_confidence_delta": confidence_delta,
        "class_changes": class_changes,
        "mean_iou": mean_iou,
        "matched_pair_count": len(matched_ious),
    }


def _by_image(images: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for image in images:
        image_id = str(image.get("image_id", ""))
        detections = image.get("detections") or []
        grouped.setdefault(image_id, [])
        for detection in detections:
            bbox = detection.get("bbox_xyxy") or []
            if len(bbox) != 4:
                continue
            grouped[image_id].append(
                {
                    "class_id": int(detection["class_id"]),
                    "confidence": float(detection["confidence"]),
                    "bbox_xyxy": [float(value) for value in bbox],
                }
            )
    return grouped


def _match_image(baseline: list[dict[str, Any]], current: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[tuple[int, float, int, int]] = []
    for baseline_index, baseline_box in enumerate(baseline):
        for current_index, current_box in enumerate(current):
            iou = box_iou_xyxy(baseline_box["bbox_xyxy"], current_box["bbox_xyxy"])
            same_class = 1 if baseline_box["class_id"] == current_box["class_id"] else 0
            candidates.append((same_class, iou, baseline_index, current_index))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    used_baseline: set[int] = set()
    used_current: set[int] = set()
    matched: list[dict[str, Any]] = []
    for _same_class, iou, baseline_index, current_index in candidates:
        if iou <= 0 or baseline_index in used_baseline or current_index in used_current:
            continue
        used_baseline.add(baseline_index)
        used_current.add(current_index)
        matched.append(
            {
                "iou": iou,
                "baseline_class_id": baseline[baseline_index]["class_id"],
                "current_class_id": current[current_index]["class_id"],
            }
        )
    return matched


def _mean_confidence(boxes: list[dict[str, Any]]) -> float | None:
    if not boxes:
        return None
    return round(sum(box["confidence"] for box in boxes) / len(boxes), 6)


def _finding_key(finding: Finding) -> str:
    evidence = ",".join(ref.id for ref in finding.evidence_refs)
    return f"{finding.title}|{evidence}"


def _finding_changes(baseline: list[Finding], current: list[Finding]) -> list[dict[str, str]]:
    baseline_map = {_finding_key(item): item for item in baseline}
    current_map = {_finding_key(item): item for item in current}
    changes: list[dict[str, str]] = []
    for key in sorted(set(baseline_map) | set(current_map)):
        before = baseline_map.get(key)
        after = current_map.get(key)
        if before is None and after is not None:
            changes.append(
                {
                    "change": "NEW",
                    "title": after.title,
                    "baseline_severity": "",
                    "current_severity": after.severity.value,
                }
            )
        elif after is None and before is not None:
            changes.append(
                {
                    "change": "CLEARED",
                    "title": before.title,
                    "baseline_severity": before.severity.value,
                    "current_severity": "",
                }
            )
        elif before is not None and after is not None and before.severity != after.severity:
            changes.append(
                {
                    "change": "SEVERITY_CHANGE",
                    "title": after.title,
                    "baseline_severity": before.severity.value,
                    "current_severity": after.severity.value,
                }
            )
        elif before is not None and after is not None:
            changes.append(
                {
                    "change": "UNCHANGED",
                    "title": after.title,
                    "baseline_severity": before.severity.value,
                    "current_severity": after.severity.value,
                }
            )
    return changes


def _has_material_change(detection_metrics: dict[str, Any], finding_changes: list[dict[str, str]]) -> bool:
    if detection_metrics["detection_count_delta"] != 0:
        return True
    if detection_metrics["class_changes"]:
        return True
    confidence_delta = detection_metrics["mean_confidence_delta"]
    if confidence_delta not in (None, 0, 0.0):
        return True
    mean_iou = detection_metrics["mean_iou"]
    if mean_iou is not None and mean_iou < 1:
        return True
    return any(item["change"] != "UNCHANGED" for item in finding_changes)
