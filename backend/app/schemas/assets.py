from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AssetType


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    workspace_id: str
    type: AssetType
    original_name: str
    size: int = Field(description="Asset size in bytes")
    format: str
    sha256: str
    created_at: datetime
    registration_metadata: dict[str, Any]


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    asset_count: int
    metadata: dict[str, Any]
    baseline_model_asset_id: str | None = None
    baseline_model_sha256: str | None = None


class ModelBaselineRequest(BaseModel):
    asset_id: str
    workspace_id: str | None = None


class ModelBaselineResponse(BaseModel):
    workspace_id: str
    asset_id: str
    sha256: str
    message: str
