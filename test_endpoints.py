import urllib.request
import json

BASE_URL = "http://127.0.0.1:8001"

def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def post_json(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def test_flow():
    print("Fetching demo workspace...")
    ws = get_json(f"{BASE_URL}/api/demo/workspace")
    dataset_id = ws["dataset"]["asset_id"]
    model_id = ws["model"]["asset_id"]
    workspace_id = ws["workspace_id"]
    
    print("Creating run...")
    run_req = {
        "workspace_id": workspace_id,
        "dataset_asset_id": dataset_id,
        "model_asset_id": model_id,
        "checks": ["DATA_INTEGRITY", "MODEL_INTEGRITY", "DISTRIBUTION_SHIFT"],
        "configuration": {"scenario": "BRIGHTNESS_SHIFT", "thresholds": {"shiftThreshold": 0.5}}
    }
    run = post_json(f"{BASE_URL}/api/runs", run_req)
    print("Run Response:", run["id"], run["state"])
    run_id = run["id"]
    
    print("Fetching findings...")
    findings = get_json(f"{BASE_URL}/api/runs/{run_id}/findings")
    print(f"Got {len(findings)} findings.")
    
    print("Fetching evidence...")
    evidence = get_json(f"{BASE_URL}/api/runs/{run_id}/evidence")
    print(f"Got {len(evidence)} evidence samples.")
    
    print("Creating second run for comparator...")
    run_req["configuration"]["scenario"] = "MODEL_MISMATCH"
    run2 = post_json(f"{BASE_URL}/api/runs", run_req)
    run_id2 = run2["id"]
    
    print("Fetching comparator...")
    cmp = get_json(f"{BASE_URL}/api/runs/{run_id2}/compare?baseline_run_id={run_id}")
    print("Comparator Output is_compatible:", cmp["compatibility"]["is_compatible"])
    
    print("Fetching ledger...")
    ledger = get_json(f"{BASE_URL}/api/ledger")
    print(f"Got {len(ledger['entries'])} ledger entries. Verification: {ledger['verification']['status']}")
    
    print("Fetching report...")
    report = get_json(f"{BASE_URL}/api/runs/{run_id2}/report")
    print("Report generated successfully.")
    
    print("All backend tests PASSED!")

if __name__ == "__main__":
    test_flow()
