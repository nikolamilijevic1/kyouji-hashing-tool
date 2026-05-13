import pytest
from backend.logic import generate_hash

EXPECTED_HASH_MIXED = "cb8339b38956b6ea59aeb2c2cdbac5bd0f95f3fcdb2e706ec31ca764b2de8e0e"
EXPECTED_HASH_LOWER = "82c16ac5f2287c30f7931542b59486c1e1a3020d32cbff7e6dcb240bac8e15a5"
EXPECTED_HASH_UPPER = "ab75cd57bf0a9bc4092a22cedcac12b03129a3cb5645abc0d7646baa5b9772e4"

def test_logic():
    input1 = "  Data To Verify  "
    input2 = "data to verify"
    input3 = "DATA TO VERIFY"
    
    assert generate_hash(input1) == EXPECTED_HASH_MIXED
    assert generate_hash(input2) == EXPECTED_HASH_LOWER
    assert generate_hash(input3) == EXPECTED_HASH_UPPER
    assert generate_hash(input1) == generate_hash("Data To Verify")
    assert generate_hash(input2) != generate_hash(input3)
