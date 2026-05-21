"""
Technical Reference — Kyouji SHA-256 Hashing Tool
Explains the full system architecture, algorithm specification, and API contract
for technical users who need to understand exactly what is happening under the hood.
"""
import os
import sys
import streamlit as st

# Allow utils to be imported when running from the pages/ sub-directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import load_logo, inject_global_css, render_header, render_sidebar

logo_img, logo_html = load_logo()

st.set_page_config(
    page_title="Technical Reference — Kyouji",
    page_icon=logo_img,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_header(logo_html, title="Technical Reference")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
render_sidebar(BACKEND_URL)

st.markdown("---")

# ── 1. System Architecture ────────────────────────────────────────────────────
st.header("1. System Architecture")
st.markdown("""
This tool is deployed as two isolated Docker containers that communicate over a private
Docker network and share a single volume for large file transfers.

```
┌─────────────────────────┐        HTTP (internal network)        ┌──────────────────────────┐
│   Frontend Container    │ ────────────────────────────────────► │   Backend Container      │
│   Streamlit · port 8501 │                                        │   Go HTTP · port 8000    │
│                         │ ◄────────────────────────────────────  │                          │
└────────────┬────────────┘        JSON / NDJSON stream            └──────────────┬───────────┘
             │                                                                    │
             └────────────────── Shared Volume (/app/shared) ───────────────────┘
                                  (large file I/O bypass)
```

**Why a shared volume for large files?**  
Streaming a 100 MB file through the HTTP request body introduces significant network
buffering overhead inside Docker. Instead, the frontend writes the file directly to the
shared volume, then sends the backend only a lightweight JSON payload with the filenames.
The backend reads, hashes, and writes the output entirely on disk — eliminating the
network bottleneck for large workloads.
""")

# ── 2. Backend Internals ──────────────────────────────────────────────────────
st.header("2. Backend Internals")

st.subheader("2.1 Language & Runtime")
st.markdown("""
The backend is written in **Go 1.22** and compiled to a statically linked binary.
It is served by Go's standard `net/http` package with no external framework dependency.
The binary runs inside a minimal Alpine Linux container.
""")

st.subheader("2.2 SHA-256 Implementation")
st.markdown("""
Hashing is performed using [`minio/sha256-simd`](https://github.com/minio/sha256-simd),
a drop-in replacement for Go's `crypto/sha256` that automatically detects and uses
**SIMD CPU extensions** (AVX512, AVX2, ARM NEON) at runtime.

On supported hardware this delivers up to **4× throughput** compared to the standard
library implementation with zero change to output correctness — SHA-256 is a fixed
standard and the digest is identical regardless of the execution path.

**Core hashing function:**
```go
func hashBytes(data []byte) string {
    cleanData := bytes.TrimSpace(data)
    hash := sha256.Sum256(cleanData)
    return "RCMP_REDACT_" + hex.EncodeToString(hash[:])
}
```
""")

st.subheader("2.3 Concurrency Model (Disk-to-Disk Pipeline)")
st.markdown("""
For file processing, the backend uses a **producer / ordered-future / single-writer**
pipeline to maximise CPU utilisation while preserving exact CSV row ordering:

```
Scanner (single goroutine)
    │
    │  batches of 5,000 lines
    ▼
┌─────────────────────────────────────────────────────┐
│  Worker Pool  (numCPU goroutines, semaphore-limited) │
│  Each goroutine hashes its batch sequentially        │
│  and sends the result to an ordered future channel   │
└──────────────────────────┬──────────────────────────┘
                           │ ordered futures
                           ▼
                   Writer goroutine
                   (single, sequential)
                   Writes CSV rows to disk via 8 MB buffered writer
                   Emits NDJSON progress events to the HTTP stream
```

**Key design decisions:**

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| Batch size | 5,000 lines | Amortises goroutine scheduling cost without RAM spikes |
| Queue size | 4,000 futures | Limits in-memory backlog to ~20 M lines before back-pressure |
| Buffer size | 8 MB | Reduces OS `write()` syscall frequency by ~8,000× |
| Worker count | `runtime.NumCPU()` | Saturates all available cores |
""")

st.subheader("2.4 Output Format")
st.markdown("""
Every hash produced by this tool follows the format:

```
RCMP_REDACT_<64-character lowercase hexadecimal SHA-256 digest>
```

**Example:**
```
Input:   John Smith
Output:  RCMP_REDACT_ef61a579c907bbed674c0dbcbcf7f7af8f851538eef7b7e23d900d944c536cd0
```

The `RCMP_REDACT_` prefix makes redacted values unambiguous in downstream data pipelines —
a plain-text field that begins with this prefix has been deterministically redacted and
can be re-verified at any point using the original value.
""")

# ── 3. API Reference ──────────────────────────────────────────────────────────
st.header("3. API Reference")

st.markdown("The backend exposes four HTTP endpoints on port `8000`.")

with st.expander("GET /health"):
    st.markdown("""
**Response**
```json
{ "status": "healthy" }
```
""")

with st.expander("POST /hash  —  single string"):
    st.markdown("""
**Request body**
```json
{ "data": "string to hash" }
```
**Response**
```json
{ "hash": "RCMP_REDACT_<hex>" }
```
""")

with st.expander("POST /hash/bulk  —  list of strings"):
    st.markdown("""
**Request body**
```json
{ "data_list": ["string 1", "string 2", "..."] }
```
**Response**
```json
{ "hashes": ["RCMP_REDACT_<hex>", "RCMP_REDACT_<hex>", "..."] }
```
Order is preserved and guaranteed deterministic.
""")

with st.expander("POST /hash/file/disk  —  disk-to-disk file processing"):
    st.markdown("""
Both files must exist (or be created) on the shared Docker volume at `/app/shared/`.

**Request body**
```json
{
  "input_file": "input_<uuid>.txt",
  "output_file": "<uuid>_hashes.csv"
}
```
**Response** — NDJSON stream, one object per batch:
```
{"processed": 5000}
{"processed": 10000}
...
{"processed": 1042381}
```
The output CSV has a header row `Original,SHA-256 Hash` followed by one row per input line.
""")

with st.expander("GET /download/{filename}?original_name=<name>  —  file download"):
    st.markdown("""
Streams the processed CSV from `/app/shared/{filename}`.  
The optional `original_name` query parameter controls the browser's download filename:
the server strips the extension, appends `_hashed`, and serves it as `{stem}_hashed.csv`.
""")

# ── 4. Data Handling & Privacy ────────────────────────────────────────────────
st.header("4. Data Handling & Privacy")
st.markdown("""
- **No data is persisted** beyond the active session. Input files are deleted from the
  shared volume immediately after hashing completes.
- **No data leaves the Docker network.** All communication is internal; the frontend
  contacts the backend via Docker's internal DNS (`http://backend:8000`).
- **No logging of plaintext.** The audit logger records only the timestamp, source IP,
  and item count — never the input values or their hashes.
- The tool is **stateless**: restarting either container discards all in-flight state.
""")

st.divider()
st.caption("v2.0")
