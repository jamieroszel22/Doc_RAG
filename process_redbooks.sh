#!/bin/bash
# Process Redbooks PDFs with Docling

echo "Processing Redbooks PDFs with Docling..."

# Base directory
BASE_DIR="/Users/jamieroszel/Desktop/Docling RAG"
SCRIPTS_DIR="$BASE_DIR/scripts"
PDFS_DIR="$BASE_DIR/pdfs"
PROCESSED_DIR="$BASE_DIR/processed_redbooks"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

# Check if there are PDFs to process
pdf_count=$(find "$PDFS_DIR" -name "*.pdf" | wc -l | tr -d '[:space:]')
if [ "$pdf_count" -eq 0 ]; then
    echo "No PDF files found in $PDFS_DIR"
    echo "Please add PDF files to the directory and try again."
    exit 1
fi

echo "Found $pdf_count PDF files to process."

# Run the processor script
echo "Starting Docling processing..."
$PYTHON_CMD "$SCRIPTS_DIR/redbook_processor.py" \
    --input-dir "$PDFS_DIR" \
    --output-dir "$PROCESSED_DIR" \
    --chunk-size 1000 \
    --chunk-overlap 100

# Check exit status
if [ $? -eq 0 ]; then
    echo "Processing completed successfully!"
    echo ""
    echo "Processed files are available in:"
    echo "- Documents: $PROCESSED_DIR/docs"
    echo "- Chunks:    $PROCESSED_DIR/chunks"
    echo "- Ollama:    $PROCESSED_DIR/ollama"
    echo ""
    echo "Next steps:"
    echo "1. Run simple query:  bash $BASE_DIR/run_simple_query.sh"
    echo "2. Run Ollama RAG:    bash $BASE_DIR/run_rag_interactive.sh"
    echo "3. Prepare for Open WebUI: bash $BASE_DIR/prepare_for_openwebui.sh"
else
    echo "Processing encountered errors. Please check the logs."
    exit 1
fi
