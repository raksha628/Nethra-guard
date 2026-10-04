import pytest
import json
from pathlib import Path
from app.services.dataset_validator import validate_dataset
from app.config import DatasetConfig

@pytest.fixture
def temp_dataset_dir(tmp_path):
    dataset_dir = tmp_path / "model_evaluation"
    images_dir = dataset_dir / "images"
    annotations_dir = dataset_dir / "annotations"
    images_dir.mkdir(parents=True)
    annotations_dir.mkdir(parents=True)
    
    # create dummy image
    img_path = images_dir / "test.jpg"
    img_path.write_bytes(b"dummy_image_data")
    
    # create valid coco
    coco_data = {
        "images": [{"id": 1, "file_name": "test.jpg", "width": 640, "height": 640}],
        "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [10, 10, 50, 50], "area": 2500, "iscrowd": 0}],
        "categories": [{"id": 1, "name": "person"}]
    }
    
    with open(annotations_dir / "instances.json", "w") as f:
        json.dump(coco_data, f)
        
    # metadata
    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump({"dataset_name": "test"}, f)
        
    return dataset_dir

def test_valid_coco_dataset_passes(temp_dataset_dir):
    config = DatasetConfig(
        name="Test",
        purpose="Testing",
        path=str(temp_dataset_dir),
        annotation_format="COCO",
        class_names=["person"],
        expected_image_format="JPEG",
        supports_semantic_evaluation=True,
        source_metadata="test"
    )
    result = validate_dataset(config)
    assert result.is_valid is True
    assert result.status == "valid"
    assert result.image_count == 1
    assert result.dataset_hash is not None

def test_missing_image_detected(temp_dataset_dir):
    # remove the image
    (temp_dataset_dir / "images" / "test.jpg").unlink()
    config = DatasetConfig(
        name="Test", purpose="Testing", path=str(temp_dataset_dir),
        annotation_format="COCO", class_names=["person"],
        expected_image_format="JPEG", supports_semantic_evaluation=True, source_metadata="test"
    )
    result = validate_dataset(config)
    assert result.is_valid is False
    assert any("missing" in err and "test.jpg" in err for err in result.errors)

def test_invalid_bbox_detected(temp_dataset_dir):
    with open(temp_dataset_dir / "annotations" / "instances.json", "r") as f:
        data = json.load(f)
    data["annotations"][0]["bbox"] = [10, 10, -5, 50]
    with open(temp_dataset_dir / "annotations" / "instances.json", "w") as f:
        json.dump(data, f)
        
    config = DatasetConfig(
        name="Test", purpose="Testing", path=str(temp_dataset_dir),
        annotation_format="COCO", class_names=["person"],
        expected_image_format="JPEG", supports_semantic_evaluation=True, source_metadata="test"
    )
    result = validate_dataset(config)
    assert result.is_valid is False
    assert any("Invalid bbox dimensions" in err for err in result.errors)

def test_identical_dataset_produces_identical_hash(temp_dataset_dir):
    config = DatasetConfig(
        name="Test", purpose="Testing", path=str(temp_dataset_dir),
        annotation_format="COCO", class_names=["person"],
        expected_image_format="JPEG", supports_semantic_evaluation=True, source_metadata="test"
    )
    result1 = validate_dataset(config)
    result2 = validate_dataset(config)
    assert result1.dataset_hash == result2.dataset_hash
