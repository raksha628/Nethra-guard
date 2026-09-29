from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import AssuranceStatus, FindingSeverity, FindingStatus, RunState


class RunCreateRequest(BaseModel):
    workspace_id: str | None = None
    dataset_asset_id: str | None = None
    reference_dataset_asset_id: str | None = None
    current_dataset_asset_id: str | None = None
    model_asset_id: str | None = None
    asset_id: str | None = None
    checks: list[str] = Field(default_factory=lambda: ["DATA_INTEGRITY"])
    configuration: dict[str, Any] = Field(default_factory=dict)


class EvidenceResponse(BaseModel):
    id: str
    finding_id: str
    sample_id: str
    metric: str
    expected_value: str | None = None
    observed_value: str | None = None
    reference: str | None = None
    asset_reference: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class FindingResponse(BaseModel):
    id: str
    run_id: str
    category: str
    severity: FindingSeverity
    status: FindingStatus
    title: str
    description: str
    method: str
    observed_value: str
    threshold: str
    confidence_note: str
    limitations: str
    evidence_refs: list[str]
    affected_asset: str
    affected_sample: str | None = None
    remediation: str
    created_at: datetime


class RunResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_asset_id: str | None
    reference_dataset_asset_id: str | None = None
    current_dataset_asset_id: str | None = None
    model_asset_id: str | None
    state: RunState
    created_at: datetime
    completed_at: datetime | None = None
    selected_checks: list[str]
    summary: dict[str, Any]
    configuration: dict[str, Any]
    findings_count: int
    status: AssuranceStatus


class RunDetailResponse(RunResponse):
    findings: list[FindingResponse]
