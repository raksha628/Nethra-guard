## Dataset

- Total reference images: 80
- Total evaluation images: 82
- Total annotations: 542 (274 reference, 268 evaluation)
- Classes: 4 (vehicle, person, equipment, structure)
- Image formats: PNG
- Image resolutions: 640x480, 800x600, 1280x720
- Dataset ZIP: `workspace/synthetic_cv/reference_dataset.zip` and `workspace/synthetic_cv/evaluation_dataset.zip`
- Dataset size: 6.9 MB / 7.2 MB (approximate depending on compression)

## Reference Distribution

- Brightness statistics: Unmodified, standard randomized base colors
- Contrast statistics: Unmodified
- RGB statistics: Unmodified
- Dimensions: Mixed standard CV resolutions (640x480, 800x600, 1280x720)

## Evaluation Distribution

- Brightness statistics: Reduced computationally (Brightness enhanced by 0.65)
- Contrast statistics: Increased computationally (Contrast enhanced by 1.4)
- RGB statistics: Altered per enhanced brightness/contrast curves
- Dimensions: Mixed standard CV resolutions

## Injected Assurance Issues

The following anomalies were injected into the Evaluation Set specifically to trigger NETRA-Guard's Data Integrity engine:
- Duplicate Image: 1 identical image cloned with a different filename to trigger hash-based detection.
- Missing image reference: 1 COCO annotation explicitly points to a non-existent `missing_nonexistent.png` file.
- Out-of-bounds Bounding Box: 1 COCO annotation contains coordinates `[9000, 9000, 100, 100]` to exceed image boundaries.
- Extreme Aspect Ratio: 1 COCO annotation contains bounding box `[10, 10, 500, 2]` to trigger aspect ratio threshold warnings.

## NETRA-Guard Validation

- COCO parser: PASS
- Data integrity: PASS
- Distribution shift: PASS
- Provenance: PASS

## Dynamic Test

The dataset was tested end-to-end via the `POST /api/runs` API endpoint using a simulated UI request. 
Changes/Results:
- Data Integrity correctly parsed the COCO JSON and image bytes, throwing `CRITICAL` findings for the missing image reference and the `(9000, 9000, 100, 100)` invalid bbox. It correctly threw `WARNING` findings for the Extreme Bbox Aspect and the Duplicate Image bytes.
- The Distribution Shift engine parsed the Pillow images and correctly identified the pixel variation introduced programmatically between Reference/Evaluation inputs, throwing a `WARNING: Distribution shift detected` due to divergence in the `rgb_mean`.
This confirms NETRA-Guard dynamically parses and analyzes genuine anomalies in the generated dataset.

## Model

- Existing real model found: NO (using the dummy string byte artifact)
- Model inference performed: NO
- Model artifact used: `workspace/demo/demo_model.pt`
- If inference is unavailable, state why: As documented in the backend `model_adapter.py`, NETRA-Guard explicitly avoids unsafe deserialization of user-provided pickled `.pt` artifacts in this pipeline tier. It instead hashes the file for cryptographic provenance, and then executes a deterministic fallback generator that predicts bounding boxes and classes mathematically seeded by the model's SHA-256 digest to safely mock the execution cycle.

## Files Created

- `scripts/generate_synthetic_dataset.py`
- `workspace/synthetic_cv/reference/` (and contents)
- `workspace/synthetic_cv/evaluation/` (and contents)
- `workspace/synthetic_cv/reference_dataset.zip`
- `workspace/synthetic_cv/evaluation_dataset.zip`

## Files Modified

- `backend/app/services/demo_workspace.py` (Modified `_write_demo_dataset()` to integrate the synthetic evaluation zip file dynamically, falling back on the dummy structure if the generator isn't run, preserving backwards API compatibility.)

## Tests

- `npm run build`: PASS (1953 modules transformed in 2.39s)
- `pytest backend/tests -v`: PASS (31 passed, 1 warning, in 9.21s)

## Final Status

`DATASET GENERATED AND INTEGRATED`
