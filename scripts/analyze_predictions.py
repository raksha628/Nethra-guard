import json
from pathlib import Path
import onnxruntime as ort
from PIL import Image, ImageDraw
import numpy as np
import cv2

MODEL_PATH = Path("workspace/synthetic_cv/models/detector.onnx")
EVAL_IMAGES = Path("workspace/synthetic_cv/evaluation/images")
VIS_DIR = Path("workspace/synthetic_cv/evaluation/visualized")

CLASS_NAMES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush'
]

CLASS_MAP = {
    0: 'person', 1: 'vehicle', 2: 'vehicle', 3: 'vehicle',
    4: 'vehicle', 5: 'vehicle', 6: 'vehicle', 7: 'vehicle', 8: 'vehicle'
}

def preprocess(img_path):
    img = Image.open(img_path).convert("RGB")
    orig_w, orig_h = img.size
    img_resized = img.resize((640, 640))
    img_np = np.array(img_resized, dtype=np.float32) / 255.0
    img_np = np.transpose(img_np, (2, 0, 1))
    return np.expand_dims(img_np, axis=0), orig_w, orig_h, img

def postprocess(output, orig_w, orig_h, conf_thres=0.01, iou_thres=0.45):
    if len(output.shape) != 3 or output.shape[1] < 4:
        return []
    pred = output[0].T
    boxes_xywh = pred[:, :4]
    scores_matrix = pred[:, 4:]
    
    max_scores = np.max(scores_matrix, axis=1)
    class_ids = np.argmax(scores_matrix, axis=1)
    
    keep = max_scores > conf_thres
    boxes_xywh = boxes_xywh[keep]
    max_scores = max_scores[keep]
    class_ids = class_ids[keep]
    
    if len(boxes_xywh) == 0:
        return []
        
    boxes_xyxy = np.empty_like(boxes_xywh)
    boxes_xyxy[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
    boxes_xyxy[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2
    boxes_xyxy[:, 2] = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2
    boxes_xyxy[:, 3] = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2
    
    scale_w = orig_w / 640.0
    scale_h = orig_h / 640.0
    boxes_xyxy[:, 0] *= scale_w
    boxes_xyxy[:, 2] *= scale_w
    boxes_xyxy[:, 1] *= scale_h
    boxes_xyxy[:, 3] *= scale_h
    
    indices = np.argsort(max_scores)[::-1]
    keep_boxes = []
    
    while len(indices) > 0:
        current = indices[0]
        keep_boxes.append(current)
        if len(indices) == 1: break
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
        
    results = []
    for i in keep_boxes:
        cid = int(class_ids[i])
        x1 = max(0.0, float(boxes_xyxy[i, 0]))
        y1 = max(0.0, float(boxes_xyxy[i, 1]))
        x2 = min(float(orig_w), float(boxes_xyxy[i, 2]))
        y2 = min(float(orig_h), float(boxes_xyxy[i, 3]))
        if x2 > x1 and y2 > y1:
            results.append({
                "class_id": cid,
                "raw_class_name": CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else str(cid),
                "mapped_class_name": CLASS_MAP.get(cid, None),
                "confidence": float(max_scores[i]),
                "bbox": [x1, y1, x2, y2]
            })
    return results

def main():
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    session = ort.InferenceSession(str(MODEL_PATH), providers=['CPUExecutionProvider'])
    input_name = session.get_inputs()[0].name
    output_names = [out.name for out in session.get_outputs()]
    
    thresholds = [0.01, 0.05, 0.10, 0.25, 0.50]
    results_by_thresh = {t: {"images": 0, "predictions": 0, "confidences": []} for t in thresholds}
    
    all_raw_classes = set()
    mapped_classes = set()
    
    images = list(EVAL_IMAGES.glob("*.png"))
    
    print(f"Analyzing {len(images)} images...")
    
    for i, img_path in enumerate(images):
        img_tensor, orig_w, orig_h, orig_img = preprocess(img_path)
        outputs = session.run(output_names, {input_name: img_tensor})
        raw_output = outputs[0]
        
        for t in thresholds:
            dets = postprocess(raw_output, orig_w, orig_h, conf_thres=t)
            if len(dets) > 0:
                results_by_thresh[t]["images"] += 1
                results_by_thresh[t]["predictions"] += len(dets)
                for d in dets:
                    results_by_thresh[t]["confidences"].append(d["confidence"])
                    
                    if t == 0.01:
                        all_raw_classes.add(d["raw_class_name"])
                        if d["mapped_class_name"]:
                            mapped_classes.add(d["mapped_class_name"])
                            
        # Save a visualization for threshold 0.01 for the first 5 images that have detections
        if i < 5:
            dets = postprocess(raw_output, orig_w, orig_h, conf_thres=0.01)
            if dets:
                vis_img = orig_img.copy()
                draw = ImageDraw.Draw(vis_img)
                for d in dets:
                    x1, y1, x2, y2 = d["bbox"]
                    label = f"{d['raw_class_name']}({d['confidence']:.2f})"
                    if d['mapped_class_name']:
                        label += f" -> {d['mapped_class_name']}"
                        color = "green"
                    else:
                        color = "red"
                    draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                    draw.text((x1, y1), label, fill=color)
                vis_img.save(VIS_DIR / f"vis_{img_path.name}")
                print(f"Saved visualization: vis_{img_path.name}")

    print("\n--- THRESHOLD SWEEP ---")
    for t in thresholds:
        stats = results_by_thresh[t]
        mean_conf = np.mean(stats["confidences"]) if stats["confidences"] else 0
        print(f"Threshold: {t:.2f} | Images: {stats['images']} | Predictions: {stats['predictions']} | Mean Conf: {mean_conf:.4f}")
        
    print("\n--- CLASS ANALYSIS ---")
    print(f"Detected COCO Classes (raw): {sorted(list(all_raw_classes))}")
    print(f"Successfully Mapped Classes: {sorted(list(mapped_classes))}")
    
if __name__ == "__main__":
    main()
