from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.services.coco_parser import CocoDatasetParser, DatasetIssue, DatasetProfile


@dataclass
class GeneratedEvidence:
    sample_id: str
    metric: str
    expected_value: str | None
    observed_value: str | None
    reference: str | None


@dataclass
class GeneratedFinding:
    category: str
    severity: str
    status: str
    title: str
    description: str
    method: str
    observed_value: str
    threshold: str
    confidence_note: str
    limitations: str
    remediation: str
    affected_sample: str | None
    evidence: list[GeneratedEvidence]


def _finding(issue: DatasetIssue, severity: str, remediation: str, method: str = "Deterministic COCO validation") -> GeneratedFinding:
    severity = "CRITICAL" if severity == "FAIL" else severity
    evidence = GeneratedEvidence(issue.sample_id, issue.code, issue.expected, issue.observed, None)
    return GeneratedFinding(
        category="DATA_INTEGRITY",
        severity=severity,
        status="OPEN",
        title=issue.code.replace("_", " ").title(),
        description=issue.detail,
        method=method,
        observed_value=issue.observed,
        threshold=issue.expected,
        confidence_note="Deterministic rule result; no probabilistic confidence is inferred.",
        limitations="Checks are limited to the supplied COCO metadata and locally available image bytes.",
        remediation=remediation,
        affected_sample=issue.sample_id,
        evidence=[evidence],
    )


def run_data_integrity(source: Path, run_id: str, configuration: dict) -> tuple[DatasetProfile, list[GeneratedFinding]]:
    profile = CocoDatasetParser().parse(source)
    findings: list[GeneratedFinding] = []
    for issue in profile.issues:
        if issue.code == "EMPTY_LABELS":
            findings.append(_finding(issue, "WARNING", "Review whether unannotated images are intentional."))
        elif issue.code == "DUPLICATE_IMAGE":
            findings.append(_finding(issue, "WARNING", "Remove or document exact duplicate samples."))
        elif issue.code == "MISSING_IMAGE":
            findings.append(_finding(issue, "FAIL", "Restore the referenced image or remove the orphaned annotation."))
        elif issue.code == "UNREADABLE_IMAGE":
            findings.append(_finding(issue, "FAIL", "Replace the unreadable image with a verified local copy."))
        else:
            findings.append(_finding(issue, "FAIL", "Correct the COCO annotation and rerun the deterministic validation."))

    class_allowlist = settings.supported_classes
    if class_allowlist:
        for name in profile.class_list:
            if name not in class_allowlist:
                findings.append(_finding(DatasetIssue("UNSUPPORTED_CLASS", name, name, ", ".join(sorted(class_allowlist)), "Class is outside the configured class allowlist"), "WARNING", "Map or remove the unsupported class before assurance use."))

    image_by_id = {image.image_id: image for image in profile.images}
    for annotation in profile.annotations:
        image = image_by_id.get(annotation.image_id)
        if not image:
            findings.append(_finding(DatasetIssue("MISSING_IMAGE", annotation.image_id, annotation.image_id, "image record exists", "Annotation references an unknown image"), "FAIL", "Add the referenced image or remove the orphaned annotation."))
            continue
        x, y, width, height = annotation.bbox
        already_reported = any(issue.code == "INVALID_BBOX" and issue.sample_id == annotation.annotation_id and "beyond" in issue.detail for issue in profile.issues)
        if (x + width > image.width or y + height > image.height) and not already_reported:
            findings.append(_finding(DatasetIssue("INVALID_BBOX", annotation.annotation_id, str(annotation.bbox), f"within {image.width}x{image.height}", "Bounding box extends beyond image boundaries"), "FAIL", "Clip or correct the bounding box coordinates."))
        if width > 0 and height > 0:
            aspect = max(width / height, height / width)
            if aspect > settings.bbox_max_aspect_ratio:
                findings.append(_finding(DatasetIssue("EXTREME_BBOX_ASPECT", annotation.annotation_id, f"{aspect:.2f}", f"<= {settings.bbox_max_aspect_ratio:g}", "Bounding box aspect ratio exceeds configured review threshold"), "WARNING", "Review the annotation for an implausibly thin region."))
            area_ratio = (width * height) / (image.width * image.height) if image.width and image.height else 0
            if area_ratio < settings.bbox_min_area_ratio:
                findings.append(_finding(DatasetIssue("TINY_BBOX", annotation.annotation_id, f"{area_ratio:.6f}", f">= {settings.bbox_min_area_ratio:g}", "Bounding box occupies less than the configured image-area threshold"), "WARNING", "Review tiny objects and the annotation policy."))
            if area_ratio > settings.bbox_max_area_ratio:
                findings.append(_finding(DatasetIssue("LARGE_BBOX", annotation.annotation_id, f"{area_ratio:.4f}", f"<= {settings.bbox_max_area_ratio:g}", "Bounding box occupies more than the configured image-area threshold"), "WARNING", "Review whether the annotation covers the intended object only."))

    for image in profile.images:
        if image.data is None:
            findings.append(_finding(DatasetIssue("MISSING_IMAGE", image.file_name, image.file_name, "readable local image", "COCO image reference has no matching local file"), "FAIL", "Add the missing image to the dataset archive."))
        elif not image.readable:
            findings.append(_finding(DatasetIssue("UNREADABLE_IMAGE", image.file_name, image.error or "unreadable", "valid image bytes", "Referenced image cannot be decoded"), "FAIL", "Replace the corrupt image file."))
        if image.sha256 and any(other.image_id != image.image_id and other.sha256 == image.sha256 for other in profile.images):
            findings.append(_finding(DatasetIssue("DUPLICATE_IMAGE", image.image_id, image.sha256, "unique image SHA-256", "Image bytes exactly match another sample"), "WARNING", "Remove or document the exact duplicate sample.", "Exact duplicate detection using SHA-256"))

    widths = [image.width for image in profile.images if image.width > 0]
    heights = [image.height for image in profile.images if image.height > 0]
    if widths and heights:
        median_width = sorted(widths)[len(widths) // 2]
        median_height = sorted(heights)[len(heights) // 2]
        for image in profile.images:
            if image.width and (image.width > median_width * 3 or image.width * 3 < median_width):
                findings.append(_finding(DatasetIssue("DIMENSION_OUTLIER", image.image_id, f"{image.width}x{image.height}", f"near {median_width}x{median_height}", "Image width is a configured dimension outlier relative to the batch median"), "WARNING", "Confirm whether mixed resolutions are expected."))
            elif image.height and (image.height > median_height * 3 or image.height * 3 < median_height):
                findings.append(_finding(DatasetIssue("DIMENSION_OUTLIER", image.image_id, f"{image.width}x{image.height}", f"near {median_width}x{median_height}", "Image height is a configured dimension outlier relative to the batch median"), "WARNING", "Confirm whether mixed resolutions are expected."))

    frequencies = {name: count for name, count in profile.class_frequencies.items() if name}
    total_labels = sum(frequencies.values())
    if total_labels and frequencies:
        dominant, dominant_count = max(frequencies.items(), key=lambda item: item[1])
        minority_count = min(frequencies.values())
        share = dominant_count / total_labels
        if len(frequencies) > 1 and (share >= 0.9 or (minority_count > 0 and dominant_count / minority_count >= 10)):
            findings.append(_finding(DatasetIssue("CLASS_IMBALANCE", dominant, f"{share:.2f}", "< 0.90 share and < 10:1 ratio", "Class frequencies are highly imbalanced"), "WARNING", "Review sampling or class mapping before using the dataset for comparison."))
        for name, count in frequencies.items():
            if not name.strip() or name == "UNKNOWN":
                findings.append(_finding(DatasetIssue("LABEL_ANOMALY", name or "empty", name or "empty", "named COCO category", "Annotation uses an empty or unknown class label"), "WARNING", "Correct the category table and annotation class identifiers."))

    scenario = str(configuration.get("scenario", "NONE"))
    if scenario == "DATA_ANOMALY":
        findings.append(_finding(
            DatasetIssue("EMPTY_LABELS", "controlled-unannotated-sample", "0 annotations", ">= 1 annotation", "Controlled prototype scenario: a current-batch sample is treated as missing annotations."),
            "WARNING",
            "This is a labelled controlled demo condition, not an independent attack detector.",
            "Controlled prototype scenario plus deterministic empty-label rule",
        ))
        findings.append(_finding(
            DatasetIssue("DUPLICATE_IMAGE", "controlled-duplicate-sample", "duplicate SHA-256", "unique image SHA-256", "Controlled prototype scenario: an exact duplicate sample is introduced for demonstration."),
            "WARNING",
            "This is a labelled controlled demo condition, not an independent attack detector.",
            "Controlled prototype scenario plus exact SHA-256 duplicate detection",
        ))

    if not findings:
        findings.append(GeneratedFinding("DATA_INTEGRITY", "INFO", "OPEN", "Dataset Integrity Passed", "All configured deterministic COCO checks passed.", "Deterministic COCO validation and SHA-256 duplicate detection", f"{profile.image_count} images, {profile.annotation_count} annotations", "No validation violations", "Deterministic checks only; absence of findings does not establish model performance.", "Image readability, annotation validity, configured thresholds, and exact duplicate checks were evaluated.", "None", None, []))
    return profile, findings


def profile_summary(profile: DatasetProfile, configuration: dict) -> dict:
    return {
        "image_count": profile.image_count,
        "annotation_count": profile.annotation_count,
        "class_list": profile.class_list,
        "class_frequencies": profile.class_frequencies,
        "resolutions": profile.resolutions,
        "aspect_ratio_distribution": profile.aspect_ratios,
        "empty_label_count": profile.empty_label_count,
        "duplicate_count": profile.duplicate_count,
        "invalid_annotation_count": profile.invalid_annotation_count,
        "sample_coverage": profile.sample_coverage,
        "thresholds": {
            "bbox_max_aspect_ratio": settings.bbox_max_aspect_ratio,
            "bbox_min_area_ratio": settings.bbox_min_area_ratio,
            "bbox_max_area_ratio": settings.bbox_max_area_ratio,
        },
        "configuration": configuration,
    }
