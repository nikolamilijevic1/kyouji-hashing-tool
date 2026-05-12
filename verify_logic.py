import sys
import os
from typing import List

# Import production logic from the backend package
from backend.logic import generate_hash, _hash_worker

# Ground Truth Hashes (SHA-256)
# Note: "  Data To Verify  " will be stripped to "Data To Verify"
EXPECTED_HASH_MIXED = "cb8339b38956b6ea59aeb2c2cdbac5bd0f95f3fcdb2e706ec31ca764b2de8e0e" # "Data To Verify"
EXPECTED_HASH_LOWER = "82c16ac5f2287c30f7931542b59486c1e1a3020d32cbff7e6dcb240bac8e15a5" # "data to verify"
EXPECTED_HASH_UPPER = "ab75cd57bf0a9bc4092a22cedcac12b03129a3cb5645abc0d7646baa5b9772e4" # "DATA TO VERIFY"

def test_logic():
    print("Starting Forensic Logic Verification (Imported from backend.logic)...")

    # Inputs with potential formatting issues
    input1 = "  Data To Verify  "  # Should strip to "Data To Verify"
    input2 = "data to verify"      # Clean lowercase
    input3 = "DATA TO VERIFY"      # Clean uppercase
    
    # Generate hashes using the actual production functions
    hash1 = generate_hash(input1)
    hash2 = generate_hash(input2)
    hash3 = generate_hash(input3)
    
    # 1. Verification against Ground Truth
    print(f"Testing individual hashing against ground truth...")
    assert hash1 == EXPECTED_HASH_MIXED, f"Hash mismatch for input1! Got {hash1}"
    assert hash2 == EXPECTED_HASH_LOWER, f"Hash mismatch for input2! Got {hash2}"
    assert hash3 == EXPECTED_HASH_UPPER, f"Hash mismatch for input3! Got {hash3}"
    
    # 2. Verify Stripping Logic
    print("Verifying whitespace stripping...")
    hash_clean = generate_hash("Data To Verify")
    assert hash1 == hash_clean, "Stripping failed: padded string doesn't match clean string!"
    
    # 3. Forensic Integrity (Casing remains significant)
    print("Verifying case sensitivity (Forensic Integrity)...")
    assert hash2 != hash3, "Forensic failure: case was normalized!"

    # 4. Batch Processing Test
    print("Testing batch processing...")
    input_batch = [input1, input2, input3]
    expected_batch = [EXPECTED_HASH_MIXED, EXPECTED_HASH_LOWER, EXPECTED_HASH_UPPER]
    
    # In verify_logic we can test the list comprehension version
    batch_results = [generate_hash(item) for item in input_batch]
    assert batch_results == expected_batch, f"Batch result mismatch!"
    
    print("-" * 40)
    print("Logic verification PASSED.")
    print("  - Successfully imported production functions.")
    print("  - Whitespace stripping is active.")
    print("  - Casing integrity is preserved.")
    print("-" * 40)

if __name__ == "__main__":
    test_logic()
