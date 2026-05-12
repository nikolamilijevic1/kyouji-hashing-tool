# SHA-256 Redaction Tool

A high-performance service for deterministic data hashing and redaction.

## Core Features

-   **Deterministic Hashing**: Implements raw SHA-256. Leading and trailing whitespace is stripped before hashing; casing is preserved.
-   **Parallel Processing**: Utilizes `ProcessPoolExecutor` for CPU-bound tasks. Bulk operations are optimized via `executor.map` with configurable chunking.
-   **Automated Build Verification**: Cryptographic logic is validated against hardcoded ground-truth hashes during the Docker build process (`verify_logic.py`).

## Technical Stack

-   **Backend**: FastAPI (Python 3.11).
-   **Frontend**: Streamlit.
-   **Orchestration**: Docker Compose.

## Configuration

### Performance Tuning
- `MAX_HASH_WORKERS`: Auto-detected via `os.sched_getaffinity` (container-aware) with 1 core reserved for system headroom.
- `HASH_CHUNK_SIZE`: Dynamically calculated based on workload to optimize multi-core distribution.

## Deployment

```bash
docker-compose up --build
```

## API Reference

### Single Item
`POST /hash`
```json
{ "data": "string_to_hash" }
```

### Bulk Processing
`POST /hash/bulk`
```json
{ "data_list": ["string1", "string2", "string3"] }
```

## Project Structure
- `backend/`: FastAPI application and hashing logic.
- `frontend/`: Streamlit dashboard.
- `tests/`: Dedicated test suite (Logic & API).

## Testing
Logic and API integrity checks are executed automatically during the Docker build.

To run manually:
```bash
# Set PYTHONPATH to the root
$env:PYTHONPATH = "."
python tests/test_logic.py
python tests/test_api.py
```
