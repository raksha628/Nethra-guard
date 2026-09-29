"""Person 1 assurance core

Offline checks for dataset integrity, model fingerprints, a deterministic
inference contract, and the provenance hash chain. Distribution shift and the
baseline comparator are not implemented here.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python fixtures/build_fixtures.py
pytest
```

Run one scenario and print the handoff JSON:

```bash
python -m assurance.scenarios NONE
python -m assurance.scenarios DATA_ANOMALY
python -m assurance.scenarios MODEL_MISMATCH
```

## What was actually tested

- Annotation format: COCO JSON only (`images`, `annotations`, `categories`, bbox `[x, y, width, height]`). YOLO labels are not parsed.
- Hash method: SHA-256 of file bytes. Dataset fingerprint is SHA-256 of canonical JSON containing the annotation-file hash and each image hash.
- Images: Pillow decode of the bundled PNG fixtures.
- Model artifacts: a `.bin` stand-in compared with the hash in `fixtures/baseline_manifest.json`. No framework metadata is invented.
- Inference: simulated. `DeterministicAdapter` returns fixed boxes for the demo image ids and sets `simulated: true`. ONNX and YOLO weights are not bundled, were not executed, and are not claimed as supported.
- Ledger: `current_hash = SHA256(canonical_json(entry_without_current_hash) + previous_hash)`. The first previous hash is 64 zero characters. The verifier reports `VALID` or the first broken sequence.

## Scenarios

| Scenario | Dataset | Model | Expected |
| --- | --- | --- | --- |
| `NONE` | clean | baseline bytes | data `PASS`, model `PASS` |
| `DATA_ANOMALY` | duplicate, missing file, out-of-bounds box, invalid class id | baseline bytes | data `FAIL` |
| `MODEL_MISMATCH` | clean | altered bytes | model `FAIL` |
| `DISTRIBUTION_SHIFT` | not run | not run | every module `NOT_RUN` |

`distribution_shift` and `comparator` are `NOT_RUN` in every scenario this package executes.

## Prototype thresholds

These are demonstration thresholds, not deployment limits.

- Exact duplicate: more than 1 file with the same SHA-256 (`WARNING`)
- Extreme aspect ratio: `max(width/height, height/width) > 8` (`WARNING`)
- Class imbalance: `max(count) / min(count) >= 4` across at least two classes (`WARNING`)
- Resolution outlier: width or height more than 50% away from the median, when at least 4 images decode (`WARNING`)

Critical structural failures (`FAIL`): malformed COCO, missing or undecodable images, non-positive boxes, boxes outside the image, invalid class ids, and paths that leave the dataset directory.

A model hash mismatch means the file differs from the registered baseline. It does not prove malicious tampering. Exact duplicate bytes do not prove poisoning.

## Handoff files

- `fixtures/expected_clean.json`
- `fixtures/expected_anomaly.json`
- `fixtures/normalized_detections.json` for the analytics workstream

Module results use the shared snake_case contract (`observed_value`, `evidence_refs`, `method`, `limitations`). Ledger entries use the frontend provenance names (`datasetHash`, `modelHash`, `configHash`, `summaryHash`, `previousHash`, `currentHash`).
