import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import List
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from logic import generate_hash, _hash_worker
from logger import log_forensic_event
import os

app = FastAPI(title="Forensic Data Verification API")

# Hashing Engine Configuration
MAX_HASH_WORKERS = int(os.getenv("MAX_HASH_WORKERS", os.cpu_count() or 4))
DEFAULT_CHUNK_SIZE = int(os.getenv("HASH_CHUNK_SIZE", 1000))

# Initialize ProcessPoolExecutor
executor = ProcessPoolExecutor(max_workers=MAX_HASH_WORKERS)

class HashRequest(BaseModel):
    data: str

class BulkHashRequest(BaseModel):
    data_list: List[str]

class HashResponse(BaseModel):
    hash: str

class BulkHashResponse(BaseModel):
    hashes: List[str]

@app.post("/hash", response_model=HashResponse)
async def hash_single(request: Request, body: HashRequest):
    """
    Generate SHA-256 hash for a single string. Used for data redaction and verification.
    """
    try:
        result = generate_hash(body.data)
        log_forensic_event(request, items_processed=1)
        return HashResponse(hash=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hash/bulk", response_model=BulkHashResponse)
async def hash_bulk(request: Request, body: BulkHashRequest):
    """
    Generate SHA-256 hashes for a list of strings using multi-core processing.
    """
    if not body.data_list:
        return BulkHashResponse(hashes=[])

    try:
        loop = asyncio.get_running_loop()
        
        # Offload the map operation to the executor using the defined chunk size.
        results = await loop.run_in_executor(
            None, 
            lambda: list(executor.map(_hash_worker, body.data_list, chunksize=DEFAULT_CHUNK_SIZE))
        )
        
        log_forensic_event(request, items_processed=len(body.data_list))
        return BulkHashResponse(hashes=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    executor.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
