from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Asset, Workspace
from app.schemas.common import AssetType
from app.services.hash_service import calculate_sha256


def _write_demo_dataset() -> Path:
    import shutil
    
    synthetic_eval = settings.workspace_root / "synthetic_cv" / "evaluation_dataset.zip"
    directory = settings.workspace_root / "demo"
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / "demo_coco_dataset.zip"
    
    if synthetic_eval.exists():
        shutil.copyfile(synthetic_eval, archive)
    else:
        # Fallback to tiny fixture if synthetic generator wasn't run
        first = BytesIO()
        second = BytesIO()
        Image.new("RGB", (32, 24), (40, 80, 160)).save(first, format="PNG")
        Image.new("RGB", (32, 24), (180, 60, 40)).save(second, format="PNG")
        document = {
            "images": [
                {"id": 1, "file_name": "images/one.png", "width": 32, "height": 24},
                {"id": 2, "file_name": "images/two.png", "width": 32, "height": 24},
            ],
            "categories": [{"id": 1, "name": "vehicle"}],
            "annotations": [
                {"id": 1, "image_id": 1, "category_id": 1, "bbox": [2, 2, 10, 8]},
                {"id": 2, "image_id": 2, "category_id": 1, "bbox": [4, 3, 12, 9]},
            ],
        }
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("annotations/instances.json", json.dumps(document))
            output.writestr("images/one.png", first.getvalue())
            output.writestr("images/two.png", second.getvalue())
            
    return archive


def _write_demo_model() -> Path:
    import shutil
    
    onnx_source = settings.workspace_root / "synthetic_cv" / "models" / "detector.onnx"
    directory = settings.workspace_root / "demo"
    directory.mkdir(parents=True, exist_ok=True)
    
    if onnx_source.exists():
        path = directory / "demo_model.onnx"
        shutil.copyfile(onnx_source, path)
    else:
        path = directory / "demo_model.pt"
        path.write_bytes(b"NETRA-GUARD-DEMO-MODEL-ARTIFACT-V1")
        
    return path


def _register_if_missing(db: Session, workspace: Workspace, path: Path, asset_type: AssetType, original_name: str) -> Asset:
    existing = db.scalar(select(Asset).where(Asset.workspace_id == workspace.id, Asset.original_name == original_name, Asset.type == asset_type.value))
    if existing:
        return existing
    relative = path.resolve().relative_to(settings.workspace_root.resolve()).as_posix()
    asset = Asset(
        id=f"asset_{uuid4().hex}",
        workspace_id=workspace.id,
        type=asset_type.value,
        original_name=original_name,
        safe_path=relative,
        format=path.suffix.lower().lstrip("."),
        size_bytes=path.stat().st_size,
        sha256=calculate_sha256(path),
        metadata_json=json.dumps({"source": "bundled_demo", "offline": True}),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def ensure_demo_assets(db: Session, workspace: Workspace) -> tuple[Asset, Asset]:
    dataset = _register_if_missing(db, workspace, _write_demo_dataset(), AssetType.DATASET, "demo_coco_dataset.zip")
    
    model_path = _write_demo_model()
    model = _register_if_missing(db, workspace, model_path, AssetType.MODEL, model_path.name)
    
    if not workspace.baseline_model_asset_id:
        workspace.baseline_model_asset_id = model.id
        workspace.baseline_model_sha256 = model.sha256
        db.commit()
        db.refresh(workspace)
    return dataset, model
