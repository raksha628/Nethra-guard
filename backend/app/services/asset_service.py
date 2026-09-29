from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models import Asset, Workspace
from app.schemas.assets import AssetResponse
from app.schemas.common import AssetType
from app.services.file_storage import resolve_storage_path, validate_upload_size
from app.services.hash_service import calculate_sha256


def register_asset(db: Session, upload: UploadFile, asset_type: AssetType, workspace: Workspace) -> AssetResponse:
    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A filename is required")
    size = validate_upload_size(upload)
    destination = resolve_storage_path(upload.filename, asset_type)
    upload.file.seek(0)
    try:
        with destination.open("xb") as target:
            shutil.copyfileobj(upload.file, target)
        file_hash = calculate_sha256(destination)
        asset = Asset(
            id=f"asset_{uuid4().hex}",
            workspace_id=workspace.id,
            type=asset_type.value,
            original_name=Path(upload.filename).name,
            safe_path=destination.relative_to(workspace_root(workspace)).as_posix(),
            format=destination.suffix.lower().lstrip("."),
            size_bytes=size,
            sha256=file_hash,
            metadata_json=json.dumps({"source": "local_upload", "content_type": upload.content_type}),
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return AssetResponse(
        asset_id=asset.id,
        workspace_id=asset.workspace_id,
        type=AssetType(asset.type),
        original_name=asset.original_name,
        size=asset.size_bytes,
        format=asset.format,
        sha256=asset.sha256,
        created_at=asset.created_at,
        registration_metadata=json.loads(asset.metadata_json),
    )


def workspace_root(workspace: Workspace) -> Path:
    from app.config import settings

    return settings.workspace_root
