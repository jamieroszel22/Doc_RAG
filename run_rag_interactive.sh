#!/bin/bash
# Run Ollama RAG interactive session

echo "Starting Ollama RAG interactive session..."

# Base directory
BASE_DIR="/Users/jamieroszel/Desktop/Docling RAG"
SCRIPTS_DIR="$BASE_DIR/scripts"
CHUNKS_DIR="$BASE_DIR/processed_redbooks/chunks"
CACHE_DIR="$BASE_DIR/processed_redbooks/embeddings_cache"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

# Check if chunks exist
chunk_count=$(find "$CHUNKS_DIR" -name "*_chunks.json" | wc -l | tr -d '[:space:]')
if [ "$chunk_count" -eq 0 ]; then
    echo "No chunk files found in $CHUNKS_DIR"
    echo "Please run process_redbooks.sh first to generate chunks."
    exit 1
fi

# Check if Ollama is running
echo "Checking if Ollama is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama is not running or not accessible at http://localhost:11434"
    echo "Please start Ollama and try again."
    exit 1
fi

# Set the model to use
MODEL="granite3.2:8b-instruct-fp16"
# Alternate models: "llama3:8b-instruct" or any other model available in your Ollama

echo "Using model: $MODEL"
echo "Found $chunk_count chunk files to search."

# Run the Ollama RAG script
echo "Starting Ollama RAG interface..."
echo "This will use the $MODEL model for RAG."
echo ""

$PYTHON_CMD "$SCRIPTS_DIR/ollama_rag.py" \
    --ollama-url "http://localhost:11434" \
    --model "$MODEL" \
    --chunks-dir "$CHUNKS_DIR" \
    --cache-dir "$CACHE_DIR" \
    --top-k 5
