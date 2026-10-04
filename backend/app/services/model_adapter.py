from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.services.hash_service import calculate_sha256


@dataclass(frozen=True)
class EvaluationSample:
    sample_id: str
    preprocessing: str = "RGB decode; fixed 64x64 nearest-neighbor resize"


@dataclass(frozen=True)
class NormalizedPrediction:
    sample_id: str
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]
    detection_count: int = 1


@dataclass(frozen=True)
class ModelMetadata:
    adapter: str
    format: str
    framework: str
    deterministic_fallback: bool
    preprocessing: str
    details: dict[str, Any]


class ModelAdapter(Protocol):
    def load(self, model_path: Path) -> None: ...
    def validate(self, model_path: Path) -> list[str]: ...
    def run_inference(self, samples: list[EvaluationSample]) -> list[NormalizedPrediction]: ...
    def metadata(self) -> ModelMetadata: ...


FROZEN_EVALUATION_SET = (
    EvaluationSample("fixed-sample-001"),
    EvaluationSample("fixed-sample-002"),
    EvaluationSample("fixed-sample-003"),
)


class DeterministicFallbackAdapter:
    def __init__(self) -> None:
        self.model_path: Path | None = None
        self.model_hash = ""

    def load(self, model_path: Path) -> None:
        self.model_path = model_path
        self.model_hash = calculate_sha256(model_path)

    def validate(self, model_path: Path) -> list[str]:
        if not model_path.is_file():
            return ["model file is not available"]
        if model_path.stat().st_size == 0:
            return ["model file is empty"]
        return []

    def run_inference(self, samples: list[EvaluationSample]) -> list[NormalizedPrediction]:
        if not self.model_hash:
            raise RuntimeError("model must be loaded before inference")
        predictions: list[NormalizedPrediction] = []
        for sample in samples:
            digest = hashlib.sha256(f"{self.model_hash}:{sample.sample_id}:{sample.preprocessing}".encode("utf-8")).digest()
            class_name = f"class-{digest[0] % 3}"
            confidence = round(0.5 + (digest[1] / 255) * 0.49, 4)
            x = round((digest[2] / 255) * 0.35, 4)
            y = round((digest[3] / 255) * 0.35, 4)
            width = round(0.25 + (digest[4] / 255) * 0.35, 4)
            height = round(0.25 + (digest[5] / 255) * 0.35, 4)
            predictions.append(NormalizedPrediction(sample.sample_id, class_name, confidence, (x, y, width, height)))
        return predictions

    def metadata(self) -> ModelMetadata:
        return ModelMetadata("deterministic-fallback", "unknown", "none", True, FROZEN_EVALUATION_SET[0].preprocessing, {"reason": "No compatible runtime was selected for the uploaded artifact"})


class ONNXModelAdapter:
    def __init__(self) -> None:
        self.model_path: Path | None = None
        self.model_hash = ""
        self.session = None
        self.input_name = ""
        self.input_shape = []
        self.input_dtype = ""
        self.output_names = []
        self.output_shapes = []
        self.class_mapping = {
            0: 'person', 1: 'vehicle', 2: 'vehicle', 3: 'vehicle',
            4: 'vehicle', 5: 'vehicle', 6: 'vehicle', 7: 'vehicle',
            8: 'vehicle', 73: 'equipment', 24: 'equipment', 26: 'equipment',
            # Map a few more things just in case
        }

    def load(self, model_path: Path) -> None:
        import onnxruntime as ort
        self.model_path = model_path
        self.model_hash = calculate_sha256(model_path)
        
        try:
            self.session = ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
            inputs = self.session.get_inputs()
            outputs = self.session.get_outputs()
            
            if inputs:
                self.input_name = inputs[0].name
                self.input_shape = inputs[0].shape
                self.input_dtype = inputs[0].type
            
            self.output_names = [out.name for out in outputs]
            self.output_shapes = [out.shape for out in outputs]
            
        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {str(e)}")

    def validate(self, model_path: Path) -> list[str]:
        errors = []
        if not model_path.is_file():
            errors.append("model file is not available")
            return errors
        if model_path.stat().st_size == 0:
            errors.append("model file is empty")
            return errors
            
        try:
            import onnxruntime as ort
            ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
        except Exception as e:
            errors.append(f"Invalid ONNX model format: {str(e)}")
            
        return errors

    def _preprocess(self, image_path: Path):
        from PIL import Image
        import numpy as np
        
        img = Image.open(image_path).convert("RGB")
        orig_w, orig_h = img.size
        
        # YOLO standard 640x640 resize (ignoring aspect ratio for simplicity in this prototype)
        img_resized = img.resize((640, 640))
        img_np = np.array(img_resized, dtype=np.float32) / 255.0
        
        # HWC to CHW
        img_np = np.transpose(img_np, (2, 0, 1))
        # Add batch dimension
        img_tensor = np.expand_dims(img_np, axis=0)
        
        return img_tensor, orig_w, orig_h

    def _postprocess(self, output, orig_w, orig_h, conf_thres=0.01, iou_thres=0.45):
        import numpy as np
        
        # YOLOv8 output: [1, 84, 8400]
        if len(output.shape) != 3 or output.shape[1] < 4:
            return []
            
        pred = output[0].T # (8400, 84)
        
        # Extract boxes and scores
        boxes_xywh = pred[:, :4]
        scores_matrix = pred[:, 4:]
        
        max_scores = np.max(scores_matrix, axis=1)
        class_ids = np.argmax(scores_matrix, axis=1)
        
        keep = max_scores > conf_thres
        boxes_xywh = boxes_xywh[keep]
        max_scores = max_scores[keep]
        class_ids = class_ids[keep]
        
        results = []
        if len(boxes_xywh) == 0:
            return results
            
        # NMS in python without cv2 for simplicity (cv2.dnn.NMSBoxes expects a list of boxes)
        boxes_xyxy = np.empty_like(boxes_xywh)
        boxes_xyxy[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
        boxes_xyxy[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2
        boxes_xyxy[:, 2] = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2
        boxes_xyxy[:, 3] = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2
        
        # Scale back to original image
        scale_w = orig_w / 640.0
        scale_h = orig_h / 640.0
        boxes_xyxy[:, 0] *= scale_w
        boxes_xyxy[:, 2] *= scale_w
        boxes_xyxy[:, 1] *= scale_h
        boxes_xyxy[:, 3] *= scale_h
        
        # Simple NMS
        indices = np.argsort(max_scores)[::-1]
        keep_boxes = []
        
        while len(indices) > 0:
            current = indices[0]
            keep_boxes.append(current)
            if len(indices) == 1:
                break
                
            rest = indices[1:]
            
            box1 = boxes_xyxy[current]
            boxes2 = boxes_xyxy[rest]
            
            x1 = np.maximum(box1[0], boxes2[:, 0])
            y1 = np.maximum(box1[1], boxes2[:, 1])
            x2 = np.minimum(box1[2], boxes2[:, 2])
            y2 = np.minimum(box1[3], boxes2[:, 3])
            
            inter_area = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
            box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
            boxes2_area = (boxes2[:, 2] - boxes2[:, 0]) * (boxes2[:, 3] - boxes2[:, 1])
            
            union_area = box1_area + boxes2_area - inter_area
            iou = inter_area / (union_area + 1e-6)
            
            indices = rest[iou <= iou_thres]
            
        for i in keep_boxes:
            cid = int(class_ids[i])
            # Only keep classes we care about
            if cid in self.class_mapping:
                mapped_name = self.class_mapping[cid]
                # Clip to image bounds
                x1 = max(0.0, float(boxes_xyxy[i, 0]))
                y1 = max(0.0, float(boxes_xyxy[i, 1]))
                x2 = min(float(orig_w), float(boxes_xyxy[i, 2]))
                y2 = min(float(orig_h), float(boxes_xyxy[i, 3]))
                
                if x2 > x1 and y2 > y1:
                    results.append({
                        "class_id": cid,
                        "class_name": mapped_name,
                        "confidence": float(max_scores[i]),
                        "bbox": (x1, y1, x2, y2)
                    })
                
        return results

    def run_inference(self, samples: list[EvaluationSample]) -> list[NormalizedPrediction]:
        if not self.session:
            raise RuntimeError("model must be loaded before inference")
            
        from app.services.file_storage import get_workspace_dir
        
        workspace_dir = get_workspace_dir()
        
        predictions = []
        for sample in samples:
            image_path = workspace_dir / "synthetic_cv" / "evaluation" / "images" / sample.sample_id
            if not image_path.exists():
                # Try clean baseline
                image_path = workspace_dir / "synthetic_cv" / "reference" / "images" / sample.sample_id
                if not image_path.exists():
                    continue
                    
            try:
                img_tensor, orig_w, orig_h = self._preprocess(image_path)
                
                outputs = self.session.run(self.output_names, {self.input_name: img_tensor})
                raw_output = outputs[0]
                
                detections = self._postprocess(raw_output, orig_w, orig_h)
                
                for det in detections:
                    predictions.append(
                        NormalizedPrediction(
                            sample_id=sample.sample_id,
                            class_name=det["class_name"],
                            confidence=round(det["confidence"], 4),
                            bbox=det["bbox"],
                            detection_count=1
                        )
                    )
            except Exception as e:
                print(f"Inference failed for {sample.sample_id}: {e}")
                
        return predictions

    def metadata(self) -> ModelMetadata:
        details = {
            "input_name": self.input_name,
            "input_shape": self.input_shape,
            "input_dtype": str(self.input_dtype),
            "output_names": self.output_names,
            "output_shapes": self.output_shapes,
            "class_mapping": self.class_mapping,
            "preprocessing": "Resize 640x640, RGB, float32 [0,1], CHW",
            "postprocessing": "NMS, threshold=0.01, iou=0.45"
        }
        return ModelMetadata(
            adapter="onnxruntime",
            format="onnx",
            framework="yolov8",
            deterministic_fallback=False,
            preprocessing="Resize 640x640 RGB float32 NCHW",
            details=details
        )


def select_adapter(model_path: Path) -> ModelAdapter:
    if model_path.suffix.lower() == ".onnx":
        return ONNXModelAdapter()
    return DeterministicFallbackAdapter()


def normalize_predictions(predictions: list[NormalizedPrediction]) -> list[dict[str, Any]]:
    return [{"sample_id": item.sample_id, "class": item.class_name, "confidence": item.confidence, "bbox": list(item.bbox), "detection_count": item.detection_count} for item in predictions]


def box_iou(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> float:
    first_x2, first_y2 = first[0] + first[2], first[1] + first[3]
    second_x2, second_y2 = second[0] + second[2], second[1] + second[3]
    intersection = max(0.0, min(first_x2, second_x2) - max(first[0], second[0])) * max(0.0, min(first_y2, second_y2) - max(first[1], second[1]))
    union = first[2] * first[3] + second[2] * second[3] - intersection
    return round(intersection / union, 6) if union else 0.0


def compare_predictions(baseline: list[NormalizedPrediction], current: list[NormalizedPrediction], confidence_delta_threshold: float = 0.15, iou_threshold: float = 0.5) -> list[dict[str, Any]]:
    baseline_by_sample = {item.sample_id: item for item in baseline}
    current_by_sample = {item.sample_id: item for item in current}
    changes: list[dict[str, Any]] = []
    for sample_id in sorted(set(baseline_by_sample) | set(current_by_sample)):
        before, after = baseline_by_sample.get(sample_id), current_by_sample.get(sample_id)
        if before is None or after is None:
            changes.append({"sample_id": sample_id, "type": "detection_count_change", "baseline": before.detection_count if before else 0, "current": after.detection_count if after else 0})
            continue
        iou = box_iou(before.bbox, after.bbox)
        confidence_delta = round(after.confidence - before.confidence, 6)
        if before.class_name != after.class_name:
            changes.append({"sample_id": sample_id, "type": "class_change", "baseline": before.class_name, "current": after.class_name})
        if abs(confidence_delta) > confidence_delta_threshold:
            changes.append({"sample_id": sample_id, "type": "confidence_delta", "baseline": before.confidence, "current": after.confidence, "delta": confidence_delta, "threshold": confidence_delta_threshold})
        if iou < iou_threshold:
            changes.append({"sample_id": sample_id, "type": "bounding_box_change", "baseline": list(before.bbox), "current": list(after.bbox), "iou": iou, "threshold": iou_threshold})
    return changes
