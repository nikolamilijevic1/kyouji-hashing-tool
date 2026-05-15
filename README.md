# Kyouji: SHA-256 Hashing & Redaction Service

A high-performance Go-based service for deterministic SHA-256 hashing. Designed for processing multi-gigabyte datasets with fixed memory overhead and bit-for-bit reproducibility.

## Technical Architecture

### Concurrency & Performance
- **SIMD Acceleration**: Utilizes `minio/sha256-simd` to leverage AVX2, AVX512, and SHA-NI hardware instructions.
- **Concurrent Hashing**: Distributes workload across `runtime.NumCPU()` goroutines using a semaphore-controlled worker pool.
- **Ordered Futures**: Implements a buffered channel-of-channels pattern to ensure output CSV rows maintain the exact order of the input file despite concurrent processing.
- **Backpressure**: The `MAX_QUEUE_SIZE` parameter acts as a flow-control mechanism, slowing the input scanner if the disk writer or CPU workers cannot keep pace, preventing OOM crashes.

### I/O Optimization
- **Disk-to-Disk Processing**: Leverages shared Docker volumes to read and write files directly to the filesystem. This bypasses the memory and network overhead of uploading/downloading multi-GB files via HTTP.
- **Buffered I/O**: 
  - **Reads**: Uses `bufio.Scanner` with a configurable buffer (default 10MB) to handle extremely long lines.
  - **Writes**: Wraps the output file in an 8MB `bufio.Writer` to batch kernel write syscalls, significantly reducing context-switching overhead.
- **Deterministic Output**: Strips leading/trailing whitespace (`bytes.TrimSpace`) before hashing. All hashes are prepended with the `RCMP_REDACT_` prefix.

## Configuration

Tuning parameters are managed via environment variables in the `.env` file:

| Variable | Default | Description |
|---|---|---|
| `HASH_BATCH_SIZE` | `5000` | Number of lines per goroutine batch. |
| `MAX_QUEUE_SIZE` | `4000` | Backpressure limit for the ordered futures queue. |
| `MAX_LINE_MB` | `10` | Maximum allowed line size for the input scanner. |
| `SHARED_DIR` | `/app/shared/` | Mount point for the shared Docker volume. |
| `PORT` | `8000` | HTTP server port. |

## Deployment

### Docker (Recommended)
Build and start the backend and Streamlit frontend:
```bash
docker compose up --build -d
```

### Local Development
Requires [uv](https://docs.astral.sh/uv/) for the frontend and [Go 1.22+](https://go.dev/dl/) for the backend.
```bash
# Sync frontend dependencies
uv sync --all-packages

# Run tests
uv run pytest

# Run Go backend
cd src/backend && go run main.go
```

## API Reference

### Hashing Endpoints
- `POST /hash`: Single string hashing. Returns JSON.
- `POST /hash/bulk`: Batch processing of JSON string arrays.
- `POST /hash/file/disk`: Processes a file from the shared volume. Returns a newline-delimited JSON stream of progress updates (`{"processed": N}`).

### File Management
- `GET /download/{filename}`: Streams a file from the shared volume as a `text/csv` attachment using `http.ServeFile`.
- `GET /health`: Standard health check.
