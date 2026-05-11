import hmac
import hashlib
from typing import List
from config import config

def generate_hash(data: str) -> str:
    """
    Generates a one-way HMAC-SHA256 hash for an input string.
    The input is treated as-is (UTF-8 encoded).
    """
    raw_data = data.encode("utf-8")
    secret_key = config.HMAC_SECRET_KEY.encode("utf-8")
    
    signature = hmac.new(
        secret_key,
        raw_data,
        hashlib.sha256
    ).hexdigest()
    
    return signature

def bulk_generate_hashes(data_list: List[str]) -> List[str]:
    """
    Helper function for bulk processing.
    """
    return [generate_hash(item) for item in data_list]
