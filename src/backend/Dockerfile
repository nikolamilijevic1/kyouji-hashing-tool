# Stage 1: Builder
FROM golang:1.22-alpine AS builder

WORKDIR /app

# --- Dependency Layer (cached until go.mod/go.sum change) ---
# Copy dependency files first so Docker caches the downloaded modules.
# Changes to main.go will NOT re-trigger this expensive download step.
COPY src/backend/go.mod ./
COPY src/backend/go.sum ./
RUN go mod download

# --- Source Layer (only re-triggers go build) ---
COPY src/backend/main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o kyouji-backend main.go

# Stage 2: Runner
FROM alpine:latest

WORKDIR /app
COPY --from=builder /app/kyouji-backend .

EXPOSE 8000
CMD ["./kyouji-backend"]
