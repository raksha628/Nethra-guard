"""Run-level assurance status. This is not a fifth module and not a numeric score."""

from __future__ import annotations

from assurance.schemas import ModuleName, ModuleResult, ModuleStatus, Severity


def aggregate_status(
    modules: list[ModuleResult],
    required: list[ModuleName] | None = None,
) -> dict[str, object]:
    """FAIL, then NOT_RUN, then REVIEW, then PASS.

    A skipped required module is NOT_RUN. It is not treated as a pass.
    """
    required_names = list(required) if required is not None else [module.module for module in modules]
    by_name = {module.module: module for module in modules}
    selected: list[ModuleResult] = []
    missing: list[ModuleName] = []
    for name in required_names:
        module = by_name.get(name)
        if module is None:
            missing.append(name)
        else:
            selected.append(module)

    fail_reasons: list[str] = []
    for module in selected:
        if module.status == ModuleStatus.FAIL:
            fail_reasons.append(f"{module.module.value} FAIL")
        for finding in module.findings:
            if finding.severity in {Severity.CRITICAL, Severity.HIGH}:
                fail_reasons.append(f"{module.module.value} {finding.severity.value}: {finding.title}")
    if fail_reasons:
        return {"status": "FAIL", "reasons": fail_reasons}

    not_run = [f"{module.module.value} NOT_RUN" for module in selected if module.status == ModuleStatus.NOT_RUN]
    not_run.extend(f"{name.value} NOT_RUN" for name in missing)
    if not_run:
        return {"status": "NOT_RUN", "reasons": not_run}

    warnings = [f"{module.module.value} WARNING" for module in selected if module.status == ModuleStatus.WARNING]
    if warnings:
        return {"status": "REVIEW", "reasons": warnings}

    return {"status": "PASS", "reasons": [f"{module.module.value} PASS" for module in selected]}
