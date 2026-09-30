# NETRA-Guard analytics

Person 2 package for distribution shift, run comparison, and the run-level assurance status. It calls the assurance core. It does not reimplement dataset parsing, model hashing, or the ledger.

Detections from the demo `.bin` file are simulated. A shift is a warning about the image batch. It does not by itself prove the model failed.

## Run

From `backend`, with the virtualenv activated:

```bash
python fixtures/build_shift_fixtures.py
pytest
python -m analytics.runner NONE
python -m analytics.runner BRIGHTNESS
```

`python -m assurance.scenarios DISTRIBUTION_SHIFT` stays `NOT_RUN`. That stub belongs to the assurance core.

## Population Stability Index

For each image feature, reference and current values share fixed bins. With bin proportions `r_i` and `c_i`:

```text
PSI = sum_i (c_i - r_i) * ln(c_i / r_i)
```

Empty bins use a small epsilon so the logarithm is defined. The published score is the maximum PSI across features.

Features: per-channel RGB mean and standard deviation, brightness, contrast, width, height, and edge density. Edge density is the mean absolute difference between adjacent luminance pixels, divided by 255. Color and brightness use 10 equal bins from 0 to 255. Width and height use 10 bins of 40 pixels. Edge density uses fixed edges from 0 to 1, with a finer low end, because these fixtures sit near zero. Equal 0.1 bins would hide a blur.

The cutoff is **0.10**. That is a prototype demonstration threshold, not a deployment limit.

- PSI under 0.10: `PASS`
- PSI at or above 0.10: one `MEDIUM` finding and module `WARNING`

The finding is never `HIGH` or `CRITICAL`, so a shift cannot by itself fail the module.

## Fixtures

`fixtures/shift/reference` is a checker on a flat field, not the flat color images in `fixtures/clean`. Flat images make blur and contrast measure nothing. The generator writes that reference plus brightness, blur, contrast, color-cast, and resolution batches. It does not rewrite the assurance fixtures.

The clean `.bin` adapter returns the same box for the same image id. Comparator deltas on those boxes show that the contract is stable. They do not show prediction drift. `fixtures/shift/simulated_detections_edited.json` is a labeled edit used to test count, class, confidence, and IoU. It is not a model output.

## Comparator and status

Two runs are comparable only when the dataset hash, model hash, preprocessing, and configuration match. Otherwise the comparator is `NOT_RUN`, with the mismatched fields, and detection deltas are omitted.

On a comparable run, boxes are matched per `image_id` by greedy IoU on `bbox_xyxy`, preferring the same class. The result reports detection-count change, mean confidence change, class changes, mean IoU, and finding changes (`NEW`, `CLEARED`, `UNCHANGED`, `SEVERITY_CHANGE`). Precision, recall, and mAP are not computed.

The run status is not a score:

- `FAIL` if a required module fails or a finding is `HIGH` or `CRITICAL`
- `NOT_RUN` if a required module did not run
- `REVIEW` if a required module is `WARNING`
- `PASS` if every required module passed

A controlled shift scenario changes the configuration, so it is not compared with the clean baseline. The comparator result is still returned, and the decision notes say why the deltas were omitted. Dataset, model, and shift stay required, so a brightness shift is `REVIEW`.
