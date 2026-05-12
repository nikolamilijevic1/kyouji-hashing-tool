import sys
import os
from fastapi.testclient import TestClient

# Add the project root to sys.path to import production logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

client = TestClient(app)

def test_api_endpoints():
    print("Starting End-to-End API Verification (tests/test_api.py)...")

    # 1. Test Single Hash Endpoint
    print("Testing /hash (Single)...")
    payload_single = {"data": "  Test String  "}
    expected_hash = "30c6ff7a44f7035af933babaea771bf177fc38f06482ad06434cbcc04de7ac14"
    
    response = client.post("/hash", json=payload_single)
    assert response.status_code == 200
    assert response.json()["hash"] == expected_hash
    print("  - Single hash verified.")

    # 2. Test Bulk Hash Endpoint
    print("Testing /hash/bulk...")
    payload_bulk = {
        "data_list": [
            "  Test String  ",
            "data to verify",
            "DATA TO VERIFY"
        ]
    }
    expected_hashes = [
        "30c6ff7a44f7035af933babaea771bf177fc38f06482ad06434cbcc04de7ac14",
        "82c16ac5f2287c30f7931542b59486c1e1a3020d32cbff7e6dcb240bac8e15a5",
        "ab75cd57bf0a9bc4092a22cedcac12b03129a3cb5645abc0d7646baa5b9772e4"
    ]

    response = client.post("/hash/bulk", json=payload_bulk)
    assert response.status_code == 200
    assert response.json()["hashes"] == expected_hashes
    print("  - Bulk hashing verified.")

    print("-" * 40)
    print("API FULL-STACK VERIFICATION PASSED.")
    print("-" * 40)

if __name__ == "__main__":
    try:
        test_api_endpoints()
    except Exception as e:
        print(f"\nAPI TEST FAILED: {str(e)}")
        sys.exit(1)
