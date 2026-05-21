package main

import (
	"bufio"
	"bytes"
	sha256 "github.com/minio/sha256-simd"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
)

// Define request and response structures
type HashRequest struct {
	Data string `json:"data"`
}

type HashResponse struct {
	Hash string `json:"hash"`
}

type BulkHashRequest struct {
	DataList []string `json:"data_list"`
}

type BulkHashResponse struct {
	Hashes []string `json:"hashes"`
}

type DiskHashRequest struct {
	InputFile  string `json:"input_file"`
	OutputFile string `json:"output_file"`
}

// Configuration Helpers
func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}

func getEnvAsInt(key string, fallback int) int {
	valueStr := getEnv(key, "")
	if value, err := strconv.Atoi(valueStr); err == nil {
		return value
	}
	return fallback
}

// Worker function to hash a byte slice directly
func hashBytes(data []byte) string {
	cleanData := bytes.TrimSpace(data)
	hash := sha256.Sum256(cleanData)
	return "RCMP_REDACT_" + hex.EncodeToString(hash[:])
}

// Handlers
func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func hashSingleHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req HashRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	resp := HashResponse{Hash: hashStringCompat(req.Data)}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func hashStringCompat(data string) string {
	return hashBytes([]byte(data))
}

func hashBulkHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req BulkHashRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	numWorkers := runtime.NumCPU()
	if numWorkers < 1 {
		numWorkers = 1
	}

	// Process bulk hashes concurrently
	hashes := make([]string, len(req.DataList))
	var wg sync.WaitGroup
	semaphore := make(chan struct{}, numWorkers)

	for i, data := range req.DataList {
		wg.Add(1)
		semaphore <- struct{}{}
		go func(idx int, d string) {
			defer wg.Done()
			hashes[idx] = hashStringCompat(d)
			<-semaphore
		}(i, data)
	}
	wg.Wait()

	resp := BulkHashResponse{Hashes: hashes}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func hashFileDiskHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req DiskHashRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Prepare streaming response
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Transfer-Encoding", "chunked")
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	sharedDir := getEnv("SHARED_DIR", "/app/shared/")
	inputPath := filepath.Join(sharedDir, filepath.Base(req.InputFile))
	outputPath := filepath.Join(sharedDir, filepath.Base(req.OutputFile))

	inFile, err := os.Open(inputPath)
	if err != nil {
		http.Error(w, "Could not open input file", http.StatusBadRequest)
		return
	}
	// Defer file closing and deletion
	defer func() {
		inFile.Close()
		os.Remove(inputPath)
	}()

	outFile, err := os.Create(outputPath)
	if err != nil {
		http.Error(w, "Could not create output file", http.StatusInternalServerError)
		return
	}
	// Wrap output in an 8MB buffered writer to batch OS syscalls.
	// Without this, every chunk write triggers a kernel syscall, which is extremely expensive at scale.
	bufWriter := bufio.NewWriterSize(outFile, 8*1024*1024)
	defer func() {
		bufWriter.Flush() // Flush remaining bytes to disk before closing
		outFile.Close()
	}()

	_, err = bufWriter.WriteString("Original,SHA-256 Hash\n")
	if err != nil {
		http.Error(w, "Could not write to output file", http.StatusInternalServerError)
		return
	}

	// Concurrency setup
	numWorkers := runtime.NumCPU()
	if numWorkers < 1 {
		numWorkers = 1
	}

	// ARCHITECTURE NOTE: BATCH SIZE & QUEUE SIZE
	// Why 5000 (Batch Size)?
	// Spawning a goroutine for every single line is inefficient due to context switching.
	// Grouping 5000 lines ensures each CPU core has enough work to do per routine.
	// Increasing this heavily will cause memory spikes; decreasing it will increase CPU overhead.
	//
	// Why 1000 (Queue Size)?
	// The futures channel acts as critical Backpressure. Since we must preserve exact CSV row
	// ordering, we have a single sequential Writer goroutine. If the CPU hashes faster than the SSD
	// can write, the results pile up in RAM. A queue of 1000 limits the backlog to ~5 million lines.
	// Increasing this risks an Out-Of-Memory (OOM) crash on massive files. Decreasing this risks
	// starving the CPU workers while they wait for the single slow disk writer.
	//
	// LIMITATIONS:
	// Go's concurrency is massive, but we are ultimately bottlenecked by the OS Disk I/O speed.
	batchSize := getEnvAsInt("HASH_BATCH_SIZE", 5000)
	semaphore := make(chan struct{}, numWorkers)

	queueSize := getEnvAsInt("MAX_QUEUE_SIZE", 4000)
	// Channel to maintain order of futures
	futures := make(chan chan string, queueSize)

	// Writer goroutine
	writeDone := make(chan struct{})
	linesProcessed := 0

	go func() {
		for future := range futures {
			chunkOutput := <-future
			bufWriter.WriteString(chunkOutput)

			// Count newlines to determine lines processed in this chunk
			linesProcessed += strings.Count(chunkOutput, "\n")

			// Stream JSON update
			progressUpdate := fmt.Sprintf("{\"processed\": %d}\n", linesProcessed)
			w.Write([]byte(progressUpdate))
			flusher.Flush()
		}
		close(writeDone)
	}()

	scanner := bufio.NewScanner(inFile)
	maxLineMB := getEnvAsInt("MAX_LINE_MB", 10)
	// Increase scanner buffer size for very long lines if necessary (e.g. 1MB buffer)
	buf := make([]byte, 1024*1024)
	scanner.Buffer(buf, maxLineMB*1024*1024)

	var currentBatch [][]byte

	dispatchBatch := func(batch [][]byte) {
		future := make(chan string, 1)
		futures <- future
		semaphore <- struct{}{}

		go func(b [][]byte, f chan string) {
			defer func() { <-semaphore }()
			var sb strings.Builder
			for _, lineBytes := range b {
				if len(lineBytes) > 0 {
					hash := hashBytes(lineBytes)
					sb.Write(lineBytes)
					sb.WriteString(",")
					sb.WriteString(hash)
					sb.WriteString("\n")
				}
			}
			f <- sb.String()
			close(f)
		}(batch, future)
	}

	for scanner.Scan() {
		rawBytes := scanner.Bytes()
		cleanLine := bytes.TrimSpace(rawBytes)
		if len(cleanLine) > 0 {
			// We MUST copy the bytes because scanner.Bytes() is volatile and will be overwritten
			// Using bytes.Clone leverages Go 1.20+ internal optimizations
			lineCopy := bytes.Clone(cleanLine)
			currentBatch = append(currentBatch, lineCopy)
			if len(currentBatch) >= batchSize {
				dispatchBatch(currentBatch)
				currentBatch = nil // allocate new slice next loop
			}
		}
	}

	if len(currentBatch) > 0 {
		dispatchBatch(currentBatch)
	}

	close(futures)
	<-writeDone

	if err := scanner.Err(); err != nil {
		log.Printf("Scanner error: %v", err)
	}
}

func downloadFileHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	filename := strings.TrimPrefix(r.URL.Path, "/download/")
	if filename == "" {
		http.Error(w, "Filename required", http.StatusBadRequest)
		return
	}

	sharedDir := getEnv("SHARED_DIR", "/app/shared/")
	safeFilename := filepath.Base(filename)
	filePath := filepath.Join(sharedDir, safeFilename)
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		http.Error(w, "File not found", http.StatusNotFound)
		return
	}

	originalName := r.URL.Query().Get("original_name")
	downloadName := safeFilename
	if originalName != "" {
		baseName := originalName
		if idx := strings.LastIndex(originalName, "."); idx != -1 {
			baseName = originalName[:idx]
		}
		if strings.HasSuffix(baseName, "_hashes") {
			baseName = strings.TrimSuffix(baseName, "_hashes")
		} else if strings.HasSuffix(baseName, "_hashed") {
			baseName = strings.TrimSuffix(baseName, "_hashed")
		}
		downloadName = baseName + "_hashed.csv"
	}

	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s\"", downloadName))
	http.ServeFile(w, r, filePath)
}

func main() {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", healthCheckHandler)
	mux.HandleFunc("/hash", hashSingleHandler)
	mux.HandleFunc("/hash/bulk", hashBulkHandler)
	mux.HandleFunc("/hash/file/disk", hashFileDiskHandler)
	mux.HandleFunc("/download/", downloadFileHandler)

	port := getEnv("PORT", "8000")
	log.Printf("Starting Go backend server on port %s...", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatalf("Could not start server: %v", err)
	}
}
