# Kyouji: Hashing & Redaction Tool

*Kyouji (矜持) is a Japanese term for "pride" or "dignity"—specifically the pride one takes in unshakeable adherence to one's own principles. In this service, it represents the unwavering integrity of the SHA-256 algorithm. Like a person with 'Kyouji', the hash remains constant, truthful, and dignified, regardless of external attempts to alter its core truth.*

A tool for generating deterministic SHA-256 hashes. Used for data redaction and verification while ensuring consistency via whitespace stripping.

## Features
- **Deterministic Hashing**: SHA-256 implementation that strips leading/trailing whitespace before hashing.
- **Bulk Processing**: Multi-core hashing for large lists of strings using `ProcessPoolExecutor`.
- **API Access**: FastAPI endpoints for single and bulk hashing operations.
- **Verification Suite**: Build-time logic and API integrity checks.

## Configuration
Tuning parameters available in `.env`:
- `MAX_HASH_WORKERS`: Number of parallel workers (detected automatically with 1-core headroom).
- `HASH_CHUNK_SIZE`: Task distribution size per worker (calculated dynamically).

## Deployment
Requires Docker and Docker Compose.
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
- `tests/`: Logic and API integrity tests.

## Testing
Logic and API checks are executed automatically during the Docker build.

To run manually:
```bash
# Set PYTHONPATH to the root
$env:PYTHONPATH = "."
python tests/test_logic.py
python tests/test_api.py
```
