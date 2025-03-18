#!/bin/bash
# Prepare data for Open WebUI collection

echo "Preparing Redbooks data for Open WebUI..."

# Base directory - use relative paths for portability
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$SCRIPT_DIR"
SCRIPTS_DIR="$BASE_DIR/scripts"
CHUNKS_DIR="$BASE_DIR/processed_redbooks/chunks"
OPENWEBUI_DIR="$BASE_DIR/processed_redbooks/openwebui"
OUTPUT_FILE="$OPENWEBUI_DIR/ibm_knowledge_collection.json"

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

# Create OpenWebUI directory if it doesn't exist
mkdir -p "$OPENWEBUI_DIR"

# Set the collection name
COLLECTION="IBM Z Knowledge Base"

echo "Found $chunk_count chunk files to convert."
echo "Collection name: $COLLECTION"

# Run the Open WebUI preparation script
echo "Preparing collection..."
$PYTHON_CMD "$SCRIPTS_DIR/prepare_for_openwebui.py" \
    --chunks-dir "$CHUNKS_DIR" \
    --output-file "$OUTPUT_FILE" \
    --collection-name "$COLLECTION"

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "Open WebUI collection prepared successfully!"
    echo "Collection file: $OUTPUT_FILE"
    echo ""
    echo "To import this collection into Open WebUI:"
    echo "1. Open the Open WebUI interface"
    echo "2. Go to Collections"
    echo "3. Click \"Import Collection\""
    echo "4. Select the file: $OUTPUT_FILE"
    echo "5. Verify the import was successful"
else
    echo "Preparation encountered errors. Please check the logs."
    exit 1
fi
