#!/bin/bash
# Run simple keyword-based query on processed Redbooks

echo "Starting simple query system for Redbooks..."

# Base directory
BASE_DIR="/Users/jamieroszel/Desktop/Docling RAG"
SCRIPTS_DIR="$BASE_DIR/scripts"
CHUNKS_DIR="$BASE_DIR/processed_redbooks/chunks"

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

echo "Found $chunk_count chunk files to search."

# Run the simple query script
echo "Starting simple query interface..."
$PYTHON_CMD "$SCRIPTS_DIR/simple_query.py" --chunks-dir "$CHUNKS_DIR"
