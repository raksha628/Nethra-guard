import os
from ultralytics import YOLO

def export_model():
    model = YOLO("yolov8n.pt")  # Downloads if missing
    
    out_dir = "workspace/synthetic_cv/models"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Exporting model to ONNX...")
    # Export returns the path to the exported model
    # By default, YOLO saves exported models alongside the .pt file (e.g. yolov8n.onnx)
    # We will then move it to the proper directory.
    onnx_path = model.export(format="onnx", imgsz=640)
    
    target_path = os.path.join(out_dir, "detector.onnx")
    if os.path.exists(target_path):
        os.remove(target_path)
    os.rename(onnx_path, target_path)
    print(f"Model exported successfully to {target_path}")

if __name__ == "__main__":
    export_model()
