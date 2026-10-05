"""Shared module-result, finding, and detection contracts.

The JSON for module results follows the AIML work-split schema (snake_case).
Ledger entries use the frontend provenance field names (camelCase) via aliases.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModuleName(str, Enum):
    data_integrity = "data_integrity"
    model_integrity = "model_integrity"
    distribution_shift = "distribution_shift"
    comparator = "comparator"


class ModuleStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceRef(BaseModel):
    id: str
    sample_id: str
    file_hash: str | None = None
    evidence_type: str


class Finding(BaseModel):
    severity: Severity
    title: str
    method: str
    observed_value: str
    threshold: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    limitations: str


class ModuleResult(BaseModel):
    module: ModuleName
    status: ModuleStatus
    metrics: dict[str, Any] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)


class Detection(BaseModel):
    class_id: int
    confidence: float
    bbox_xyxy: list[int]


class ImageDetections(BaseModel):
    image_id: str
    detections: list[Detection]


class LedgerEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sequence: int
    run_id: str = Field(alias="runId")
    timestamp: str
    actor_label: str = Field(default="local-demo", alias="actorLabel")
    dataset_hash: str = Field(alias="datasetHash")
    model_hash: str = Field(alias="modelHash")
    config_hash: str = Field(alias="configHash")
    summary_hash: str = Field(alias="summaryHash")
    previous_hash: str = Field(alias="previousHash")
    current_hash: str = Field(alias="currentHash")
    baseline_run_id: str | None = Field(default=None, alias="baselineRunId")


class LedgerVerification(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    first_invalid_sequence: int | None = Field(default=None, alias="firstInvalidSequence")
    reason: str | None = None


def not_run(module: ModuleName, reason: str) -> ModuleResult:
    return ModuleResult(
        module=module,
        status=ModuleStatus.NOT_RUN,
        metrics={"reason": reason},
        findings=[],
    )


def status_from_findings(findings: list[Finding]) -> ModuleStatus:
    """CRITICAL or HIGH fails the module. Any other finding is a warning."""
    if any(item.severity in {Severity.CRITICAL, Severity.HIGH} for item in findings):
        return ModuleStatus.FAIL
    if findings:
        return ModuleStatus.WARNING
    return ModuleStatus.PASS
