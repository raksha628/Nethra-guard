import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from app.config import DatasetConfig
from app.services.hash_service import calculate_sha256
import hashlib

@dataclass
class DatasetValidationResult:
    is_valid: bool
    status: str
    errors: list[str]
    dataset_hash: str | None = None
    image_count: int = 0
    annotation_count: int = 0
    categories: list[dict] = None

def validate_dataset(config: DatasetConfig) -> DatasetValidationResult:
    errors = []
    base_path = Path(config.path)
    
    if not base_path.exists():
        errors.append(f"Dataset root directory does not exist: {base_path}")
        return DatasetValidationResult(False, "not_available", errors)
        
    images_dir = base_path / "images"
    if not images_dir.exists():
        errors.append(f"Images directory missing: {images_dir}")
        return DatasetValidationResult(False, "invalid", errors)
        
    annotations_file = base_path / "annotations" / "instances.json"
    if not annotations_file.exists():
        errors.append(f"Annotations file missing: {annotations_file}")
        return DatasetValidationResult(False, "invalid", errors)
        
    metadata_file = base_path / "metadata.json"
    if not metadata_file.exists():
        errors.append(f"Metadata file missing: {metadata_file}")
    
    try:
        with open(annotations_file, "r") as f:
            coco_data = json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse COCO JSON: {str(e)}")
        return DatasetValidationResult(False, "invalid", errors)
        
    if "images" not in coco_data or "annotations" not in coco_data or "categories" not in coco_data:
        errors.append("COCO JSON missing required keys (images, annotations, categories)")
        return DatasetValidationResult(False, "invalid", errors)
        
    images = coco_data["images"]
    if not images:
        errors.append("Dataset contains zero images")
    
    annotations = coco_data["annotations"]
    if not annotations:
        errors.append("Dataset contains zero annotations")
        
    categories = coco_data.get("categories", [])
    
    image_ids = set()
    for img in images:
        if img["id"] in image_ids:
            errors.append(f"Duplicate image ID detected: {img['id']}")
        image_ids.add(img["id"])
        
        img_path = images_dir / img["file_name"]
        if not img_path.exists():
            errors.append(f"Referenced image missing: {img['file_name']}")
            
    ann_ids = set()
    category_ids = {c["id"] for c in categories}
    
    for ann in annotations:
        if ann["id"] in ann_ids:
            errors.append(f"Duplicate annotation ID detected: {ann['id']}")
        ann_ids.add(ann["id"])
        
        if ann["image_id"] not in image_ids:
            errors.append(f"Orphan annotation referenced unknown image_id: {ann['image_id']}")
            
        if ann["category_id"] not in category_ids:
            errors.append(f"Annotation referenced unknown category_id: {ann['category_id']}")
            
        bbox = ann.get("bbox")
        if not bbox or len(bbox) != 4:
            errors.append(f"Malformed bbox in annotation {ann['id']}")
        else:
            _, _, w, h = bbox
            if w <= 0 or h <= 0:
                errors.append(f"Invalid bbox dimensions in annotation {ann['id']}")

    if errors:
        return DatasetValidationResult(False, "invalid", errors)
        
    # Generate fingerprint (Hash)
    hash_payload = hashlib.sha256()
    hash_payload.update(annotations_file.read_bytes())
    if metadata_file.exists():
        hash_payload.update(metadata_file.read_bytes())
        
    # Incorporate valid image list deterministically
    sorted_images = sorted([img["file_name"] for img in images])
    for fname in sorted_images:
        img_path = images_dir / fname
        if img_path.exists():
            hash_payload.update(fname.encode('utf-8'))
            hash_payload.update(str(img_path.stat().st_size).encode('utf-8'))
            
    dataset_hash = hash_payload.hexdigest()
    
    return DatasetValidationResult(
        is_valid=True,
        status="valid",
        errors=[],
        dataset_hash=dataset_hash,
        image_count=len(images),
        annotation_count=len(annotations),
        categories=categories
    )
