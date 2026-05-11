# Forensic Data Verification Tool

A secure, containerized service for verifying the integrity of forensic data using HMAC-SHA256. This tool provides a mechanism to validate sensitive data (e.g., documents, logs, system state) without storing or exposing the raw input.

## Security Model

The system utilizes HMAC (Hash-based Message Authentication Code) with the SHA-256 algorithm to ensure both data integrity and authenticity.

### Key Features
1.  **Secret Key Management**: The HMAC operation requires a high-entropy secret key. This key is stored in the backend environment and is never exposed to the client or logged.
2.  **Adversary Resistance**: Captured hashes cannot be verified or forged without the secret key, preventing offline brute-force attacks on the data.
3.  **Zero-Knowledge Logging**: The system does not log input data or generated hashes. Only transactional metadata (timestamp, item count) is retained for auditing purposes.
4.  **Exact-Match Verification**: Input data is processed as-is (UTF-8 encoded). Every byte, including whitespace and casing, is significant to the resulting hash.

## Architecture

The application is built on a decoupled, containerized architecture optimized for high-throughput forensic workloads.

-   **Backend**: FastAPI (Python 3.11). Implements HMAC logic and manages process-level parallelism.
-   **Frontend**: Streamlit. Interface for single and bulk verification operations.
-   **Orchestration**: Docker Compose. Ensures environment consistency across deployments.

## Core Logic & Performance

*   **Process-Level Parallelism**: CPU-bound hashing operations are offloaded to a `ProcessPoolExecutor`. This enables concurrent processing across all available CPU cores, preventing API blocking during bulk operations.
*   **Immutable Processing**: The tool does not perform normalization or transformation on the input data.

## Getting Started

### 1. Deployment
Ensure Docker and Docker Compose are installed, then run:
```bash
docker-compose up --build
```

### 2. Accessing the Tool
-   **Web Interface**: `http://localhost:8501`
-   **API Documentation (Swagger)**: `http://localhost:8000/docs`

### 3. API Usage Examples

**Single Item Verification:**
```bash
curl -X POST "http://localhost:8000/hash" \
     -H "Content-Type: application/json" \
     -d '{"data": "forensic-test-string"}'
```

**Bulk Verification:**
```bash
curl -X POST "http://localhost:8000/hash/bulk" \
     -H "Content-Type: application/json" \
     -d '{"data_list": ["string1", "string2", "string3"]}'
```

## Operational Notes
-   **Configuration**: Set the `HMAC_SECRET_KEY` in the `.env` file.
-   **Scaling**: The number of worker processes scales automatically based on the host's CPU core count.
