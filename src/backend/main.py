import asyncio
import hashlib
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import List
from fastapi import FastAPI, Request, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.logic import generate_hash, _hash_worker
from backend.logger import log_hashing_event
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    app.state.executor = ThreadPoolExecutor(max_workers=MAX_HASH_WORKERS)
    yield
    # Shutdown logic
    app.state.executor.shutdown()

app = FastAPI(title="Kyouji: Hashing API", lifespan=lifespan)

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

MAX_HASH_WORKERS = int(os.getenv("MAX_HASH_WORKERS", str(get_optimal_worker_count())))

class HashRequest(BaseModel):
    data: str

class BulkHashRequest(BaseModel):
    data_list: List[str]

class HashResponse(BaseModel):
    hash: str

class BulkHashResponse(BaseModel):
    hashes: List[str]

class DiskHashRequest(BaseModel):
    input_file: str
    output_file: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Serve a massive processed file directly using FastAPI's high-performance asynchronous FileResponse.
    """
    from fastapi.responses import FileResponse
    file_path = f"/app/shared/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/csv", filename="hashes.csv")
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/hash", response_model=HashResponse)
async def hash_single(request: Request, body: HashRequest):
    """
    Generate SHA-256 hash for a single string. Used for data redaction and verification.
    """
    try:
        result = generate_hash(body.data)
        log_hashing_event(request, items_processed=1)
        return HashResponse(hash=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hash/bulk", response_model=BulkHashResponse)
async def hash_bulk(request: Request, body: BulkHashRequest):
    """
    Generate SHA-256 hashes for a list of strings using multi-core processing.
    """
    return await _process_hashing(request, body.data_list)

@app.post("/hash/file")
async def hash_file(request: Request, file: UploadFile = File(...)):
    """
    Generate SHA-256 hashes for each line in a massive file without memory constraints.
    Returns a text/csv stream containing the original value and hash.
    """
    async def stream_row_hashing():
        loop = asyncio.get_running_loop()
        executor = request.app.state.executor
        chunk_size = 1024 * 1024
        remainder = b""
        
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                if remainder:
                    clean_line = remainder.decode('utf-8', errors='ignore').strip()
                    if clean_line:
                        hashed = await loop.run_in_executor(executor, _hash_worker, clean_line)
                        yield f"{clean_line},{hashed}\n"
                break
                
            lines = (remainder + chunk).split(b"\n")
            remainder = lines.pop()
            
            str_lines = [line.decode('utf-8', errors='ignore').strip() for line in lines if line.strip()]
            
            if str_lines:
                # Distribute the lines evenly across all available workers
                batch_size = max(1000, len(str_lines) // MAX_HASH_WORKERS)
                batches = [str_lines[i:i + batch_size] for i in range(0, len(str_lines), batch_size)]
                
                tasks = [
                    loop.run_in_executor(executor, _hash_chunk_sequentially, batch)
                    for batch in batches
                ]
                
                # asyncio.gather preserves exact deterministic order
                batch_results = await asyncio.gather(*tasks)
                chunk_hashes = [h for sublist in batch_results for h in sublist]
                
                chunk_output = "".join([f"{orig},{h}\n" for orig, h in zip(str_lines, chunk_hashes)])
                yield chunk_output
                    
    return StreamingResponse(stream_row_hashing(), media_type="text/csv")

@app.post("/hash/file/disk")
async def hash_file_disk(request: Request, body: DiskHashRequest):
    """
    Generate SHA-256 hashes using Disk-to-Disk architecture to avoid network bottleneck.
    Reads from /app/shared/{input_file} and writes to /app/shared/{output_file}.
    Yields JSON progress updates.
    """
    async def process_disk_to_disk():
        loop = asyncio.get_running_loop()
        executor = request.app.state.executor
        chunk_size = 1024 * 1024
        remainder = b""
        lines_processed = 0
        
        input_path = f"/app/shared/{body.input_file}"
        output_path = f"/app/shared/{body.output_file}"
        
        try:
            with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
                fout.write(b"Original,SHA-256 Hash\n")
                
                while True:
                    chunk = fin.read(chunk_size)
                    if not chunk:
                        if remainder:
                            clean_line = remainder.decode('utf-8', errors='ignore').strip()
                            if clean_line:
                                hashed = await loop.run_in_executor(executor, _hash_worker, clean_line)
                                fout.write(f"{clean_line},{hashed}\n".encode('utf-8'))
                                lines_processed += 1
                                yield f'{{"processed": {lines_processed}}}\n'
                        break
                        
                    lines = (remainder + chunk).split(b"\n")
                    remainder = lines.pop()
                    
                    str_lines = [line.decode('utf-8', errors='ignore').strip() for line in lines if line.strip()]
                    
                    if str_lines:
                        batch_size = max(1000, len(str_lines) // MAX_HASH_WORKERS)
                        batches = [str_lines[i:i + batch_size] for i in range(0, len(str_lines), batch_size)]
                        
                        tasks = [
                            loop.run_in_executor(executor, _hash_chunk_sequentially, batch)
                            for batch in batches
                        ]
                        
                        batch_results = await asyncio.gather(*tasks)
                        chunk_hashes = [h for sublist in batch_results for h in sublist]
                        
                        chunk_output = "".join([f"{orig},{h}\n" for orig, h in zip(str_lines, chunk_hashes)])
                        fout.write(chunk_output.encode('utf-8'))
                        
                        lines_processed += len(str_lines)
                        yield f'{{"processed": {lines_processed}}}\n'
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
                
    return StreamingResponse(process_disk_to_disk(), media_type="application/json")

def _hash_chunk_sequentially(chunk: List[str]) -> List[str]:
    """Helper function to hash a chunk sequentially without spawning new threads."""
    return [_hash_worker(item) for item in chunk]

async def _process_hashing(request: Request, data_list: List[str]):
    """
    Distribute list of strings across ThreadPoolExecutor for parallel SHA-256 hashing using chunks.
    """
    if not data_list:
        return BulkHashResponse(hashes=[])

    try:
        loop = asyncio.get_running_loop()
        num_items = len(data_list)
        executor = request.app.state.executor
        
        # Chunk the data to prevent event loop starvation and memory spikes
        # Using a static micro-batch size (5000) guarantees perfect load distribution across all workers
        chunk_size = int(os.getenv("HASH_CHUNK_SIZE", "5000"))
        chunks = [data_list[i:i + chunk_size] for i in range(0, num_items, chunk_size)]
        
        # Offload chunks directly to custom executor
        tasks = [
            loop.run_in_executor(executor, _hash_chunk_sequentially, chunk)
            for chunk in chunks
        ]
        
        # Gather all chunk results concurrently without blocking default thread pool
        chunked_results = await asyncio.gather(*tasks)
        
        # Flatten the list of lists
        results = [item for sublist in chunked_results for item in sublist]
        
        log_hashing_event(request, items_processed=len(data_list))
        return BulkHashResponse(hashes=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
