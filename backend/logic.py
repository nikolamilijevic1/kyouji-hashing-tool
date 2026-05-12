import hashlib
from typing import List

def _hash_worker(data: str) -> str:
    """
    Standalone worker function for ProcessPoolExecutor.
    Performs deterministic SHA-256 hashing on stripped input.
    Leading and trailing whitespace is removed to ensure only the "true" data is hashed.
    """
    return hashlib.sha256(data.strip().encode("utf-8")).hexdigest()

def generate_hash(data: str) -> str:
    """
    Generates a deterministic SHA-256 hash for an input string.
    """
    return _hash_worker(data)
