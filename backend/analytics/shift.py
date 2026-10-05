"""Population Stability Index between a reference image batch and a current batch.

The published score is the maximum PSI across features. The 0.10 cutoff is a
prototype demo threshold, not a deployment limit. A shift is a warning. It
does not fail the module and does not prove the model failed.
"""

from __future__ import annotations

import math
from pathlib import Path

from assurance.hashing import sha256_file
from assurance.schemas import (
    EvidenceRef,
    Finding,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    Severity,
)

from .features import ImageFeatures, extract_directory, feature_names, feature_value

PSI_CUTOFF = 0.10
MIN_READABLE_IMAGES = 2
# Fixed demo bins. Color and brightness share 0–255 edges. Size uses pixel edges.
# Edge density uses 0–1 edges. These are prototype bins, not learned quantiles.
COLOR_EDGES = [0, 36, 90, 140, 190, 255]
SIZE_EDGES = [0, 24, 40, 56, 80, 128, 256, 1024]
DENSITY_EDGES = [0, 0.02, 0.05, 0.10, 0.20, 0.40, 0.70, 1.0]
BIN_COUNT = len(COLOR_EDGES) - 1
COLOR_FEATURES = {
    "red_mean",
    "green_mean",
    "blue_mean",
    "red_std",
    "green_std",
    "blue_std",
    "brightness",
    "contrast",
}
SIZE_FEATURES = {"width", "height"}
SHIFT_LIMITATION = (
    "A distribution shift is a warning signal. It does not prove the model failed, "
    "and it does not by itself show an attack. The 0.10 PSI cutoff is a prototype "
    "demo threshold, not a deployment limit."
)
TOO_FEW_REASON = "Too few readable images to estimate distribution shift."


def check_shift(reference_dir: Path, current_dir: Path) -> ModuleResult:
    reference, reference_skipped = extract_directory(reference_dir)
    current, current_skipped = extract_directory(current_dir)
    if len(reference) < MIN_READABLE_IMAGES or len(current) < MIN_READABLE_IMAGES:
        return ModuleResult(
            module=ModuleName.distribution_shift,
            status=ModuleStatus.NOT_RUN,
            metrics={
                "reason": TOO_FEW_REASON,
                "readable_reference": len(reference),
                "readable_current": len(current),
                "minimum_readable_images": MIN_READABLE_IMAGES,
                "psi_cutoff": PSI_CUTOFF,
                "threshold_label": "prototype demo threshold, not a deployment limit",
                "limitations": SHIFT_LIMITATION,
                "skipped_reference": reference_skipped,
                "skipped_current": current_skipped,
            },
            findings=[],
        )

    per_feature: dict[str, dict[str, object]] = {}
    for name in feature_names():
        edges = _edges_for(name)
        ref_values = [feature_value(item, name) for item in reference]
        cur_values = [feature_value(item, name) for item in current]
        score, ref_counts, cur_counts = population_stability_index(ref_values, cur_values, edges)
        per_feature[name] = {
            "psi": round(score, 6),
            "reference_mean": round(sum(ref_values) / len(ref_values), 6),
            "current_mean": round(sum(cur_values) / len(cur_values), 6),
            "reference_bin_counts": ref_counts,
            "current_bin_counts": cur_counts,
        }

    max_psi = max(float(item["psi"]) for item in per_feature.values())
    features_at_max = [
        name for name, item in per_feature.items() if abs(float(item["psi"]) - max_psi) <= 1e-3
    ]
    max_feature = max(
        features_at_max,
        key=lambda name: abs(float(per_feature[name]["current_mean"]) - float(per_feature[name]["reference_mean"])),
    )
    metrics: dict[str, object] = {
        "psi": max_psi,
        "max_feature": max_feature,
        "features_at_max_psi": features_at_max,
        "psi_cutoff": PSI_CUTOFF,
        "threshold_label": "prototype demo threshold, not a deployment limit",
        "method": "Population Stability Index. The published score is the maximum PSI across features.",
        "per_feature": per_feature,
        "reference_sample_ids": [item.sample_id for item in reference],
        "current_sample_ids": [item.sample_id for item in current],
        "reference_hashes": {item.sample_id: item.sha256 for item in reference},
        "current_hashes": {item.sample_id: item.sha256 for item in current},
        "readable_reference": len(reference),
        "readable_current": len(current),
        "skipped_reference": reference_skipped,
        "skipped_current": current_skipped,
        "limitations": SHIFT_LIMITATION,
    }
    if max_psi < PSI_CUTOFF:
        return ModuleResult(
            module=ModuleName.distribution_shift,
            status=ModuleStatus.PASS,
            metrics=metrics,
            findings=[],
        )
    return ModuleResult(
        module=ModuleName.distribution_shift,
        status=ModuleStatus.WARNING,
        metrics=metrics,
        findings=[
            Finding(
                severity=Severity.MEDIUM,
                title="Image distribution shift exceeds the prototype threshold",
                method=(
                    "Population Stability Index on shared bins of image features. "
                    "The published score is the maximum PSI across features. "
                    "The cutoff is a prototype demo threshold, not a deployment limit."
                ),
                observed_value=f"{max_psi:.4f} ({max_feature})",
                threshold=f"{PSI_CUTOFF:.2f}",
                evidence_refs=[_evidence(item) for item in current],
                limitations=SHIFT_LIMITATION,
            )
        ],
    )


def population_stability_index(
    reference: list[float],
    current: list[float],
    edges: list[float],
    epsilon: float = 1e-4,
) -> tuple[float, list[int], list[int]]:
    """PSI = sum (c_i - r_i) * ln(c_i / r_i), with epsilon so an empty bin is safe."""
    bin_count = len(edges) - 1
    reference_counts = [0] * bin_count
    current_counts = [0] * bin_count
    for value in reference:
        reference_counts[_bin_index(value, edges)] += 1
    for value in current:
        current_counts[_bin_index(value, edges)] += 1
    reference_total = sum(reference_counts) + epsilon * bin_count
    current_total = sum(current_counts) + epsilon * bin_count
    score = 0.0
    for reference_count, current_count in zip(reference_counts, current_counts):
        reference_proportion = (reference_count + epsilon) / reference_total
        current_proportion = (current_count + epsilon) / current_total
        score += (current_proportion - reference_proportion) * math.log(current_proportion / reference_proportion)
    return score, reference_counts, current_counts


def _edges_for(feature_name: str) -> list[float]:
    if feature_name in COLOR_FEATURES:
        return COLOR_EDGES
    if feature_name in SIZE_FEATURES:
        return SIZE_EDGES
    return DENSITY_EDGES


def _bin_index(value: float, edges: list[float]) -> int:
    if value <= edges[0]:
        return 0
    last = len(edges) - 2
    if value >= edges[-1]:
        return last
    for index in range(len(edges) - 1):
        if edges[index] <= value < edges[index + 1]:
            return index
    return last


def _evidence(features: ImageFeatures) -> EvidenceRef:
    digest = features.sha256 or sha256_file(Path(features.sample_id))
    return EvidenceRef(
        id=f"shift-{features.sample_id}",
        sample_id=features.sample_id,
        file_hash=digest,
        evidence_type="image_features",
    )
