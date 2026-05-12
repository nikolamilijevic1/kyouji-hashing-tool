import sys
import os
from typing import List

# Add the project root to sys.path to allow importing from the backend package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.logic import generate_hash, _hash_worker

# Ground Truth Hashes (SHA-256)
EXPECTED_HASH_MIXED = "cb8339b38956b6ea59aeb2c2cdbac5bd0f95f3fcdb2e706ec31ca764b2de8e0e" # "Data To Verify"
EXPECTED_HASH_LOWER = "82c16ac5f2287c30f7931542b59486c1e1a3020d32cbff7e6dcb240bac8e15a5" # "data to verify"
EXPECTED_HASH_UPPER = "ab75cd57bf0a9bc4092a22cedcac12b03129a3cb5645abc0d7646baa5b9772e4" # "DATA TO VERIFY"

def test_logic():
    print("Starting Forensic Logic Verification (tests/test_logic.py)...")

    # Inputs
    input1 = "  Data To Verify  "
    input2 = "data to verify"
    input3 = "DATA TO VERIFY"
    
    # Generate hashes
    hash1 = generate_hash(input1)
    hash2 = generate_hash(input2)
    hash3 = generate_hash(input3)
    
    # Verification
    assert hash1 == EXPECTED_HASH_MIXED
    assert hash2 == EXPECTED_HASH_LOWER
    assert hash3 == EXPECTED_HASH_UPPER
    
    # Verify Stripping
    assert hash1 == generate_hash("Data To Verify")
    
    # Verify Case Sensitivity
    assert hash2 != hash3

    print("-" * 40)
    print("Logic verification PASSED.")
    print("-" * 40)

if __name__ == "__main__":
    test_logic()
