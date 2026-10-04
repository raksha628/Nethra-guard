import pytest
from pathlib import Path
from app.services.model_evaluation import _compute_iou, evaluate_model_behaviour
from app.config import DatasetConfig

def test_iou_matching_works():
    # perfect match
    box1 = [10, 10, 50, 50]
    box2 = [10, 10, 50, 50]
    assert _compute_iou(box1, box2) == 1.0
    
    # disjoint
    box3 = [100, 100, 150, 150]
    assert _compute_iou(box1, box3) == 0.0
    
    # partial match
    box4 = [30, 30, 70, 70]
    iou = _compute_iou(box1, box4)
    # Area1 = 1600, Area2 = 1600, Inter = 400
    # Union = 3200 - 400 = 2800 -> 400/2800 = 1/7
    assert abs(iou - (1/7)) < 0.01

def test_missing_evaluation_dataset_returns_unavailable():
    config = DatasetConfig(
        name="Empty",
        purpose="Test",
        path="workspace/does_not_exist",
        annotation_format="COCO",
        class_names=["person"],
        expected_image_format="JPEG",
        supports_semantic_evaluation=True,
        source_metadata="test"
    )
    # Don't even need a real model path for this failure path
    summary = evaluate_model_behaviour(Path("dummy.onnx"), config)
    assert summary.metrics["semantic"]["status"] == "NOT_AVAILABLE"
