import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import List
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from backend.logic import generate_hash, _hash_worker
from backend.logger import log_forensic_event
import os

app = FastAPI(title="Forensic Data Verification API")

# Hashing Engine Configuration
def get_optimal_worker_count() -> int:
    try:
        # Linux-specific: detects only CPUs assigned to the container/process
        cores = len(os.sched_getaffinity(0))
    except AttributeError:
        # Fallback for Windows or non-Linux systems
        cores = os.cpu_count() or 2
    
    # Leave 1 core as headroom for the main FastAPI process, minimum 1 worker
    return max(1, cores - 1)

MAX_HASH_WORKERS = int(os.getenv("MAX_HASH_WORKERS", get_optimal_worker_count()))

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
        num_items = len(body.data_list)
        
        # Dynamic Chunksize Logic:
        # Use a minimum of 1000. Scale chunks up for massive lists to balance IPC vs. load balancing.
        # We aim for ~4 tasks per worker to ensure good distribution.
        dynamic_chunksize = max(1000, num_items // (MAX_HASH_WORKERS * 4))
        
        # Offload the map operation to the executor using the dynamic chunk size.
        results = await loop.run_in_executor(
            None, 
            lambda: list(executor.map(_hash_worker, body.data_list, chunksize=dynamic_chunksize))
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
