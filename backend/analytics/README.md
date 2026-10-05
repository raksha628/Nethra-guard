# Analytics core

Person 2 consumes Person 1's assurance outputs. This package does not reimplement dataset parsing, SHA-256, or the ledger. It calls `check_dataset`, `check_model`, `run_inference`, `append_entry`, and `verify_ledger`.

`assurance.scenarios` still returns `distribution_shift` and `comparator` as `NOT_RUN`. Use this runner for those checks:

```bash
python -m analytics.runner NONE
python -m analytics.runner BRIGHTNESS
```

Run it from the `backend` directory. `NONE` compares the reference image batch to itself. `BRIGHTNESS`, `BLUR`, `CONTRAST`, `COLOR_CAST`, and `RESOLUTION` compare the owned batches under `fixtures/shift/`.

## Distribution shift

For each image the feature set is RGB mean and standard deviation, luminance brightness, luminance contrast, width, height, and edge density. Edge density is the share of adjacent pixels whose luminance jump is at least 24. The same function runs on both batches.

The metric is Population Stability Index on fixed bins. Color and brightness use edges `0, 36, 90, 140, 190, 255`. Size uses pixel edges. Edge density uses edges from 0 to 1. With bin proportions `r_i` and `c_i`:

```text
PSI = sum (c_i - r_i) * ln(c_i / r_i)
```

Empty bins add a small epsilon before the log. The published score is the maximum PSI across features.

The cutoff **0.10** is a prototype demo threshold, not a deployment limit.

- PSI under 0.10: `PASS`
- PSI at or above 0.10: one `MEDIUM` finding and module status `WARNING`

Shift does not use `HIGH` or `CRITICAL`, so it cannot by itself fail a run. A shift is a warning. It does not prove the model failed. Fewer than two readable images in either batch returns `NOT_RUN`.

Person 1's clean PNGs are flat color, so blur and contrast on those files would not move edge density or contrast. The shift batches are separate images with an interior edge. Rebuild them with `python fixtures/build_shift_fixtures.py` from `backend`. That script does not rewrite `fixtures/clean`, `fixtures/anomaly`, or the expected handoff JSON.

## Comparator

Two runs are comparable only when dataset hash, model hash, preprocessing, and configuration match. Otherwise the module is `NOT_RUN`, `metrics.reason` explains the mismatch, and detection deltas are omitted.

Compatible runs match boxes per `image_id` with greedy IoU on `bbox_xyxy`, preferring the same `class_id`. The result reports detection-count change, mean confidence change, class changes, mean IoU, and finding changes (`NEW`, `CLEARED`, `UNCHANGED`, `SEVERITY_CHANGE`). Precision, recall, and mAP are not computed.

The `.bin` adapter returns the same boxes for the same image id. Two clean runs show IoU 1 and zero deltas. Those detections are simulated. They are not evidence of detector drift. `fixtures/shift/simulated_detections_edited.json` is a labeled simulated edit used to show count, class, confidence, and IoU movement.

## Status

Run status is not a module and not a 0–100 score.

- `FAIL` if a required module fails or a finding is `HIGH` or `CRITICAL`
- otherwise `NOT_RUN` if a required module did not run
- otherwise `REVIEW` if a required module is `WARNING`
- otherwise `PASS`

## What this pass does not do

The React screens still use their mock data. KS-test, Wasserstein, and SSIM strings in the UI are copy. They are not implemented here.
