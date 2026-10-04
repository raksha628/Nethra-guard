import json
import time
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # Initialize
    ws = client.get("/api/demo/workspace")
    ws_data = ws.json()
    print("Workspace:", ws_data["name"])

    # Post Run
    payload = {
        "datasetId": "ds_coco128",
        "modelId": "model_yolov8n",
        "referenceDatasetId": "ds_demo_01",
        "configuration": {
            "checks": ["DATA_INTEGRITY", "MODEL_INTEGRITY", "DISTRIBUTION_SHIFT", "COMPARATOR"]
        }
    }
    resp = client.post(f"/api/workspaces/{ws_data["workspace_id"]}/runs", json=payload)
    run_data = resp.json()
    print("Run created:", run_data["id"])

    # Poll
    for _ in range(15):
        r = client.get(f"/api/runs/{run_data['id']}/report")
        d = r.json()
        if d.get("run_state") in ["COMPLETED", "FAILED"]:
            print("\n=== FINAL METRICS ===")
            print(json.dumps(d.get("model_evaluation"), indent=2))
            break
        time.sleep(1)
