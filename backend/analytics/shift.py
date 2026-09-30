"""Distribution shift by Population Stability Index.

PSI = sum_i (c_i - r_i) * ln(c_i / r_i)

r_i and c_i are the reference and current proportions in shared bins.
Empty bins use a small epsilon so the logarithm stays defined. The published
score is the maximum PSI across image features.

The cutoff 0.10 is a prototype demonstration threshold, not a deployment limit.
A shift is a warning. It does not by itself prove the model failed, so findings
stay MEDIUM and the module stays WARNING.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from assurance.schemas import (
    EvidenceRef,
    Finding,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    Severity,
    status_from_findings,
)

from .features import FEATURE_ORDER, ImageFeatures, extract_batch

PSI_THRESHOLD = 0.10
MIN_SAMPLES = 2
BIN_COUNT = 10
PSI_EPSILON = 1e-6
SHIFT_TITLE = "Image feature distribution shift"
SHIFT_LIMITATION = (
    "A distribution shift is a warning signal. It does not by itself prove the model failed. "
    "The 0.10 PSI cutoff is a prototype demonstration threshold, not a deployment limit."
)
THRESHOLD_LABEL = "Prototype demonstration threshold, not a deployment limit."
FORMULA = "PSI = sum_i (c_i - r_i) * ln(c_i / r_i)"


def color_edges(bin_count: int = BIN_COUNT) -> list[float]:
    """Fixed edges from 0 through 255."""
    return [index * 255.0 / bin_count for index in range(bin_count + 1)]


def size_edges(bin_count: int = BIN_COUNT) -> list[float]:
    """Fixed pixel edges. Each bin is 40 pixels wide, through 400."""
    return [index * 40.0 for index in range(bin_count + 1)]


# Fixed 0–1 edges. The low end is finer because these fixtures measure small
# edge densities. Equal 0.1 bins would hide a blur that stays under 0.1.
EDGE_DENSITY_EDGES = [0.0, 0.005, 0.08, 0.15, 0.25, 0.4, 0.55, 0.7, 0.85, 0.95, 1.0]


def edges_for(feature: str, bin_count: int = BIN_COUNT) -> list[float]:
    if feature in {"width", "height"}:
        return size_edges(bin_count)
    if feature == "edge_density":
        return list(EDGE_DENSITY_EDGES)
    return color_edges(bin_count)


def bin_index(value: float, edges: list[float]) -> int:
    """Bin that contains value. The rightmost edge belongs to the last bin."""
    last = len(edges) - 2
    if value <= edges[0]:
        return 0
    if value >= edges[-1]:
        return last
    index = 0
    for cursor, edge in enumerate(edges):
        if value >= edge:
            index = cursor
        else:
            break
    return min(index, last)


def population_stability_index(
    reference: list[float],
    current: list[float],
    edges: list[float],
) -> tuple[float, list[int], list[int]]:
    """Return PSI and the reference and current bin counts."""
    if len(edges) < 2:
        raise ValueError("PSI edges need at least two boundaries")
    bins = len(edges) - 1
    reference_counts = [0] * bins
    current_counts = [0] * bins
    for value in reference:
        reference_counts[bin_index(float(value), edges)] += 1
    for value in current:
        current_counts[bin_index(float(value), edges)] += 1
    reference_share = _proportions(reference_counts)
    current_share = _proportions(current_counts)
    score = 0.0
    for reference_bin, current_bin in zip(reference_share, current_share):
        score += (current_bin - reference_bin) * math.log(current_bin / reference_bin)
    return score, reference_counts, current_counts


def check_shift(
    reference_dir: Path,
    current_dir: Path,
    *,
    config: dict[str, Any] | None = None,
) -> ModuleResult:
    """Compare two image batches and return a distribution_shift ModuleResult."""
    settings = config or {}
    threshold = float(settings.get("psi_threshold", PSI_THRESHOLD))
    minimum = int(settings.get("min_samples", MIN_SAMPLES))
    bin_count = int(settings.get("bin_count", BIN_COUNT))
    reference, reference_skipped = extract_batch(reference_dir)
    current, current_skipped = extract_batch(current_dir)
    if len(reference) < minimum or len(current) < minimum:
        reason = (
            f"At least {minimum} readable images are required in each batch. "
            f"Reference has {len(reference)} and current has {len(current)}."
        )
        return ModuleResult(
            module=ModuleName.distribution_shift,
            status=ModuleStatus.NOT_RUN,
            metrics={
                "reason": reason,
                "reference_sample_count": len(reference),
                "current_sample_count": len(current),
                "reference_skipped": reference_skipped,
                "current_skipped": current_skipped,
                "threshold": threshold,
                "threshold_label": THRESHOLD_LABEL,
            },
            findings=[],
        )

    feature_psi: dict[str, float] = {}
    reference_means: dict[str, float] = {}
    current_means: dict[str, float] = {}
    bin_counts: dict[str, dict[str, Any]] = {}
    for feature in FEATURE_ORDER:
        edges = edges_for(feature, bin_count)
        reference_values = [item.as_map()[feature] for item in reference]
        current_values = [item.as_map()[feature] for item in current]
        score, reference_bins, current_bins = population_stability_index(
            reference_values,
            current_values,
            edges,
        )
        feature_psi[feature] = round(score, 6)
        reference_means[feature] = round(_mean(reference_values), 6)
        current_means[feature] = round(_mean(current_values), 6)
        bin_counts[feature] = {
            "edges": edges,
            "reference": reference_bins,
            "current": current_bins,
        }

    observed = max(feature_psi.values())
    affected = _affected_feature(feature_psi, reference_means, current_means)
    over = [
        feature
        for feature in FEATURE_ORDER
        if feature_psi[feature] >= threshold
    ]
    metrics: dict[str, Any] = {
        "method": "Population Stability Index on binned image features",
        "formula": FORMULA,
        "primary_metric": "max_psi",
        "observed_score": observed,
        "threshold": threshold,
        "threshold_label": THRESHOLD_LABEL,
        "affected_feature": affected,
        "features_over_threshold": over,
        "feature_psi": feature_psi,
        "reference_means": reference_means,
        "current_means": current_means,
        "bin_counts": bin_counts,
        "bin_count": bin_count,
        "reference_batch": reference_dir.name,
        "current_batch": current_dir.name,
        "reference_sample_count": len(reference),
        "current_sample_count": len(current),
        "reference_samples": _samples(reference),
        "current_samples": _samples(current),
        "limitations": SHIFT_LIMITATION,
    }
    findings: list[Finding] = []
    if observed >= threshold:
        findings.append(
            Finding(
                severity=Severity.MEDIUM,
                title=SHIFT_TITLE,
                method=(
                    "Population Stability Index on shared bins. "
                    f"{FORMULA} Largest PSI is {affected}. {THRESHOLD_LABEL}"
                ),
                observed_value=f"{observed:.6f}",
                threshold=f"{threshold:.2f}",
                evidence_refs=[_evidence(item) for item in current],
                limitations=SHIFT_LIMITATION,
            )
        )
    return ModuleResult(
        module=ModuleName.distribution_shift,
        status=status_from_findings(findings),
        metrics=metrics,
        findings=findings,
    )


def _proportions(counts: list[int]) -> list[float]:
    bins = len(counts)
    total = float(sum(counts))
    raw = [(count + PSI_EPSILON) / (total + PSI_EPSILON * bins) for count in counts]
    scale = sum(raw)
    return [value / scale for value in raw]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _affected_feature(
    feature_psi: dict[str, float],
    reference_means: dict[str, float],
    current_means: dict[str, float],
) -> str:
    """Feature with the largest PSI. Ties prefer the larger relative mean shift."""

    def sort_key(feature: str) -> tuple[float, float, str]:
        reference = reference_means[feature]
        relative = abs(current_means[feature] - reference) / max(abs(reference), 1e-6)
        return (feature_psi[feature], relative, feature)

    return max(FEATURE_ORDER, key=sort_key)


def _samples(items: list[ImageFeatures]) -> list[dict[str, str]]:
    return [{"sample_id": item.sample_id, "file_hash": item.file_hash} for item in items]


def _evidence(item: ImageFeatures) -> EvidenceRef:
    return EvidenceRef(
        id=f"shift-{item.sample_id}",
        sample_id=item.sample_id,
        file_hash=item.file_hash,
        evidence_type="distribution_shift",
    )
