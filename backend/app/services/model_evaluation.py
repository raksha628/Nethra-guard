import json
from pathlib import Path
from typing import Any
from app.config import DatasetConfig, MODEL_CONFIG
from app.services.model_adapter import NormalizedPrediction
from app.services.dataset_validator import validate_dataset

class EvaluationSummary:
    def __init__(self):
        self.metrics: dict[str, Any] = {}
        self.predictions: list[NormalizedPrediction] = []
        self.evidence: list[Any] = []
        self.semantic_evaluation_supported: bool = False
        self.evaluation_status: str = "not_available"

def _compute_iou(box1, box2):
    # box format: [x1, y1, x2, y2] for predictions
    # Ground truth bbox from COCO is [x, y, w, h] -> need to convert it?
    # No, wait, ensure callers pass unified format.
    # Let's assume both are [x1, y1, x2, y2]
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - inter_area
    if union_area == 0: return 0
    return inter_area / union_area

def evaluate_model_behaviour(
    model_path: Path,
    dataset_config: DatasetConfig,
) -> EvaluationSummary:
    """
    Evaluates the prediction metrics and conditionally the semantic quality
    based on the dataset's stated compatibility.
    """
    summary = EvaluationSummary()
    summary.semantic_evaluation_supported = dataset_config.supports_semantic_evaluation
    
    # Validate the dataset completely
    val_result = validate_dataset(dataset_config)
    summary.evaluation_status = val_result.status
    
    if not dataset_config.supports_semantic_evaluation:
        summary.metrics["semantic"] = {
            "status": "NOT_SUPPORTED",
            "message": "Semantic evaluation is not supported for this dataset.",
            "explanation": "The current dataset is designed for assurance testing and controlled distribution/integrity analysis rather than semantic detector benchmarking."
        }
        return summary
        
    if not val_result.is_valid:
        summary.metrics["semantic"] = {
            "status": "NOT_AVAILABLE",
            "message": "Evaluation dataset is missing or invalid.",
            "errors": val_result.errors
        }
        return summary

    from app.services.model_adapter import select_adapter, EvaluationSample
    
    # Load annotations to get image names
    base_path = Path(dataset_config.path)
    annotations_file = base_path / "annotations" / "instances.json"
    with open(annotations_file, "r") as f:
        coco_data = json.load(f)
        
    image_names = [img["file_name"] for img in coco_data["images"]]
    
    # Run Inference
    adapter = select_adapter(model_path)
    adapter.load(model_path)
    
    samples = [EvaluationSample(sample_id=fname, preprocessing="default") for fname in image_names]
    dataset_images_path = base_path / "images"
    predictions = adapter.run_inference(samples, dataset_images_path=dataset_images_path)

    images_with_detections = len(set([p.sample_id for p in predictions]))
    total_detections = len(predictions)
    
    if total_detections > 0:
        confidences = [p.confidence for p in predictions]
        mean_conf = sum(confidences) / total_detections
        sorted_conf = sorted(confidences)
        median_conf = sorted_conf[total_detections // 2]
        low_conf_count = len([c for c in confidences if c < 0.3])
        high_conf_count = len([c for c in confidences if c >= 0.7])
    else:
        mean_conf = 0.0
        median_conf = 0.0
        low_conf_count = 0
        high_conf_count = 0

    class_distribution = {}
    for p in predictions:
        class_distribution[p.class_name] = class_distribution.get(p.class_name, 0) + 1

    summary.metrics["prediction"] = {
        "images_processed": val_result.image_count if val_result.is_valid else 0,
        "images_with_detections": images_with_detections,
        "total_detections": total_detections,
        "class_distribution": class_distribution,
        "mean_confidence": mean_conf,
        "median_confidence": median_conf,
        "low_confidence_detections": low_conf_count,
        "high_confidence_detections": high_conf_count
    }

    # 2. Ground-Truth Metrics
    if not dataset_config.supports_semantic_evaluation:
        summary.metrics["semantic"] = {
            "status": "NOT_SUPPORTED",
            "message": "Semantic evaluation is not supported for this dataset.",
            "explanation": "The current dataset is designed for assurance testing and controlled distribution/integrity analysis rather than semantic detector benchmarking."
        }
        return summary
        
    if not val_result.is_valid:
        summary.metrics["semantic"] = {
            "status": "NOT_AVAILABLE",
            "message": "Evaluation dataset is missing or invalid.",
            "errors": val_result.errors
        }
        return summary

    # Load annotations
    base_path = Path(dataset_config.path)
    annotations_file = base_path / "annotations" / "instances.json"
    with open(annotations_file, "r") as f:
        coco_data = json.load(f)

    # Map categories: category_id -> target class string
    # E.g., if real dataset has "person", we map it to "person".
    cat_map = {c["id"]: c["name"].lower() for c in coco_data["categories"]}
    
    # Ground truth structure: image_filename -> list of (class_name, bbox_xyxy)
    img_id_to_name = {img["id"]: img["file_name"] for img in coco_data["images"]}
    ground_truths = {img["file_name"]: [] for img in coco_data["images"]}
    
    for ann in coco_data["annotations"]:
        fname = img_id_to_name[ann["image_id"]]
        raw_cname = cat_map.get(ann["category_id"])
        
        # Apply explicit NETRA-Guard mapping to Ground Truth
        cat_id = ann["category_id"]
        mapping = MODEL_CONFIG.class_mapping.get(cat_id)
        if mapping and mapping.status == "mapped":
            cname = mapping.target
        else:
            cname = raw_cname # Keep unmapped class as its raw name
            
        x, y, w, h = ann["bbox"]
        ground_truths[fname].append({
            "class_name": cname,
            "raw_class_name": raw_cname,
            "bbox": [x, y, x + w, y + h],
            "matched": False
        })
        
    def _calculate_ap(preds, gts_dict, iou_thresh):
        import copy
        import numpy as np
        # Deep copy to track matched state
        gts = copy.deepcopy(gts_dict)
        
        # Supported classes mapped
        supported_classes = {m.target for m in MODEL_CONFIG.class_mapping.values() if m.status == 'mapped'}
        
        # Filter and sort ALL predictions
        filtered_preds = [p for p in preds if p.class_name in supported_classes]
        sorted_preds = sorted(filtered_preds, key=lambda x: x.confidence, reverse=True)
        
        total_gt = sum([1 for gt_list in gts.values() for gt in gt_list if gt["class_name"] in supported_classes])
        
        if total_gt == 0:
            return 0.0, 0, 0, 0
            
        tp_array = []
        fp_array = []
        
        tp_count = 0
        fp_count = 0
        
        for p in sorted_preds:
            sample_gts = gts.get(p.sample_id, [])
            best_iou = 0
            best_gt = None
            for gt in sample_gts:
                if not gt["matched"] and gt["class_name"] == p.class_name:
                    iou = _compute_iou(p.bbox, gt["bbox"])
                    if iou > best_iou:
                        best_iou = iou
                        best_gt = gt
                        
            if best_iou >= iou_thresh and best_gt is not None:
                best_gt["matched"] = True
                tp_array.append(1)
                fp_array.append(0)
                tp_count += 1
            else:
                tp_array.append(0)
                fp_array.append(1)
                fp_count += 1
                
        if len(tp_array) == 0:
            return 0.0, tp_count, fp_count, total_gt
            
        tp_cumsum = np.cumsum(tp_array)
        fp_cumsum = np.cumsum(fp_array)
        
        recalls = tp_cumsum / total_gt
        precisions = tp_cumsum / (tp_cumsum + fp_cumsum)
        
        recalls = np.concatenate(([0.0], recalls, [1.0]))
        precisions = np.concatenate(([0.0], precisions, [0.0]))
        
        for i in range(len(precisions) - 1, 0, -1):
            precisions[i - 1] = max(precisions[i - 1], precisions[i])
            
        indices = np.where(recalls[1:] != recalls[:-1])[0] + 1
        ap = np.sum((recalls[indices] - recalls[indices - 1]) * precisions[indices])
        
        fn_count = total_gt - tp_count
        return float(ap), tp_count, fp_count, fn_count

    # Calculate AP for IoU 0.50
    ap50, tp50, fp50, fn50 = _calculate_ap(predictions, ground_truths, 0.50)
    
    # Calculate mAP50-95
    ap_scores = []
    iou_thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    for thresh in iou_thresholds:
        ap, _, _, _ = _calculate_ap(predictions, ground_truths, thresh)
        ap_scores.append(ap)
        
    map50_95 = sum(ap_scores) / len(ap_scores) if ap_scores else 0.0
    
    precision50 = tp50 / (tp50 + fp50) if (tp50 + fp50) > 0 else 0.0
    recall50 = tp50 / (tp50 + fn50) if (tp50 + fn50) > 0 else 0.0
    
    summary.metrics["semantic"] = {
        "status": "SUPPORTED",
        "dataset_hash": val_result.dataset_hash,
        "TP": tp50,
        "FP": fp50,
        "FN": fn50,
        "precision": round(precision50, 4),
        "recall": round(recall50, 4),
        "AP50": round(ap50, 4),
        "mAP50-95": round(map50_95, 4)
    }

    return summary
