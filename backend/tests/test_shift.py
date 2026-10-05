import json
from pathlib import Path

from PIL import Image

from analytics.shift import PSI_CUTOFF, check_shift

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "shift"
REFERENCE = FIXTURES / "reference"
EXPECTED_FEATURE = {
    "brightness": "brightness",
    "blur": "edge_density",
    "contrast": "contrast",
    "color_cast": "red_mean",
    "resolution": "width",
}


def test_identical_reference_batch_passes_with_near_zero_psi():
    result = check_shift(REFERENCE, REFERENCE)
    assert result.status.value == "PASS"
    assert result.findings == []
    assert result.metrics["psi"] < 0.01
    assert result.metrics["psi"] < PSI_CUTOFF
    assert "prototype demo threshold" in result.metrics["threshold_label"]
    assert "does not prove the model failed" in result.metrics["limitations"]


def test_each_transformed_batch_warns_on_the_changed_feature():
    for scenario, feature in EXPECTED_FEATURE.items():
        result = check_shift(REFERENCE, FIXTURES / scenario)
        assert result.status.value == "WARNING", scenario
        assert result.findings[0].severity.value == "MEDIUM"
        assert "warning" in result.findings[0].limitations.lower() or "does not prove" in result.findings[0].limitations
        assert feature in result.metrics["features_at_max_psi"], scenario
        assert result.metrics["per_feature"][feature]["psi"] >= PSI_CUTOFF
        assert abs(result.metrics["per_feature"][feature]["psi"] - result.metrics["psi"]) <= 1e-3
        assert result.metrics["reference_hashes"]
        assert result.metrics["current_hashes"]
        assert result.metrics["per_feature"][feature]["reference_bin_counts"]


def test_too_few_readable_images_is_not_run(tmp_path: Path):
    sparse = tmp_path / "sparse"
    sparse.mkdir()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(sparse / "only.png")
    result = check_shift(REFERENCE, sparse)
    assert result.status.value == "NOT_RUN"
    assert result.findings == []
    assert result.metrics["reason"].startswith("Too few readable")
    assert result.metrics["readable_current"] == 1


def test_shift_fixtures_do_not_replace_person_1_datasets():
    clean = json.loads((FIXTURES.parents[0] / "clean" / "annotations.json").read_text(encoding="utf-8"))
    assert {image["file_name"] for image in clean["images"]} == {
        "img_001.png",
        "img_002.png",
        "img_003.png",
        "img_004.png",
    }
