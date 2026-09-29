from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.schemas.common import AssetType

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def validate_extension(filename: str, asset_type: AssetType) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions[asset_type.value]:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Extension '{suffix or '[none]'}' is not allowed for {asset_type.value} assets")
    return suffix


def safe_filename(filename: str, asset_type: AssetType) -> str:
    if Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path components are not allowed in filenames")
    suffix = validate_extension(filename, asset_type)
    stem = Path(filename).stem
    safe_stem = _SAFE_NAME.sub("_", stem).strip("._") or "asset"
    return f"{asset_type.value.lower()}_{uuid4().hex}_{safe_stem[:80]}{suffix}"


def resolve_storage_path(filename: str, asset_type: AssetType) -> Path:
    safe_name = safe_filename(filename, asset_type)
    directory = settings.workspace_root / ("datasets" if asset_type is AssetType.DATASET else "models")
    directory.mkdir(parents=True, exist_ok=True)
    path = (directory / safe_name).resolve()
    if path.parent != directory.resolve() or path.is_symlink():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage path")
    return path


def validate_upload_size(upload: UploadFile) -> int:
    size = 0
    while chunk := upload.file.read(1024 * 1024):
        size += len(chunk)
        if size > settings.max_upload_size_bytes:
            raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Uploaded file exceeds the configured size limit")
    upload.file.seek(0)
    return size
