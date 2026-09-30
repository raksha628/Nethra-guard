"""Run-level status. FAIL outranks a skip. A skip is not a pass."""

from analytics.status import aggregate_status
from assurance.schemas import (
    EvidenceRef,
    Finding,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    Severity,
)


def _module(name: ModuleName, status: ModuleStatus, severity: Severity | None = None) -> ModuleResult:
    findings = []
    if severity is not None:
        findings.append(
            Finding(
                severity=severity,
                title=name.value,
                method="Test.",
                observed_value="1",
                threshold="0",
                evidence_refs=[
                    EvidenceRef(id=name.value, sample_id="sample", file_hash=None, evidence_type="test")
                ],
                limitations="Test.",
            )
        )
    return ModuleResult(module=name, status=status, findings=findings)


def test_status_matrix():
    data = ModuleName.data_integrity
    model = ModuleName.model_integrity
    shift = ModuleName.distribution_shift
    comparator = ModuleName.comparator
    required = [data, model, shift, comparator]

    passed = aggregate_status(
        [
            _module(data, ModuleStatus.PASS),
            _module(model, ModuleStatus.PASS),
            _module(shift, ModuleStatus.PASS),
            _module(comparator, ModuleStatus.PASS),
        ],
        required,
    )
    assert passed.status == "PASS"
    assert passed.reasons == ["all required checks passed"]

    review = aggregate_status(
        [
            _module(data, ModuleStatus.PASS),
            _module(model, ModuleStatus.PASS),
            _module(shift, ModuleStatus.WARNING, Severity.MEDIUM),
            _module(comparator, ModuleStatus.PASS),
        ],
        required,
    )
    assert review.status == "REVIEW"
    assert review.reasons == ["distribution_shift is WARNING"]

    failed = aggregate_status(
        [
            _module(data, ModuleStatus.FAIL, Severity.CRITICAL),
            _module(model, ModuleStatus.PASS),
            _module(shift, ModuleStatus.NOT_RUN),
            _module(comparator, ModuleStatus.PASS),
        ],
        required,
    )
    assert failed.status == "FAIL"
    assert failed.reasons == ["data_integrity is FAIL"]

    skipped = aggregate_status(
        [
            _module(data, ModuleStatus.PASS),
            _module(model, ModuleStatus.PASS),
            _module(shift, ModuleStatus.WARNING, Severity.MEDIUM),
            _module(comparator, ModuleStatus.NOT_RUN),
        ],
        required,
    )
    assert skipped.status == "NOT_RUN"
    assert skipped.status != "PASS"
    assert "comparator did not run" in skipped.reasons

    blocking = aggregate_status(
        [
            _module(data, ModuleStatus.WARNING, Severity.HIGH),
            _module(model, ModuleStatus.PASS),
        ],
        [data, model],
    )
    assert blocking.status == "FAIL"

    missing = aggregate_status([_module(data, ModuleStatus.PASS)], [data, shift])
    assert missing.status == "NOT_RUN"
    assert missing.module_statuses["distribution_shift"] == "NOT_RUN"
