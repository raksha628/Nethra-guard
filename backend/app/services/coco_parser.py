from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.services.hash_service import calculate_sha256


@dataclass
class ImageRecord:
    image_id: str
    file_name: str
    width: int
    height: int
    data: bytes | None
    sha256: str | None = None
    readable: bool = False
    error: str | None = None


@dataclass
class AnnotationRecord:
    annotation_id: str
    image_id: str
    category_id: str
    category_name: str
    bbox: tuple[float, float, float, float]
    raw: dict[str, Any]


@dataclass
class DatasetIssue:
    code: str
    sample_id: str
    observed: str
    expected: str
    detail: str


@dataclass
class DatasetProfile:
    image_count: int
    annotation_count: int
    class_list: list[str]
    class_frequencies: dict[str, int]
    resolutions: dict[str, int]
    aspect_ratios: list[float]
    empty_label_count: int
    duplicate_count: int
    invalid_annotation_count: int
    sample_coverage: float
    images: list[ImageRecord] = field(default_factory=list)
    annotations: list[AnnotationRecord] = field(default_factory=list)
    issues: list[DatasetIssue] = field(default_factory=list)


class CocoDatasetParser:
    def parse(self, source: Path) -> DatasetProfile:
        document, image_bytes = self._read_source(source)
        images = self._parse_images(document, image_bytes, source)
        categories = {str(item.get("id")): str(item.get("name", "")) for item in document.get("categories", []) if isinstance(item, dict)}
        annotations, issues = self._parse_annotations(document, categories)
        self._validate_images(images, image_bytes)
        self._detect_duplicates(images)
        image_by_id = {image.image_id: image for image in images}
        for annotation in annotations:
            image = image_by_id.get(annotation.image_id)
            if image and (annotation.bbox[0] + annotation.bbox[2] > image.width or annotation.bbox[1] + annotation.bbox[3] > image.height):
                issues.append(DatasetIssue("INVALID_BBOX", annotation.annotation_id, str(annotation.bbox), f"within {image.width}x{image.height}", "Bounding box extends beyond image boundaries"))

        annotations_by_image: dict[str, int] = {image.image_id: 0 for image in images}
        for annotation in annotations:
            annotations_by_image[annotation.image_id] = annotations_by_image.get(annotation.image_id, 0) + 1
        for image in images:
            if annotations_by_image.get(image.image_id, 0) == 0:
                issues.append(DatasetIssue("EMPTY_LABELS", image.file_name, "0 annotations", ">= 1 annotation", "Image has no annotations"))

        frequencies: dict[str, int] = {name: 0 for name in categories.values() if name}
        for annotation in annotations:
            frequencies[annotation.category_name] = frequencies.get(annotation.category_name, 0) + 1
        resolutions: dict[str, int] = {}
        aspect_ratios: list[float] = []
        for image in images:
            key = f"{image.width}x{image.height}"
            resolutions[key] = resolutions.get(key, 0) + 1
            if image.height > 0:
                aspect_ratios.append(image.width / image.height)

        readable_count = sum(1 for image in images if image.readable)
        coverage = readable_count / len(images) if images else 0.0
        return DatasetProfile(
            image_count=len(images),
            annotation_count=len(annotations),
            class_list=sorted(frequencies),
            class_frequencies=frequencies,
            resolutions=resolutions,
            aspect_ratios=aspect_ratios,
            empty_label_count=sum(1 for issue in issues if issue.code == "EMPTY_LABELS"),
            duplicate_count=sum(max(0, count - 1) for count in self._hash_counts(images).values()),
            invalid_annotation_count=len([issue for issue in issues if issue.code in {"MALFORMED_ANNOTATION", "INVALID_BBOX"}]),
            sample_coverage=coverage,
            images=images,
            annotations=annotations,
            issues=issues,
        )

    def _read_source(self, source: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
        if source.suffix.lower() != ".zip":
            return json.loads(source.read_text(encoding="utf-8")), {}
        with zipfile.ZipFile(source) as archive:
            members = {}
            for info in archive.infolist():
                if info.is_dir() or not self._is_safe_member(info.filename):
                    continue
                members[self._normalise_name(info.filename)] = archive.read(info)
            json_names = [name for name in members if name.lower().endswith(".json")]
            if not json_names:
                raise ValueError("COCO ZIP does not contain a JSON annotation file")
            preferred = next((name for name in json_names if "annotation" in name.lower()), json_names[0])
            return json.loads(members[preferred].decode("utf-8")), members

    @staticmethod
    def _is_safe_member(name: str) -> bool:
        path = PurePosixPath(name.replace("\\", "/"))
        if not path.parts or path.is_absolute() or ".." in path.parts:
            return False
        return not name.startswith("/") and ":" not in path.parts[0]

    @staticmethod
    def _normalise_name(name: str) -> str:
        return PurePosixPath(name.replace("\\", "/")).as_posix().lstrip("./")

    def _parse_images(self, document: dict[str, Any], image_bytes: dict[str, bytes], source: Path) -> list[ImageRecord]:
        records: list[ImageRecord] = []
        for item in document.get("images", []):
            if not isinstance(item, dict) or "id" not in item or "file_name" not in item:
                continue
            file_name = self._normalise_name(str(item["file_name"]))
            if not self._is_safe_member(file_name):
                records.append(ImageRecord(str(item["id"]), file_name, int(item.get("width", 0)), int(item.get("height", 0)), None, error="unsafe image path rejected"))
                continue
            data = image_bytes.get(file_name)
            if data is None and image_bytes:
                data = image_bytes.get(next((key for key in image_bytes if PurePosixPath(key).name == PurePosixPath(file_name).name and self._is_safe_member(key)), ""))
            if data is None and not image_bytes:
                candidate = (source.parent / file_name).resolve()
                root = source.parent.resolve()
                if candidate.is_file() and (candidate == root or root in candidate.parents):
                    data = candidate.read_bytes()
            records.append(ImageRecord(str(item["id"]), file_name, int(item.get("width", 0)), int(item.get("height", 0)), data))
        return records

    def _parse_annotations(self, document: dict[str, Any], categories: dict[str, str]) -> tuple[list[AnnotationRecord], list[DatasetIssue]]:
        records: list[AnnotationRecord] = []
        issues: list[DatasetIssue] = []
        for item in document.get("annotations", []):
            if not isinstance(item, dict) or not {"id", "image_id", "category_id", "bbox"}.issubset(item):
                issues.append(DatasetIssue("MALFORMED_ANNOTATION", str(item.get("id", "unknown")) if isinstance(item, dict) else "unknown", "missing required field", "id, image_id, category_id, bbox", "COCO annotation is incomplete"))
                continue
            bbox = item["bbox"]
            if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(value, (int, float)) for value in bbox):
                issues.append(DatasetIssue("MALFORMED_ANNOTATION", str(item["id"]), str(bbox), "[x, y, width, height]", "Bounding box is not a numeric four-value list"))
                continue
            record = AnnotationRecord(str(item["id"]), str(item["image_id"]), str(item["category_id"]), categories.get(str(item["category_id"]), "UNKNOWN"), tuple(float(value) for value in bbox), item)
            records.append(record)
            x, y, width, height = record.bbox
            if width <= 0 or height <= 0 or x < 0 or y < 0:
                issues.append(DatasetIssue("INVALID_BBOX", record.annotation_id, str(record.bbox), "x >= 0, y >= 0, width > 0, height > 0", "Bounding box has invalid position or dimensions"))
        return records, issues

    def _validate_images(self, images: list[ImageRecord], image_bytes: dict[str, bytes]) -> None:
        for image in images:
            if image.data is None:
                image.error = "missing image file"
                continue
            try:
                with Image.open(BytesIO(image.data)) as opened:
                    opened.verify()
                with Image.open(BytesIO(image.data)) as opened:
                    opened.load()
                    if image.width <= 0:
                        image.width = opened.width
                    if image.height <= 0:
                        image.height = opened.height
                image.sha256 = calculate_sha256(BytesIO(image.data))
                image.readable = True
            except (UnidentifiedImageError, OSError, ValueError) as exc:
                image.error = f"unreadable image: {exc}"

    @staticmethod
    def _detect_duplicates(images: list[ImageRecord]) -> None:
        seen: dict[str, ImageRecord] = {}
        for image in images:
            if image.sha256 and image.sha256 in seen:
                image.error = image.error or f"exact duplicate of {seen[image.sha256].image_id}"
            elif image.sha256:
                seen[image.sha256] = image

    @staticmethod
    def _hash_counts(images: list[ImageRecord]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for image in images:
            if image.sha256:
                counts[image.sha256] = counts.get(image.sha256, 0) + 1
        return counts
