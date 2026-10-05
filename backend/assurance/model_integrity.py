"""Model artifact fingerprinting and baseline comparison.

A hash match means the bytes equal the registered baseline. It does not prove
the file is safe. Pickle-based weights are never deserialized.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .hashing import sha256_file
from .schemas import (
    EvidenceRef,
    Finding,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    Severity,
)

DETERMINISTIC = "Rule-based / deterministic check"
HASH_MISMATCH_TITLE = "SHA-256 hash differs from registered baseline"
HASH_MISMATCH_LIMITATION = (
    "A hash mismatch means the artifact differs from the registered baseline. "
    "It does not prove malicious tampering."
)
PASS_LIMITATION = (
    "SHA-256 match means the file bytes equal the registered baseline. "
    "It does not prove the artifact is safe or that training was trusted. "
    "Pickle-based weights are never loaded."
)
PICKLE_SUFFIXES = {".pkl", ".pickle"}


class ModelAdapter(ABC):
    """Format-specific loader. Integrity hashing does not execute weights."""

    name: str
    simulated: bool

    def fingerprint(self, model_path: Path) -> dict[str, Any]:
        path = model_path.resolve()
        return {
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "format": path.suffix.lower(),
            "metadata": {},
        }

    @abstractmethod
    def supports(self, model_path: Path) -> bool:
        """Return whether this adapter can run inference for the file."""

    @abstractmethod
    def predict(self, model_path: Path, image_paths: list[Path], config: dict[str, Any]) -> Any:
        """Run inference. Concrete adapters implement this."""


class UnsafeModelError(ValueError):
    """Raised when an adapter is asked to deserialize an unsafe model format."""


def check_model(
    model_path: Path,
    *,
    baseline_sha256: str | None,
    allowed_root: Path,
) -> ModuleResult:
    root = allowed_root.resolve()
    try:
        resolved = model_path.resolve()
        resolved.relative_to(root)
    except ValueError:
        return _result(
            ModuleStatus.FAIL,
            {},
            [
                Finding(
                    severity=Severity.CRITICAL,
                    title="Model path is not allowed",
                    method=f"{DETERMINISTIC}. The resolved path must stay inside the workspace root.",
                    observed_value=str(model_path),
                    threshold=str(root),
                    evidence_refs=[],
                    limitations="The path was rejected before the file was read.",
                )
            ],
        )

    if not resolved.is_file():
        return _result(
            ModuleStatus.FAIL,
            {"path": resolved.name, "weights_loaded": False},
            [
                Finding(
                    severity=Severity.CRITICAL,
                    title="Model artifact is unreadable",
                    method=f"{DETERMINISTIC}. The registered model path must be a file.",
                    observed_value="missing",
                    threshold="file must exist and be readable",
                    evidence_refs=[
                        EvidenceRef(
                            id="model-missing",
                            sample_id=resolved.name,
                            file_hash=None,
                            evidence_type="model_artifact",
                        )
                    ],
                    limitations="No hash was computed because the file could not be read.",
                )
            ],
        )

    fingerprint = {
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
        "format": resolved.suffix.lower(),
        "metadata": {},
        "weights_loaded": False,
        "certainty": DETERMINISTIC,
    }
    if resolved.suffix.lower() in PICKLE_SUFFIXES:
        fingerprint["load_note"] = "Pickle weights were not deserialized."

    baseline = (baseline_sha256 or "").strip().lower()
    if not baseline:
        fingerprint["reason"] = "No registered baseline hash was provided, so the artifact was not compared."
        fingerprint["limitations"] = PASS_LIMITATION
        return _result(ModuleStatus.NOT_RUN, fingerprint, [])

    fingerprint["baseline_sha256"] = baseline
    if fingerprint["sha256"] != baseline:
        return _result(
            ModuleStatus.FAIL,
            fingerprint,
            [
                Finding(
                    severity=Severity.CRITICAL,
                    title=HASH_MISMATCH_TITLE,
                    method=f"{DETERMINISTIC}. Compare the artifact SHA-256 with the registered baseline manifest.",
                    observed_value=fingerprint["sha256"],
                    threshold=baseline,
                    evidence_refs=[
                        EvidenceRef(
                            id="model-hash-mismatch",
                            sample_id=resolved.name,
                            file_hash=fingerprint["sha256"],
                            evidence_type="model_artifact",
                        )
                    ],
                    limitations=HASH_MISMATCH_LIMITATION,
                )
            ],
        )

    fingerprint["limitations"] = PASS_LIMITATION
    return _result(ModuleStatus.PASS, fingerprint, [])


def _result(status: ModuleStatus, metrics: dict[str, Any], findings: list[Finding]) -> ModuleResult:
    return ModuleResult(
        module=ModuleName.model_integrity,
        status=status,
        metrics=metrics,
        findings=findings,
    )
