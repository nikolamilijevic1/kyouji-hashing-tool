import hmac
import hashlib
import os

# Mock config
HMAC_SECRET_KEY = "test_secret"

def generate_hash(data: str) -> str:
    raw_data = data.encode("utf-8")
    secret_key = HMAC_SECRET_KEY.encode("utf-8")
    
    signature = hmac.new(
        secret_key,
        raw_data,
        hashlib.sha256
    ).hexdigest()
    
    return signature

def test_logic():
    # Test that normalization is NOT happening
    input1 = "  Data To Verify  "
    input2 = "data to verify"
    input3 = "DATA TO VERIFY"
    
    hash1 = generate_hash(input1)
    hash2 = generate_hash(input2)
    hash3 = generate_hash(input3)
    
    print(f"Input 1: '{input1}' -> {hash1}")
    print(f"Input 2: '{input2}' -> {hash2}")
    print(f"Input 3: '{input3}' -> {hash3}")
    
    assert hash1 != hash2, "Normalization still active (whitespace not distinct)!"
    assert hash2 != hash3, "Normalization still active (case not distinct)!"
    print("Logic verification PASSED: Data is treated as-is (no normalization).")

if __name__ == "__main__":
    test_logic()
