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

Performance parameters can be tuned via environment variables in `.env`:

-   `MAX_HASH_WORKERS`: Maximum concurrent worker processes (defaults to CPU count).
-   `HASH_CHUNK_SIZE`: Task size per worker (defaults to 1000) to balance IPC overhead vs. load balancing.

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
- `verify_logic.py`: Standalone verification suite.
