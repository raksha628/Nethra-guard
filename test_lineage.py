import os
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.abspath('backend'))

from app.services.demo_workspace import _write_demo_dataset
from app.services.distribution_shift import extract_features, run_distribution_shift

def test_dynamic():
    # Get the dataset
    original_zip = _write_demo_dataset()
    
    # Run baseline distribution shift (no scenario)
    features_base = extract_features(original_zip, "NONE")
    print(f"Base Features 0 (Brightness): {features_base[0].brightness}")
    
    # Run shifted distribution (scenario)
    features_shift = extract_features(original_zip, "BRIGHTNESS_SHIFT")
    print(f"Shift Features 0 (Brightness): {features_shift[0].brightness}")

    # Run the full pipeline
    baseline = {"scenario": "NONE", "thresholds": {"shiftThreshold": 0.5}}
    shifted = {"scenario": "BRIGHTNESS_SHIFT", "thresholds": {"shiftThreshold": 0.5}}

    _, findings1 = run_distribution_shift(original_zip, original_zip, "run_test_1", baseline)
    _, findings2 = run_distribution_shift(original_zip, original_zip, "run_test_2", shifted)
    
    print(f"Findings without shift: {len(findings1)}")
    print(f"Findings with shift: {len(findings2)}")
    if findings2:
        print(f"Finding value: {findings2[0].observed_value}")

test_dynamic()
