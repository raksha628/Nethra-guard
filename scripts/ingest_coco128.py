import os
import sys
import json
import urllib.request
import zipfile
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.services.dataset_validator import validate_dataset
from app.config import MODEL_EVALUATION_DATASET

COCO_CLASSES = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus',
    6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant',
    11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat',
    16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear',
    22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag',
    27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard',
    32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove',
    36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle',
    40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon',
    45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange',
    50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut',
    55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed',
    60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse',
    65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave',
    69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book',
    74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier',
    79: 'toothbrush'
}

URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"
SCRATCH_DIR = Path("scratch")
ZIP_PATH = SCRATCH_DIR / "coco128.zip"
TARGET_DIR = Path("workspace/model_evaluation")
IMAGES_DIR = TARGET_DIR / "images"
ANNS_DIR = TARGET_DIR / "annotations"

def download_and_extract():
    SCRATCH_DIR.mkdir(exist_ok=True)
    if not ZIP_PATH.exists():
        print(f"Downloading {URL}...")
        urllib.request.urlretrieve(URL, ZIP_PATH)
    
    print("Extracting ZIP...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(SCRATCH_DIR)

def convert_to_coco():
    print("Converting to COCO JSON...")
    src_images = SCRATCH_DIR / "coco128" / "images" / "train2017"
    src_labels = SCRATCH_DIR / "coco128" / "labels" / "train2017"
    
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ANNS_DIR.mkdir(parents=True, exist_ok=True)
    
    images_meta = []
    annotations_meta = []
    
    categories = [{"id": k, "name": v} for k, v in COCO_CLASSES.items()]
    
    img_id = 1
    ann_id = 1
    
    import shutil
    
    image_files = sorted(list(src_images.glob("*.jpg")))
    
    for img_path in image_files:
        # Copy image
        target_img = IMAGES_DIR / img_path.name
        if not target_img.exists():
            shutil.copy2(img_path, target_img)
            
        with Image.open(target_img) as img:
            w, h = img.size
            
        images_meta.append({
            "id": img_id,
            "file_name": img_path.name,
            "width": w,
            "height": h
        })
        
        # Parse labels
        lbl_path = src_labels / (img_path.stem + ".txt")
        if lbl_path.exists():
            with open(lbl_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        cid, xc, yc, bw, bh = map(float, parts)
                        cid = int(cid)
                        
                        bbox_w = bw * w
                        bbox_h = bh * h
                        x = (xc * w) - (bbox_w / 2)
                        y = (yc * h) - (bbox_h / 2)
                        
                        annotations_meta.append({
                            "id": ann_id,
                            "image_id": img_id,
                            "category_id": cid,
                            "bbox": [round(x, 2), round(y, 2), round(bbox_w, 2), round(bbox_h, 2)],
                            "area": round(bbox_w * bbox_h, 2),
                            "iscrowd": 0
                        })
                        ann_id += 1
                        
        img_id += 1

    coco_json = {
        "images": images_meta,
        "annotations": annotations_meta,
        "categories": categories
    }
    
    with open(ANNS_DIR / "instances.json", "w") as f:
        json.dump(coco_json, f, indent=2)
        
    return len(image_files), ann_id - 1

def write_metadata_and_readme(img_count, ann_count):
    metadata = {
        "dataset_name": "Ultralytics COCO128",
        "dataset_role": "model_evaluation",
        "source": URL,
        "original_dataset": "Microsoft COCO",
        "format": "COCO",
        "source_annotation_format": "YOLO",
        "image_count": img_count,
        "annotation_count": ann_count,
        "class_count": 80,
        "version": "1.0",
        "license": "CC0 1.0 Universal",
        "purpose": "development semantic model evaluation",
        "limitations": [
            "COCO128 is a small development dataset",
            "COCO128 is not a defence-specific dataset",
            "Results must not be interpreted as production or defence-operational accuracy"
        ]
    }
    with open(TARGET_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    readme_content = """# Dataset Provenance

### Dataset
Ultralytics COCO128

### Original Dataset
Microsoft COCO

### Purpose
Real photographic semantic model-evaluation demonstration.

### Source
Official Ultralytics COCO128 release.

### Annotation Format
Original YOLO labels converted into COCO JSON for NETRA-Guard.

### Important Limitation
COCO128 is a small general-purpose dataset.
It demonstrates the evaluation pipeline but does NOT establish:
- defence-specific accuracy
- military-object detection accuracy
- operational reliability
- production performance
- battlefield performance
"""
    with open(TARGET_DIR / "README.md", "w") as f:
        f.write(readme_content)

def cleanup():
    import shutil
    if SCRATCH_DIR.exists():
        shutil.rmtree(SCRATCH_DIR, ignore_errors=True)

if __name__ == "__main__":
    download_and_extract()
    imgs, anns = convert_to_coco()
    write_metadata_and_readme(imgs, anns)
    
    print(f"Converted {imgs} images and {anns} annotations.")
    print("Validating dataset...")
    
    val = validate_dataset(MODEL_EVALUATION_DATASET)
    if val.is_valid:
        print(f"Dataset is VALID. Hash: {val.dataset_hash}")
    else:
        print("Dataset validation FAILED.")
        for err in val.errors:
            print(" -", err)
        sys.exit(1)
        
    cleanup()
    print("Ingestion complete.")
