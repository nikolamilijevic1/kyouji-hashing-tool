# Kyouji: Hashing & Redaction Tool

*Kyouji (矜持) is a Japanese term for professional pride and inner dignity. In this service, it represents the unwavering integrity of the SHA-256 algorithm. Like a person with 'Kyouji', the hash remains constant, truthful, and dignified, regardless of external attempts to alter its core truth.*

A high-performance tool for generating deterministic SHA-256 hashes at scale. Used for data redaction and verification across multi-gigabyte datasets, ensuring consistency via whitespace stripping.

## Features
- **Deterministic Hashing**: SHA-256 implementation that strips leading/trailing whitespace before hashing. Output is bit-for-bit reproducible.
- **Zero-Allocation Hashing**: Backend operates strictly on native `[]byte` slices using `crypto/sha256`, eliminating string heap allocations and reducing GC pause overhead at 30M+ line scale.
- **Massive File Support**: "Disk-to-Disk" streaming architecture leverages shared Docker volumes to bypass HTTP network bottlenecks, processing multi-gigabyte files with flat memory usage and native SSD speed.
- **Buffered I/O**: Output CSV is written via an 8MB `bufio.Writer`, batching kernel syscalls from thousands down to ~375 for a 3GB file.
- **Go Backend**: Compiled Golang binary with goroutine-based concurrency, an ordered futures pattern for correct CSV output, and a backpressure queue to prevent OOM on massive files.
- **API Access**: HTTP endpoints for single hashing, bulk hashing, disk-to-disk file processing, and direct file downloads.

## Configuration
All tuning parameters are available via standard environment variables. All values have safe defaults:

| Variable | Default | Description |
|---|---|---|
| `PUBLIC_BACKEND_URL` | `http://localhost:8000` | External URL of backend, used by frontend for download links. Set this for remote/LAN deployments. |
| `SHARED_DIR` | `/app/shared/` | Shared volume path for disk-to-disk file transfers. |
| `HASH_BATCH_SIZE` | `5000` | Lines per goroutine batch. Higher = more RAM; Lower = more CPU overhead. |
| `MAX_QUEUE_SIZE` | `1000` | Ordered futures backpressure limit. Caps RAM backlog to ~5M lines. |
| `MAX_LINE_MB` | `10` | Maximum single-line size the scanner will accept (in MB). |
| `PORT` | `8000` | Backend server port. |

## Project Structure
- `src/backend/`: Compiled Go HTTP server (`main.go`, `go.mod`, `go.sum`).
- `src/frontend/`: Streamlit dashboard and isolated Python dependencies.
- `tests/`: Test suite for logic and API integrity.
- `pyproject.toml`: Root uv workspace manager (frontend only).
- `uv.lock`: Unified lock file for the frontend workspace.

## Local Development
The frontend requires [uv](https://docs.astral.sh/uv/). The backend requires [Go 1.22+](https://go.dev/dl/).

```bash
# Sync the frontend workspace
uv sync --all-packages

# Run the test suite
uv run pytest

# Run the Go backend locally (optional, Docker is preferred)
cd src/backend && go run main.go
```

## Deployment
Build and start the multi-stage Docker environment:
```bash
docker compose up --build
```
> **Note:** Docker layer caching is configured correctly — changing `main.go` does not re-download Go dependencies. Only changes to `go.mod` or `go.sum` trigger a fresh `go mod download`.

## Access
Once the containers are running:
- **Frontend UI**: [http://localhost:8501](http://localhost:8501)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Raw API**: [http://localhost:8000](http://localhost:8000)

## API Reference

### Health Check
`GET /health`
```json
{ "status": "healthy" }
```

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

### Disk-to-Disk File Processing
`POST /hash/file/disk`
Reads from the shared volume, processes concurrently, and streams JSON progress updates back to the caller.
```json
{ "input_file": "input_uuid.txt", "output_file": "hashes_uuid.csv" }
```
Response stream: `{"processed": 500000}` newline-delimited JSON.

### Direct File Download
`GET /download/{filename}`
Streams a file from the shared volume directly to the browser as a `text/csv` attachment. Fully memory-safe via `http.ServeFile`.
