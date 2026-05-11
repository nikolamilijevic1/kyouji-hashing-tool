import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import List
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from logic import generate_hash, bulk_generate_hashes
from logger import log_forensic_event
import os

app = FastAPI(title="Forensic Data Verification API")

# Initialize ProcessPoolExecutor
# Note: In a production environment, you might want to tune max_workers
executor = ProcessPoolExecutor(max_workers=os.cpu_count())

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
    Generate HMAC-SHA256 hash for a single string.
    """
    try:
        # Single hash is fast enough to run in the main thread/loop, 
        # but for consistency and to avoid blocking the event loop 
        # if it were more complex, we'd offload it.
        # For a single string, standard execution is fine.
        result = generate_hash(body.data)
        log_forensic_event(request, items_processed=1)
        return HashResponse(hash=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hash/bulk", response_model=BulkHashResponse)
async def hash_bulk(request: Request, body: BulkHashRequest):
    """
    Generate HMAC-SHA256 hashes for a list of strings using multi-core processing.
    """
    if not body.data_list:
        return BulkHashResponse(hashes=[])

    try:
        # Offload CPU-bound task to ProcessPoolExecutor
        loop = asyncio.get_event_loop()
        
        # Split the list into chunks for better parallelization if needed, 
        # but for simplicity, we'll pass the whole list to the executor 
        # which will handle the distribution if we wrap it correctly.
        # Or more effectively, we map the generate_hash function.
        
        # Using loop.run_in_executor with ProcessPoolExecutor
        results = await loop.run_in_executor(
            executor, 
            bulk_generate_hashes, 
            body.data_list
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
