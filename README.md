# Kyouji: Hashing & Redaction Tool

*Kyouji (矜持) is a Japanese term for professional pride and inner dignity. In this service, it represents the unwavering integrity of the SHA-256 algorithm. Like a person with 'Kyouji', the hash remains constant, truthful, and dignified, regardless of external attempts to alter its core truth.*

A tool for generating deterministic SHA-256 hashes. Used for data redaction and verification while ensuring consistency via whitespace stripping.

## Features
- **Deterministic Hashing**: SHA-256 implementation that strips leading/trailing whitespace before hashing.
- **Bulk Processing**: Multi-core hashing for large lists of strings using `ProcessPoolExecutor`.
- **Massive File Support**: Zero-disk streaming architecture supports processing multi-gigabyte files without memory crashes.
- **API Access**: FastAPI endpoints for single and bulk hashing operations.
- **Verification Suite**: Build-time logic and API integrity checks.

## Configuration
Tuning parameters available in `.env` (or via standard environment variables):
- `MAX_HASH_WORKERS`: Number of parallel workers (detected automatically with 1-core headroom).
- `HASH_CHUNK_SIZE`: Task distribution size per worker (calculated dynamically).
- `PUBLIC_BACKEND_URL`: External URL of the backend (e.g., `http://192.168.1.50:8000`). Default is `http://localhost:8000`. Used to correctly route direct file downloads when deployed on a remote server.

## Project Structure
- `backend/`: FastAPI application and isolated dependencies.
- `frontend/`: Streamlit dashboard and isolated dependencies.
- `tests/`: Unified test suite for logic and API integrity.
- `pyproject.toml`: Root uv workspace manager.
- `uv.lock`: Unified lock file for the entire workspace.

## Local Development
Requires [uv](https://docs.astral.sh/uv/).

```bash
# Sync the entire workspace and hydrate the root venv
uv sync --all-packages

# Run the test suite
uv run pytest
```

## Deployment
Build and start the multi-stage Docker environment (note: the build automatically executes the test suite and will fail if tests do not pass):
```bash
docker-compose up --build
```

## Access
Once the containers are running, you can access the services at:
- **Frontend UI**: [http://localhost:8501](http://localhost:8501)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Raw API**: [http://localhost:8000](http://localhost:8000)

## API Reference

### Single Item
`POST /hash`
```json
{ "data": "string_to_hash" }
```

### Bulk Processing (JSON)
`POST /hash/bulk`
```json
{ "data_list": ["string1", "string2", "string3"] }
```

### Bulk Processing (File)
`POST /hash/file`
Accepts a plain text file (`.txt`, `.log`, or single-column `.csv`) via multipart form-data. 
- **Logic**: Each row/line is treated as a unique string to hash.
- **Normalization**: Leading/trailing whitespace is stripped.

