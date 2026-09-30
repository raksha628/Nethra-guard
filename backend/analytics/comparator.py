"""Compare two assurance runs when their inputs match.

Deltas are omitted when the dataset hash, model hash, preprocessing, or
configuration differ. Matched boxes use bbox_xyxy and greedy IoU, preferring
the same class. Precision, recall, and mAP are not reported.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from assurance.hashing import canonical_json
from assurance.inference import SIMULATED_LIMITATION
from assurance.schemas import (
    EvidenceRef,
    Finding,
    ImageDetections,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    Severity,
    status_from_findings,
)

IOU_MATCH_THRESHOLD = 0.5
COMPARATOR_LIMITATION = (
    "Detection deltas describe the normalized box contract. "
    "When simulated is true, the same image id returns the same box from the demo adapter, "
    "so a change does not prove prediction drift. "
    "Precision, recall, and mAP are not computed."
)
NOT_COMPARABLE_REASON = (
    "Runs are not comparable because dataset, model, preprocessing, or configuration differ. "
    "Detection deltas were omitted."
)


class SourcedFinding(BaseModel):
    module: str
    finding: Finding


class RunSnapshot(BaseModel):
    run_id: str
    dataset_hash: str
    model_hash: str
    preprocessing: dict[str, Any]
    config: dict[str, Any]
    detections: list[ImageDetections] = Field(default_factory=list)
    findings: list[SourcedFinding] = Field(default_factory=list)
    simulated: bool = False


def compare_runs(baseline: RunSnapshot, current: RunSnapshot) -> ModuleResult:
    mismatched = _mismatched_fields(baseline, current)
    if mismatched:
        return ModuleResult(
            module=ModuleName.comparator,
            status=ModuleStatus.NOT_RUN,
            metrics={
                "comparable": False,
                "reason": NOT_COMPARABLE_REASON,
                "mismatched_fields": mismatched,
                "baseline_run_id": baseline.run_id,
                "current_run_id": current.run_id,
                "simulated": baseline.simulated or current.simulated,
            },
            findings=[],
        )

    matches, class_changes, matched_ious = _match_all(baseline.detections, current.detections)
    baseline_count = _detection_count(baseline.detections)
    current_count = _detection_count(current.detections)
    baseline_confidence = _mean_confidence(baseline.detections)
    current_confidence = _mean_confidence(current.detections)
    confidence_delta = None
    if baseline_confidence is not None and current_confidence is not None:
        confidence_delta = round(current_confidence - baseline_confidence, 6)
    mean_iou = round(sum(matched_ious) / len(matched_ious), 6) if matched_ious else None
    finding_changes = _finding_changes(baseline.findings, current.findings)
    simulated = baseline.simulated or current.simulated
    metrics: dict[str, Any] = {
        "comparable": True,
        "baseline_run_id": baseline.run_id,
        "current_run_id": current.run_id,
        "simulated": simulated,
        "detection_count_baseline": baseline_count,
        "detection_count_current": current_count,
        "detection_count_delta": current_count - baseline_count,
        "mean_confidence_baseline": baseline_confidence,
        "mean_confidence_current": current_confidence,
        "mean_confidence_delta": confidence_delta,
        "class_change_count": class_changes,
        "mean_iou": mean_iou,
        "matched_count": len(matched_ious),
        "matches": matches,
        "finding_changes": finding_changes,
        "limitations": _limitations(simulated),
    }
    findings: list[Finding] = []
    if _regressed(metrics, finding_changes):
        findings.append(
            Finding(
                severity=Severity.MEDIUM,
                title="Comparable runs differ",
                method=(
                    "Greedy IoU matching on bbox_xyxy, preferring the same class_id. "
                    f"A match requires IoU of at least {IOU_MATCH_THRESHOLD:.2f}. "
                    "Prototype demonstration rule, not a deployment limit."
                ),
                observed_value=_observed(metrics),
                threshold="no detection, class, confidence, or finding change",
                evidence_refs=_evidence(matches, finding_changes),
                limitations=_limitations(simulated),
            )
        )
    return ModuleResult(
        module=ModuleName.comparator,
        status=status_from_findings(findings),
        metrics=metrics,
        findings=findings,
    )


def findings_from_modules(modules: list[ModuleResult]) -> list[SourcedFinding]:
    sourced: list[SourcedFinding] = []
    for module in modules:
        for finding in module.findings:
            sourced.append(SourcedFinding(module=module.module.value, finding=finding))
    return sourced


def _mismatched_fields(baseline: RunSnapshot, current: RunSnapshot) -> list[str]:
    fields: list[str] = []
    if baseline.dataset_hash != current.dataset_hash:
        fields.append("dataset_hash")
    if baseline.model_hash != current.model_hash:
        fields.append("model_hash")
    if canonical_json(baseline.preprocessing) != canonical_json(current.preprocessing):
        fields.append("preprocessing")
    if canonical_json(baseline.config) != canonical_json(current.config):
        fields.append("config")
    return fields


def _match_all(
    baseline: list[ImageDetections],
    current: list[ImageDetections],
) -> tuple[list[dict[str, Any]], int, list[float]]:
    baseline_by_id = {item.image_id: item.detections for item in baseline}
    current_by_id = {item.image_id: item.detections for item in current}
    class_changes = 0
    ious: list[float] = []
    rows: list[dict[str, Any]] = []
    for image_id in sorted(set(baseline_by_id) | set(current_by_id)):
        pairs = _match_image(
            baseline_by_id.get(image_id, []),
            current_by_id.get(image_id, []),
        )
        for pair in pairs:
            pair["image_id"] = image_id
            if pair["matched"]:
                ious.append(pair["iou"])
                if pair["class_changed"]:
                    class_changes += 1
            rows.append(pair)
    return rows, class_changes, ious


def _match_image(baseline: list, current: list) -> list[dict[str, Any]]:
    candidates: list[tuple[int, float, int, int]] = []
    for baseline_index, before in enumerate(baseline):
        for current_index, after in enumerate(current):
            score = _iou(before.bbox_xyxy, after.bbox_xyxy)
            same = 1 if before.class_id == after.class_id else 0
            candidates.append((same, score, baseline_index, current_index))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    used_baseline: set[int] = set()
    used_current: set[int] = set()
    chosen: dict[int, tuple[int, float]] = {}
    for same, score, baseline_index, current_index in candidates:
        if baseline_index in used_baseline or current_index in used_current:
            continue
        if score < IOU_MATCH_THRESHOLD:
            continue
        used_baseline.add(baseline_index)
        used_current.add(current_index)
        chosen[baseline_index] = (current_index, score)

    rows: list[dict[str, Any]] = []
    for baseline_index, before in enumerate(baseline):
        if baseline_index not in chosen:
            rows.append(
                {
                    "matched": False,
                    "side": "baseline_only",
                    "class_id": before.class_id,
                    "confidence": before.confidence,
                    "bbox_xyxy": list(before.bbox_xyxy),
                    "iou": None,
                    "class_changed": False,
                }
            )
            continue
        current_index, score = chosen[baseline_index]
        after = current[current_index]
        rows.append(
            {
                "matched": True,
                "class_id_baseline": before.class_id,
                "class_id_current": after.class_id,
                "confidence_baseline": before.confidence,
                "confidence_current": after.confidence,
                "iou": round(score, 6),
                "class_changed": before.class_id != after.class_id,
            }
        )
    for current_index, after in enumerate(current):
        if current_index in used_current:
            continue
        rows.append(
            {
                "matched": False,
                "side": "current_only",
                "class_id": after.class_id,
                "confidence": after.confidence,
                "bbox_xyxy": list(after.bbox_xyxy),
                "iou": None,
                "class_changed": False,
            }
        )
    return rows


def _iou(left: list[int] | list[float], right: list[int] | list[float]) -> float:
    x1 = max(float(left[0]), float(right[0]))
    y1 = max(float(left[1]), float(right[1]))
    x2 = min(float(left[2]), float(right[2]))
    y2 = min(float(left[3]), float(right[3]))
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    left_area = max(0.0, float(left[2]) - float(left[0])) * max(0.0, float(left[3]) - float(left[1]))
    right_area = max(0.0, float(right[2]) - float(right[0])) * max(0.0, float(right[3]) - float(right[1]))
    union = left_area + right_area - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def _detection_count(images: list[ImageDetections]) -> int:
    return sum(len(item.detections) for item in images)


def _mean_confidence(images: list[ImageDetections]) -> float | None:
    values = [detection.confidence for item in images for detection in item.detections]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _finding_key(item: SourcedFinding) -> tuple[str, str, tuple[str, ...]]:
    samples = tuple(sorted(ref.sample_id for ref in item.finding.evidence_refs))
    return (item.module, item.finding.title, samples)


def _finding_changes(
    baseline: list[SourcedFinding],
    current: list[SourcedFinding],
) -> list[dict[str, Any]]:
    before = {_finding_key(item): item for item in baseline}
    after = {_finding_key(item): item for item in current}
    changes: list[dict[str, Any]] = []
    for key in sorted(set(before) | set(after)):
        left = before.get(key)
        right = after.get(key)
        if left is None and right is not None:
            changes.append(_change("NEW", right, None, right))
        elif right is None and left is not None:
            changes.append(_change("CLEARED", left, left, None))
        elif left is not None and right is not None:
            if left.finding.severity != right.finding.severity:
                changes.append(_change("SEVERITY_CHANGE", right, left, right))
            else:
                changes.append(_change("UNCHANGED", right, left, right))
    return changes


def _change(
    kind: str,
    identity: SourcedFinding,
    baseline: SourcedFinding | None,
    current: SourcedFinding | None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "type": kind,
        "module": identity.module,
        "title": identity.finding.title,
    }
    if baseline is not None:
        row["baseline_severity"] = baseline.finding.severity.value
    if current is not None:
        row["current_severity"] = current.finding.severity.value
    return row


def _regressed(metrics: dict[str, Any], finding_changes: list[dict[str, Any]]) -> bool:
    if metrics["detection_count_delta"] != 0 or metrics["class_change_count"] != 0:
        return True
    confidence_delta = metrics["mean_confidence_delta"]
    if confidence_delta is not None and abs(confidence_delta) > 1e-9:
        return True
    mean_iou = metrics["mean_iou"]
    if mean_iou is not None and mean_iou < 1 - 1e-9:
        return True
    return any(item["type"] in {"NEW", "CLEARED", "SEVERITY_CHANGE"} for item in finding_changes)


def _observed(metrics: dict[str, Any]) -> str:
    iou = metrics["mean_iou"]
    iou_text = "none" if iou is None else f"{iou:.6f}"
    confidence = metrics["mean_confidence_delta"]
    confidence_text = "none" if confidence is None else f"{confidence:.6f}"
    return (
        f"count delta={metrics['detection_count_delta']}, "
        f"class changes={metrics['class_change_count']}, "
        f"confidence delta={confidence_text}, "
        f"mean IoU={iou_text}"
    )


def _evidence(
    matches: list[dict[str, Any]],
    finding_changes: list[dict[str, Any]],
) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []
    seen: set[str] = set()
    for row in matches:
        image_id = row.get("image_id")
        if not image_id or image_id in seen:
            continue
        changed = (not row["matched"]) or row["class_changed"] or (
            row["matched"] and row["iou"] is not None and row["iou"] < 1 - 1e-9
        )
        if not changed:
            continue
        seen.add(image_id)
        refs.append(
            EvidenceRef(
                id=f"compare-{image_id}",
                sample_id=image_id,
                file_hash=None,
                evidence_type="detection_delta",
            )
        )
    if refs:
        return refs
    for change in finding_changes:
        if change["type"] == "UNCHANGED":
            continue
        title = change["title"]
        if title in seen:
            continue
        seen.add(title)
        refs.append(
            EvidenceRef(
                id=f"compare-{title}",
                sample_id=title,
                file_hash=None,
                evidence_type="finding_delta",
            )
        )
    return refs


def _limitations(simulated: bool) -> str:
    if simulated:
        return f"{SIMULATED_LIMITATION} {COMPARATOR_LIMITATION}"
    return COMPARATOR_LIMITATION
