"""Distribution shift tests. PSI cutoffs here are prototype demonstration values."""

import shutil
from pathlib import Path

import pytest

from analytics.shift import (
    SHIFT_LIMITATION,
    check_shift,
    population_stability_index,
)
from assurance.schemas import ModuleStatus, Severity

SHIFT = Path(__file__).resolve().parents[1] / "fixtures" / "shift"
REFERENCE = SHIFT / "reference"

# The feature a controlled batch is built to move, plus features that batch cannot move.
CASES = (
    ("brightness", "brightness", ("width", "height")),
    ("blur", "edge_density", ("width", "r_mean")),
    ("contrast", "contrast", ("width", "height")),
    ("color_cast", "r_mean", ("g_mean", "b_mean", "width")),
    ("resolution", "width", ("r_mean", "g_mean", "b_mean")),
)


def test_population_stability_index_is_zero_for_identical_values():
    edges = [0.0, 1.0, 2.0]
    score, reference_counts, current_counts = population_stability_index([0.2, 0.2, 1.2], [1.2, 0.2, 0.2], edges)
    assert score == 0.0
    assert reference_counts == current_counts


def test_population_stability_index_rises_when_mass_changes_bins():
    edges = [0.0, 1.0, 2.0]
    score, reference_counts, current_counts = population_stability_index([0.2, 0.2, 0.2, 0.2], [1.2, 1.2, 1.2, 1.2], edges)
    assert reference_counts == [4, 0]
    assert current_counts == [0, 4]
    assert score > 10


def test_reference_batch_against_itself_passes():
    result = check_shift(REFERENCE, REFERENCE)
    assert result.status == ModuleStatus.PASS
    assert result.findings == []
    assert result.metrics["observed_score"] == 0.0
    assert result.metrics["threshold"] == 0.10
    assert "Prototype demonstration threshold" in result.metrics["threshold_label"]


@pytest.mark.parametrize(("batch", "feature", "unchanged"), CASES)
def test_controlled_batch_warns_on_the_transformed_feature(batch, feature, unchanged):
    result = check_shift(REFERENCE, SHIFT / batch)
    assert result.status == ModuleStatus.WARNING
    assert result.module.value == "distribution_shift"
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.severity == Severity.MEDIUM
    assert finding.severity not in {Severity.HIGH, Severity.CRITICAL}
    assert finding.limitations == SHIFT_LIMITATION
    assert "does not by itself prove the model failed" in finding.limitations
    assert "KS" not in finding.method
    assert "SSIM" not in finding.method
    assert result.metrics["affected_feature"] == feature
    assert result.metrics["feature_psi"][feature] >= result.metrics["threshold"]
    assert result.metrics["feature_psi"][feature] == result.metrics["observed_score"]
    assert feature in result.metrics["features_over_threshold"]
    for name in unchanged:
        assert result.metrics["feature_psi"][name] < result.metrics["threshold"]
    assert finding.evidence_refs
    assert finding.evidence_refs[0].file_hash is not None
    assert len(finding.evidence_refs[0].file_hash) == 64


def test_resolution_moves_height_as_well_as_width():
    result = check_shift(REFERENCE, SHIFT / "resolution")
    assert result.metrics["feature_psi"]["height"] == result.metrics["observed_score"]
    assert "height" in result.metrics["features_over_threshold"]


def test_too_few_images_is_not_run(tmp_path: Path):
    sparse = tmp_path / "sparse"
    sparse.mkdir()
    shutil.copy(next(REFERENCE.glob("*.png")), sparse / "only.png")
    result = check_shift(REFERENCE, sparse)
    assert result.status == ModuleStatus.NOT_RUN
    assert result.status != ModuleStatus.PASS
    assert result.findings == []
    assert "readable images" in result.metrics["reason"]
    assert result.metrics["current_sample_count"] == 1
