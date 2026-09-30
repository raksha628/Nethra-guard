"""Run-level assurance status.

This is not a fifth module and it is not a numeric trust score.
FAIL outranks a skipped check. A skipped required check stays NOT_RUN.
Warnings become REVIEW. PASS requires every required module to pass.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from assurance.schemas import ModuleName, ModuleResult, ModuleStatus, Severity

DecisionStatus = Literal["PASS", "REVIEW", "FAIL", "NOT_RUN"]


class AssuranceDecision(BaseModel):
    status: DecisionStatus
    reasons: list[str]
    notes: list[str] = Field(default_factory=list)
    module_statuses: dict[str, str]
    required_modules: list[str]


def aggregate_status(
    modules: list[ModuleResult],
    required: list[ModuleName] | None = None,
) -> AssuranceDecision:
    by_name = {module.module: module for module in modules}
    required_modules = list(by_name) if required is None else list(required)
    module_statuses = {module.module.value: module.status.value for module in modules}
    for name in required_modules:
        module_statuses.setdefault(name.value, ModuleStatus.NOT_RUN.value)

    fail_reasons: list[str] = []
    skipped_reasons: list[str] = []
    review_reasons: list[str] = []
    for name in required_modules:
        module = by_name.get(name)
        if module is None:
            skipped_reasons.append(f"{name.value} did not run")
            continue
        if module.status == ModuleStatus.FAIL or _has_blocking_finding(module):
            fail_reasons.append(f"{name.value} is FAIL")
        elif module.status == ModuleStatus.NOT_RUN:
            skipped_reasons.append(f"{name.value} did not run")
        elif module.status == ModuleStatus.WARNING:
            review_reasons.append(f"{name.value} is WARNING")

    if fail_reasons:
        status: DecisionStatus = "FAIL"
        reasons = fail_reasons
    elif skipped_reasons:
        status = "NOT_RUN"
        reasons = skipped_reasons
    elif review_reasons:
        status = "REVIEW"
        reasons = review_reasons
    else:
        status = "PASS"
        reasons = ["all required checks passed"]

    return AssuranceDecision(
        status=status,
        reasons=reasons,
        module_statuses=module_statuses,
        required_modules=[name.value for name in required_modules],
    )


def _has_blocking_finding(module: ModuleResult) -> bool:
    return any(
        finding.severity in {Severity.CRITICAL, Severity.HIGH} for finding in module.findings
    )
