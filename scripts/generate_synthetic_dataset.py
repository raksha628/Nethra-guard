import os
import sys
import json
import random
import zipfile
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance

# Set deterministic seed
random.seed(20261005)

CATEGORIES = [
    {"id": 1, "name": "vehicle"},
    {"id": 2, "name": "person"},
    {"id": 3, "name": "equipment"},
    {"id": 4, "name": "structure"}
]

def generate_image(width, height, is_evaluation=False):
    # Base background (synthetic noise/gradients)
    base_color = (
        random.randint(50, 200),
        random.randint(50, 200),
        random.randint(50, 200)
    )
    img = Image.new("RGB", (width, height), base_color)
    draw = ImageDraw.Draw(img)
    
    objects = []
    num_objects = random.choice([1, 1, 2, 3, 4, 5, 8])
    for _ in range(num_objects):
        cat = random.choice(CATEGORIES)["id"]
        # Generate bounding box
        bw = random.randint(20, width // 3)
        bh = random.randint(20, height // 3)
        x = random.randint(0, width - bw - 1)
        y = random.randint(0, height - bh - 1)
        
        # Draw object
        obj_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        if cat == 1: # vehicle - rect
            draw.rectangle([x, y, x+bw, y+bh], fill=obj_color)
        elif cat == 2: # person - ellipse
            draw.ellipse([x, y, x+bw, y+bh], fill=obj_color)
        elif cat == 3: # equipment - triangle
            draw.polygon([(x+bw//2, y), (x+bw, y+bh), (x, y+bh)], fill=obj_color)
        elif cat == 4: # structure - big rect
            draw.rectangle([x, y, x+bw, y+bh], fill=obj_color, outline=(0,0,0), width=2)
            
        objects.append({
            "category_id": cat,
            "bbox": [x, y, bw, bh]
        })
        
    # Apply distribution shift if evaluation
    if is_evaluation:
        # Darker scenes and altered contrast
        img = ImageEnhance.Brightness(img).enhance(0.65)
        img = ImageEnhance.Contrast(img).enhance(1.4)
        
    return img, objects

def generate_dataset(dataset_dir, prefix, num_images, is_evaluation=False, inject_anomalies=False):
    images_dir = dataset_dir / "images"
    annotations_dir = dataset_dir / "annotations"
    images_dir.mkdir(parents=True, exist_ok=True)
    annotations_dir.mkdir(parents=True, exist_ok=True)
    
    coco = {
        "images": [],
        "annotations": [],
        "categories": CATEGORIES
    }
    
    resolutions = [(640, 480), (800, 600), (1280, 720)]
    
    ann_id = 1
    
    stats = {"images": 0, "annotations": 0, "duplicates": 0, "invalid_bbox": 0}
    
    first_image_bytes = None
    first_image_filename = None
    
    for i in range(1, num_images + 1):
        width, height = random.choice(resolutions)
        img, objects = generate_image(width, height, is_evaluation)
        
        filename = f"{prefix}_{i:03d}.png"
        filepath = images_dir / filename
        
        # Save image
        img.save(filepath, format="PNG")
        
        # Capture first image bytes for duplicate
        if i == 1:
            with open(filepath, 'rb') as f:
                first_image_bytes = f.read()
            first_image_filename = filename
            
        coco["images"].append({
            "id": i,
            "file_name": f"images/{filename}",
            "width": width,
            "height": height
        })
        stats["images"] += 1
        
        for obj in objects:
            coco["annotations"].append({
                "id": ann_id,
                "image_id": i,
                "category_id": obj["category_id"],
                "bbox": obj["bbox"]
            })
            stats["annotations"] += 1
            ann_id += 1
            
    # Inject anomalies if requested
    if inject_anomalies:
        # 1. Duplicate Image (identical bytes to first image, different filename)
        dup_filename = f"{prefix}_dup.png"
        dup_filepath = images_dir / dup_filename
        with open(dup_filepath, 'wb') as f:
            f.write(first_image_bytes)
        
        dup_id = num_images + 1
        coco["images"].append({
            "id": dup_id,
            "file_name": f"images/{dup_filename}",
            "width": coco["images"][0]["width"],
            "height": coco["images"][0]["height"]
        })
        coco["annotations"].append({
            "id": ann_id,
            "image_id": dup_id,
            "category_id": CATEGORIES[0]["id"],
            "bbox": [10, 10, 50, 50]
        })
        ann_id += 1
        stats["images"] += 1
        stats["annotations"] += 1
        stats["duplicates"] += 1
        
        # 2. Missing image reference
        missing_id = num_images + 2
        coco["images"].append({
            "id": missing_id,
            "file_name": f"images/missing_nonexistent.png",
            "width": 640,
            "height": 480
        })
        coco["annotations"].append({
            "id": ann_id,
            "image_id": missing_id,
            "category_id": 1,
            "bbox": [10, 10, 50, 50]
        })
        ann_id += 1
        stats["images"] += 1
        stats["annotations"] += 1
        
        # 3. Invalid out-of-bounds bounding box
        coco["annotations"].append({
            "id": ann_id,
            "image_id": 2,
            "category_id": 1,
            "bbox": [9000, 9000, 100, 100]  # Out of bounds
        })
        ann_id += 1
        stats["annotations"] += 1
        stats["invalid_bbox"] += 1
        
        # 4. Extreme aspect ratio
        coco["annotations"].append({
            "id": ann_id,
            "image_id": 3,
            "category_id": 2,
            "bbox": [10, 10, 500, 2]  # Very wide and thin
        })
        ann_id += 1
        stats["annotations"] += 1
        
    with open(annotations_dir / "instances.json", "w") as f:
        json.dump(coco, f, indent=2)
        
    return stats

def create_zip(dataset_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dataset_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dataset_dir)
                # Ensure forward slashes for zip
                arcname = arcname.replace('\\', '/')
                zf.write(file_path, arcname)

if __name__ == "__main__":
    base_dir = Path("workspace/synthetic_cv")
    ref_dir = base_dir / "reference"
    eval_dir = base_dir / "evaluation"
    
    print("Generating reference dataset...")
    ref_stats = generate_dataset(ref_dir, "ref", 80, is_evaluation=False, inject_anomalies=False)
    
    print("Generating evaluation dataset...")
    eval_stats = generate_dataset(eval_dir, "eval", 80, is_evaluation=True, inject_anomalies=True)
    
    print("\nCreating ZIP archives...")
    create_zip(ref_dir, base_dir / "reference_dataset.zip")
    create_zip(eval_dir, base_dir / "evaluation_dataset.zip")
    
    print("\n=== Dataset Summary ===")
    print("Reference:")
    print(f"- images: {ref_stats['images']}")
    print(f"- annotations: {ref_stats['annotations']}")
    print(f"- categories: {len(CATEGORIES)}")
    print(f"- duplicate images: {ref_stats['duplicates']}")
    print(f"- invalid boxes: {ref_stats['invalid_bbox']}")
    
    print("\nEvaluation:")
    print(f"- images: {eval_stats['images']}")
    print(f"- annotations: {eval_stats['annotations']}")
    print(f"- categories: {len(CATEGORIES)}")
    print(f"- duplicate images: {eval_stats['duplicates']}")
    print(f"- intentional annotation anomaly: YES (missing, oob, extreme aspect)")
    print(f"- shifted brightness distribution: YES")
    print(f"- shifted contrast distribution: YES")
