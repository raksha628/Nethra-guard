import pytest
from app.services.model_evaluation import evaluate_model_behaviour, _compute_iou
from app.config import DatasetConfig
import json

class MockPrediction:
    def __init__(self, sample_id, class_name, confidence, bbox):
        self.sample_id = sample_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox

def test_compute_iou():
    box1 = [0, 0, 10, 10]
    box2 = [5, 5, 15, 15]
    # intersection: [5, 5, 10, 10] area = 25
    # union: 100 + 100 - 25 = 175
    # iou = 25 / 175 = 1/7 = 0.142857
    assert abs(_compute_iou(box1, box2) - (25 / 175)) < 1e-5

def test_compute_iou_perfect():
    box = [10, 10, 50, 50]
    assert _compute_iou(box, box) == 1.0

def test_compute_iou_disjoint():
    box1 = [0, 0, 10, 10]
    box2 = [20, 20, 30, 30]
    assert _compute_iou(box1, box2) == 0.0

def test_map_calculation_perfect_match(monkeypatch):
    # We will import the internal method by mocking the wrapper or running it directly
    # To test _calculate_ap, we can extract it or mock the dependencies
    from app.services.model_evaluation import evaluate_model_behaviour
    pass

# Instead of complex monkeypatching, I'll extract _calculate_ap to module level temporarily for testing
# Actually I can just test evaluate_model_behaviour with a mocked adapter
import sys
from pathlib import Path

class MockAdapter:
    def __init__(self, predictions):
        self.preds = predictions
    def load(self, path): pass
    def run_inference(self, samples, dataset_images_path):
        return self.preds

def test_map_evaluation(monkeypatch, tmp_path):
    # Setup dummy dataset
    dataset_dir = tmp_path / "model_evaluation"
    (dataset_dir / "images").mkdir(parents=True)
    (dataset_dir / "annotations").mkdir(parents=True)
    
    coco_data = {
        "images": [
            {"id": 1, "file_name": "img1.jpg"},
            {"id": 2, "file_name": "img2.jpg"}
        ],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 100, 100]}, # [0,0,100,100]
            {"id": 2, "image_id": 1, "category_id": 1, "bbox": [50, 50, 50, 50]}, # [50,50,100,100]
            {"id": 3, "image_id": 2, "category_id": 1, "bbox": [10, 10, 20, 20]}  # [10,10,30,30]
        ],
        "categories": [{"id": 1, "name": "person"}]
    }
    with open(dataset_dir / "annotations" / "instances.json", "w") as f:
        json.dump(coco_data, f)
        
    config = DatasetConfig(name="test", path=str(dataset_dir), supports_semantic_evaluation=True, purpose="eval", annotation_format="coco", class_names=["person"], expected_image_format="jpg", source_metadata="{}")
    
    import app.services.model_evaluation
    monkeypatch.setattr(app.config.MODEL_CONFIG, "class_mapping", {1: type("M",(),{"status":"mapped", "target":"person"})()}); monkeypatch.setattr(app.services.model_evaluation, "validate_dataset", lambda c: type("V",(),{"is_valid":True,"status":"ok","dataset_hash":"hash","errors":[],"image_count":2})())
    
    # 1. Perfect predictions
    preds = [
        MockPrediction("img1.jpg", "person", 0.9, [0, 0, 100, 100]),
        MockPrediction("img1.jpg", "person", 0.8, [50, 50, 100, 100]),
        MockPrediction("img2.jpg", "person", 0.95, [10, 10, 30, 30])
    ]
    import app.services.model_adapter; monkeypatch.setattr(app.services.model_adapter, "select_adapter", lambda path: MockAdapter(preds))
    
    summary = evaluate_model_behaviour(Path("dummy.onnx"), config)
    sem = summary.metrics["semantic"]
    assert sem["TP"] == 3
    assert sem["FP"] == 0
    assert sem["FN"] == 0
    assert sem["precision"] == 1.0
    assert sem["recall"] == 1.0
    assert sem["AP50"] == 1.0
    assert sem["mAP50-95"] == 1.0

    # 2. Zero predictions
    import app.services.model_adapter; monkeypatch.setattr(app.services.model_adapter, "select_adapter", lambda path: MockAdapter([]))
    summary = evaluate_model_behaviour(Path("dummy.onnx"), config)
    sem = summary.metrics["semantic"]
    assert sem["TP"] == 0
    assert sem["FP"] == 0
    assert sem["FN"] == 3
    assert sem["precision"] == 0.0
    assert sem["recall"] == 0.0
    assert sem["AP50"] == 0.0

    # 3. One false positive
    preds = [
        MockPrediction("img1.jpg", "person", 0.9, [0, 0, 100, 100]),
        MockPrediction("img1.jpg", "person", 0.8, [50, 50, 100, 100]),
        MockPrediction("img2.jpg", "person", 0.95, [10, 10, 30, 30]),
        MockPrediction("img2.jpg", "person", 0.4, [0, 0, 5, 5]) # FP
    ]
    import app.services.model_adapter; monkeypatch.setattr(app.services.model_adapter, "select_adapter", lambda path: MockAdapter(preds))
    summary = evaluate_model_behaviour(Path("dummy.onnx"), config)
    sem = summary.metrics["semantic"]
    assert sem["TP"] == 3
    assert sem["FP"] == 1
    assert sem["FN"] == 0
    assert sem["precision"] == 0.75 # 3 / 4
    assert sem["recall"] == 1.0
