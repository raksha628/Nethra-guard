"""COCO JSON dataset integrity checks.

Annotation format tested: COCO JSON only (images, annotations, categories)
with bbox stored as [x, y, width, height].
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any

from PIL import Image, UnidentifiedImageError

from .hashing import canonical_json, sha256_file, sha256_text
from .schemas import (
    EvidenceRef,
    Finding,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    Severity,
    status_from_findings,
)

# Prototype demonstration thresholds, not universal limits.
ASPECT_RATIO_MAX = 8.0
CLASS_IMBALANCE_RATIO = 4.0
RESOLUTION_DEVIATION = 0.5

DETERMINISTIC = "Rule-based / deterministic check"
MODULE_LIMITATION = (
    "Checks are rule-based and cover this COCO JSON fixture only. "
    "They do not detect semantic mislabels or poisoning that preserves file structure."
)


def fingerprint_dataset(dataset_dir: Path) -> str:
    """SHA-256 of annotation bytes plus each image file hash, sorted by name."""
    dataset_dir = dataset_dir.resolve()
    annotations = dataset_dir / "annotations.json"
    images_dir = dataset_dir / "images"
    image_rows: list[dict[str, str]] = []
    if images_dir.is_dir():
        for path in sorted(p for p in images_dir.iterdir() if p.is_file()):
            image_rows.append({"file_name": path.name, "sha256": sha256_file(path)})
    payload = {
        "annotations_sha256": sha256_file(annotations) if annotations.is_file() else None,
        "images": image_rows,
    }
    return sha256_text(canonical_json(payload))


def check_dataset(dataset_dir: Path) -> ModuleResult:
    dataset_dir = dataset_dir.resolve()
    findings: list[Finding] = []
    annotations_path = dataset_dir / "annotations.json"
    images_dir = dataset_dir / "images"

    payload, parse_findings = _load_coco(annotations_path)
    if payload is None:
        return ModuleResult(
            module=ModuleName.data_integrity,
            status=ModuleStatus.FAIL,
            metrics={
                "annotation_format": "coco",
                "dataset_hash": _safe_fingerprint(dataset_dir),
                "certainty": DETERMINISTIC,
                "limitations": MODULE_LIMITATION,
                "thresholds": _threshold_metrics(),
            },
            findings=parse_findings,
        )

    images = payload["images"]
    annotations = payload["annotations"]
    categories = payload["categories"]
    category_ids, category_names = _category_index(categories, findings)

    decoded: dict[Any, tuple[int, int]] = {}
    file_hashes: dict[str, str] = {}
    readable_rows: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    seen_names: set[str] = set()

    for image in images:
        if not isinstance(image, dict) or "id" not in image or "file_name" not in image:
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Malformed annotations",
                    "each image needs id and file_name",
                    "missing id or file_name",
                    "id and file_name are required",
                    [],
                    "The image record was skipped because it is not valid COCO.",
                )
            )
            continue
        image_id = image["id"]
        file_name = image["file_name"]
        if not isinstance(file_name, str) or image_id in seen_ids or file_name in seen_names:
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Malformed annotations",
                    "image id and file_name must be unique strings",
                    f"id={image_id} file_name={file_name}",
                    "unique id and file_name",
                    [_evidence(f"image-{image_id}", str(file_name), None, "image_record")],
                    "Duplicate or invalid image identities were not decoded.",
                )
            )
            continue
        seen_ids.add(image_id)
        seen_names.add(file_name)

        if not _positive_int(image.get("width")) or not _positive_int(image.get("height")):
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Malformed annotations",
                    "image width and height must be positive integers",
                    f"width={image.get('width')} height={image.get('height')}",
                    "positive width and height",
                    [_evidence(f"image-{image_id}", file_name, None, "image_record")],
                    "Bounds checks need a declared image size.",
                )
            )

        resolved = _resolve_sample(images_dir, file_name)
        if resolved is None:
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Annotation path is not allowed",
                    "file_name must stay inside the dataset images directory",
                    file_name,
                    "relative path inside images/",
                    [_evidence(f"path-{file_name}", file_name, None, "rejected_path")],
                    "The path was rejected before the file was read.",
                )
            )
            continue
        if not resolved.is_file():
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Missing image file",
                    f"{DETERMINISTIC}. The COCO file_name must point at a file in images/.",
                    "missing",
                    "file must exist and be readable",
                    [_evidence(f"missing-{file_name}", file_name, None, "missing_image")],
                    "A missing file is a structural dataset failure. It is not by itself evidence of poisoning.",
                )
            )
            continue

        try:
            with Image.open(resolved) as handle:
                handle.load()
                width, height = handle.size
        except (OSError, UnidentifiedImageError, ValueError):
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Corrupt or unreadable image",
                    f"{DETERMINISTIC}. Pillow must decode the file.",
                    "unreadable",
                    "file must decode as an image",
                    [_evidence(f"corrupt-{file_name}", file_name, sha256_file(resolved), "corrupt_image")],
                    "Decode failure does not explain why the bytes are invalid.",
                )
            )
            continue

        file_hash = sha256_file(resolved)
        file_hashes[file_name] = file_hash
        decoded[image_id] = (width, height)
        readable_rows.append(
            {"file_name": file_name, "width": width, "height": height, "sha256": file_hash}
        )
        declared_w, declared_h = image.get("width"), image.get("height")
        if declared_w != width or declared_h != height:
            findings.append(
                _finding(
                    Severity.MEDIUM,
                    "Declared image size does not match decoded image",
                    f"{DETERMINISTIC}. Compare COCO width/height with Pillow size.",
                    f"declared={declared_w}x{declared_h} decoded={width}x{height}",
                    "declared size equals decoded size",
                    [_evidence(f"size-{file_name}", file_name, file_hash, "image_size")],
                    "The decoded size is used for box bounds when both are available.",
                )
            )

    annotated_ids: set[Any] = set()
    class_counts: dict[str, int] = {}
    for annotation in annotations:
        if not isinstance(annotation, dict):
            findings.append(_malformed_annotation("annotation is not an object", "invalid annotation"))
            continue
        image_id = annotation.get("image_id")
        category_id = annotation.get("category_id")
        bbox = annotation.get("bbox")
        sample_name = _file_name_for(images, image_id)
        if image_id not in seen_ids:
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Annotation references unknown image",
                    f"{DETERMINISTIC}. image_id must match an image record.",
                    str(image_id),
                    "image_id exists in images",
                    [_evidence(f"unknown-image-{image_id}", sample_name or str(image_id), None, "annotation")],
                    "The annotation was not checked for box geometry.",
                )
            )
            continue
        annotated_ids.add(image_id)
        if category_id not in category_ids:
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Invalid class id",
                    f"{DETERMINISTIC}. category_id must exist in categories.",
                    str(category_id),
                    f"category id in {sorted(category_ids, key=lambda value: str(value))}",
                    [_evidence(f"class-{image_id}-{category_id}", sample_name or str(image_id), file_hashes.get(sample_name or ""), "annotation")],
                    "An unknown class id is a structural label error. It does not prove the box is malicious.",
                )
            )
        else:
            name = category_names.get(category_id, str(category_id))
            class_counts[name] = class_counts.get(name, 0) + 1

        findings.extend(
            _check_bbox(
                annotation,
                bbox,
                decoded.get(image_id),
                _declared_size(images, image_id),
                sample_name,
                file_hashes.get(sample_name or ""),
            )
        )

    for image in images:
        if isinstance(image, dict) and image.get("id") in decoded and image.get("id") not in annotated_ids:
            file_name = str(image.get("file_name"))
            findings.append(
                _finding(
                    Severity.LOW,
                    "Image has no annotations",
                    f"{DETERMINISTIC}. Every listed image is expected to have at least one box in this demo.",
                    "0",
                    "at least 1 annotation",
                    [_evidence(f"empty-{file_name}", file_name, file_hashes.get(file_name), "image")],
                    "Some production datasets allow unlabeled images. This demo treats an empty image as a warning.",
                )
            )

    findings.extend(_duplicate_findings(file_hashes))
    findings.extend(_imbalance_findings(class_counts))
    findings.extend(_resolution_findings(readable_rows))

    readable_rows.sort(key=lambda row: row["file_name"])
    metrics = {
        "annotation_format": "coco",
        "dataset_hash": fingerprint_dataset(dataset_dir),
        "declared_image_count": len([image for image in images if isinstance(image, dict)]),
        "readable_image_count": len(readable_rows),
        "annotation_count": len([item for item in annotations if isinstance(item, dict)]),
        "class_counts": class_counts,
        "images": readable_rows,
        "duplicate_group_count": len(_duplicate_groups(file_hashes)),
        "certainty": DETERMINISTIC,
        "limitations": MODULE_LIMITATION,
        "thresholds": _threshold_metrics(),
    }
    return ModuleResult(
        module=ModuleName.data_integrity,
        status=status_from_findings(findings),
        metrics=metrics,
        findings=sorted(findings, key=lambda item: (item.title, item.observed_value, item.evidence_refs[0].sample_id if item.evidence_refs else "")),
    )


def _load_coco(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    if not path.is_file():
        return None, [
            _finding(
                Severity.CRITICAL,
                "Malformed annotations",
                f"{DETERMINISTIC}. annotations.json must exist.",
                "annotations.json missing",
                "COCO JSON file present",
                [],
                "No image checks ran because the annotation file is missing.",
            )
        ]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [
            _finding(
                Severity.CRITICAL,
                "Malformed annotations",
                f"{DETERMINISTIC}. annotations.json must be valid JSON.",
                str(exc.msg),
                "valid JSON",
                [],
                "Parsing stopped at the first JSON error.",
            )
        ]
    if not isinstance(payload, dict) or any(key not in payload for key in ("images", "annotations", "categories")):
        return None, [
            _finding(
                Severity.CRITICAL,
                "Malformed annotations",
                f"{DETERMINISTIC}. COCO JSON needs images, annotations, and categories.",
                "missing required keys",
                "images, annotations, categories",
                [],
                "Other COCO fields are ignored. YOLO labels are not parsed.",
            )
        ]
    if not all(isinstance(payload[key], list) for key in ("images", "annotations", "categories")):
        return None, [
            _finding(
                Severity.CRITICAL,
                "Malformed annotations",
                f"{DETERMINISTIC}. images, annotations, and categories must be arrays.",
                "required keys are not arrays",
                "JSON arrays",
                [],
                "The file was not interpreted as a dataset.",
            )
        ]
    return payload, []


def _category_index(categories: list[Any], findings: list[Finding]) -> tuple[set[Any], dict[Any, str]]:
    ids: set[Any] = set()
    names: dict[Any, str] = {}
    for category in categories:
        if not isinstance(category, dict) or "id" not in category:
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Malformed annotations",
                    f"{DETERMINISTIC}. Each category needs an id.",
                    "invalid category",
                    "category id",
                    [],
                    "Class checks ignore categories that have no id.",
                )
            )
            continue
        ids.add(category["id"])
        names[category["id"]] = str(category.get("name", category["id"]))
    return ids, names


def _check_bbox(
    annotation: dict[str, Any],
    bbox: Any,
    decoded_size: tuple[int, int] | None,
    declared_size: tuple[int, int] | None,
    sample_name: str | None,
    file_hash: str | None,
) -> list[Finding]:
    sample = sample_name or str(annotation.get("image_id"))
    evidence = [_evidence(f"bbox-{sample}-{annotation.get('id', 'na')}", sample, file_hash, "bounding_box")]
    if not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_number(value) for value in bbox):
        return [
            _finding(
                Severity.CRITICAL,
                "Malformed annotations",
                f"{DETERMINISTIC}. bbox must be [x, y, width, height].",
                str(bbox),
                "[x, y, width, height]",
                evidence,
                "Geometry checks did not run for this annotation.",
            )
        ]
    x, y, width, height = (float(value) for value in bbox)
    if width <= 0 or height <= 0:
        return [
            _finding(
                Severity.CRITICAL,
                "Invalid bounding box dimensions",
                f"{DETERMINISTIC}. Width and height must be greater than zero.",
                str(bbox),
                "width > 0 and height > 0",
                evidence,
                "A non-positive box is invalid COCO geometry, not a semantic judgment.",
            )
        ]
    findings: list[Finding] = []
    size = decoded_size or declared_size
    if size is not None:
        image_w, image_h = size
        if x < 0 or y < 0 or x + width > image_w or y + height > image_h:
            findings.append(
                _finding(
                    Severity.CRITICAL,
                    "Bounding box outside image bounds",
                    f"{DETERMINISTIC}. The COCO box must lie inside the image.",
                    str(bbox),
                    f"x >= 0, y >= 0, x+width <= {image_w}, y+height <= {image_h}",
                    evidence,
                    "Bounds use the decoded image size when the file is readable, otherwise the declared size.",
                )
            )
    aspect = max(width / height, height / width)
    if aspect > ASPECT_RATIO_MAX:
        findings.append(
            _finding(
                Severity.MEDIUM,
                "Extreme bounding box aspect ratio",
                f"{DETERMINISTIC}. Flag max(width/height, height/width) above the prototype threshold.",
                f"{aspect:.4f}",
                str(ASPECT_RATIO_MAX),
                evidence,
                "This prototype threshold is not a universal definition of an implausible object.",
            )
        )
    return findings


def _duplicate_findings(file_hashes: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    for digest, names in _duplicate_groups(file_hashes):
        refs = [
            _evidence(f"exact-duplicate-{name}", name, digest, "exact_duplicate")
            for name in names
        ]
        findings.append(
            _finding(
                Severity.MEDIUM,
                "Exact duplicate images",
                f"{DETERMINISTIC}. Group image files by SHA-256 and flag hashes that occur more than once.",
                str(len(names)),
                "1",
                refs,
                "Exact byte duplicates do not establish malicious poisoning. Repeated captures can share a hash.",
            )
        )
    return findings


def _duplicate_groups(file_hashes: dict[str, str]) -> list[tuple[str, list[str]]]:
    grouped: dict[str, list[str]] = {}
    for name, digest in file_hashes.items():
        grouped.setdefault(digest, []).append(name)
    groups = []
    for digest, names in grouped.items():
        if len(names) > 1:
            groups.append((digest, sorted(names)))
    groups.sort(key=lambda item: item[1][0])
    return groups


def _imbalance_findings(class_counts: dict[str, int]) -> list[Finding]:
    if len(class_counts) < 2:
        return []
    counts = list(class_counts.values())
    ratio = max(counts) / min(counts)
    if ratio < CLASS_IMBALANCE_RATIO:
        return []
    return [
        _finding(
            Severity.MEDIUM,
            "Class imbalance",
            f"{DETERMINISTIC}. Flag max(class count) / min(class count) at or above the prototype threshold.",
            f"{ratio:.4f}",
            str(CLASS_IMBALANCE_RATIO),
            [],
            "Imbalance is a dataset-profile warning. It does not prove labels were manipulated.",
        )
    ]


def _resolution_findings(rows: list[dict[str, Any]]) -> list[Finding]:
    if len(rows) < 4:
        return []
    widths = [row["width"] for row in rows]
    heights = [row["height"] for row in rows]
    median_w = median(widths)
    median_h = median(heights)
    findings: list[Finding] = []
    for row in rows:
        width_off = median_w > 0 and abs(row["width"] - median_w) / median_w > RESOLUTION_DEVIATION
        height_off = median_h > 0 and abs(row["height"] - median_h) / median_h > RESOLUTION_DEVIATION
        if width_off or height_off:
            findings.append(
                _finding(
                    Severity.MEDIUM,
                    "Resolution outlier",
                    f"{DETERMINISTIC}. Flag width or height more than {RESOLUTION_DEVIATION:.0%} from the median.",
                    f"{row['width']}x{row['height']}",
                    f"within {RESOLUTION_DEVIATION:.0%} of median {median_w:.0f}x{median_h:.0f}",
                    [_evidence(f"resolution-{row['file_name']}", row["file_name"], row["sha256"], "image_size")],
                    "This prototype threshold is not a universal resolution policy.",
                )
            )
    return findings


def _resolve_sample(images_dir: Path, file_name: str) -> Path | None:
    path = Path(file_name)
    if path.is_absolute() or ".." in path.parts:
        return None
    if not images_dir.is_dir():
        return images_dir / path.name
    candidate = (images_dir / path).resolve()
    try:
        candidate.relative_to(images_dir.resolve())
    except ValueError:
        return None
    return candidate


def _declared_size(images: list[Any], image_id: Any) -> tuple[int, int] | None:
    for image in images:
        if isinstance(image, dict) and image.get("id") == image_id:
            width, height = image.get("width"), image.get("height")
            if _positive_int(width) and _positive_int(height):
                return int(width), int(height)
    return None


def _file_name_for(images: list[Any], image_id: Any) -> str | None:
    for image in images:
        if isinstance(image, dict) and image.get("id") == image_id and isinstance(image.get("file_name"), str):
            return image["file_name"]
    return None


def _malformed_annotation(observed: str, threshold: str) -> Finding:
    return _finding(
        Severity.CRITICAL,
        "Malformed annotations",
        f"{DETERMINISTIC}. Each annotation needs image_id, category_id, and bbox.",
        observed,
        threshold,
        [],
        "The annotation was not used for geometry checks.",
    )


def _finding(
    severity: Severity,
    title: str,
    method: str,
    observed_value: str,
    threshold: str,
    evidence_refs: list[EvidenceRef],
    limitations: str,
) -> Finding:
    return Finding(
        severity=severity,
        title=title,
        method=method,
        observed_value=observed_value,
        threshold=threshold,
        evidence_refs=evidence_refs,
        limitations=limitations,
    )


def _evidence(evidence_id: str, sample_id: str, file_hash: str | None, evidence_type: str) -> EvidenceRef:
    return EvidenceRef(
        id=evidence_id,
        sample_id=sample_id,
        file_hash=file_hash or None,
        evidence_type=evidence_type,
    )


def _threshold_metrics() -> dict[str, Any]:
    return {
        "duplicate_max_per_hash": 1,
        "aspect_ratio_max": ASPECT_RATIO_MAX,
        "class_imbalance_ratio": CLASS_IMBALANCE_RATIO,
        "resolution_deviation": RESOLUTION_DEVIATION,
        "note": "Prototype demonstration thresholds, not universal limits.",
    }


def _safe_fingerprint(dataset_dir: Path) -> str | None:
    try:
        return fingerprint_dataset(dataset_dir)
    except OSError:
        return None


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
