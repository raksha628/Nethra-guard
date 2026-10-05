from analytics.status import aggregate_status
from assurance.schemas import Finding, ModuleName, ModuleResult, ModuleStatus, Severity


def _module(name: ModuleName, status: ModuleStatus, severity: Severity | None = None) -> ModuleResult:
    findings = []
    if severity is not None:
        findings.append(
            Finding(
                severity=severity,
                title=f"{name.value} finding",
                method="test",
                observed_value="1",
                threshold="0",
                limitations="test",
            )
        )
    return ModuleResult(module=name, status=status, findings=findings)


def test_status_matrix_fail_review_pass_and_not_run():
    data = ModuleName.data_integrity
    model = ModuleName.model_integrity
    shift = ModuleName.distribution_shift
    comparator = ModuleName.comparator

    failed = aggregate_status([
        _module(data, ModuleStatus.FAIL, Severity.CRITICAL),
        _module(model, ModuleStatus.PASS),
    ])
    assert failed["status"] == "FAIL"
    assert any("FAIL" in reason or "CRITICAL" in reason for reason in failed["reasons"])

    high_finding = aggregate_status([
        _module(data, ModuleStatus.WARNING, Severity.HIGH),
    ])
    assert high_finding["status"] == "FAIL"

    review = aggregate_status([
        _module(data, ModuleStatus.PASS),
        _module(shift, ModuleStatus.WARNING, Severity.MEDIUM),
    ])
    assert review["status"] == "REVIEW"
    assert review["reasons"] == ["distribution_shift WARNING"]

    passed = aggregate_status([
        _module(data, ModuleStatus.PASS),
        _module(model, ModuleStatus.PASS),
        _module(shift, ModuleStatus.PASS),
        _module(comparator, ModuleStatus.PASS),
    ])
    assert passed["status"] == "PASS"
    assert "score" not in passed

    skipped = aggregate_status([
        _module(data, ModuleStatus.PASS),
        _module(shift, ModuleStatus.NOT_RUN),
    ])
    assert skipped["status"] == "NOT_RUN"
    assert skipped["reasons"] == ["distribution_shift NOT_RUN"]

    fail_beats_skip = aggregate_status([
        _module(data, ModuleStatus.FAIL, Severity.CRITICAL),
        _module(shift, ModuleStatus.NOT_RUN),
    ])
    assert fail_beats_skip["status"] == "FAIL"
