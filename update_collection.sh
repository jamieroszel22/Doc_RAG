#!/bin/bash

# Script to update Open WebUI collection with new IBM Z content
# This script should be run whenever new PDFs are added

echo "Checking for new IBM Z content..."

# Base directory
BASE_DIR="/Users/jamieroszel/Desktop/Docling RAG"
PDFS_DIR="$BASE_DIR/pdfs"
PROCESSED_DIR="$BASE_DIR/processed_redbooks"
CHUNKS_DIR="$PROCESSED_DIR/chunks"
OPENWEBUI_DIR="$PROCESSED_DIR/openwebui"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

# Check if there are any PDF files
pdf_count=$(find "$PDFS_DIR" -name "*.pdf" | wc -l | tr -d '[:space:]')
if [ "$pdf_count" -eq 0 ]; then
    echo "No PDF files found in $PDFS_DIR"
    echo "Please add your IBM Z PDFs to this directory."
    exit 1
fi

# Process new PDFs
echo "Processing new PDFs..."
$PYTHON_CMD "$BASE_DIR/super_simple.py"

# Check if processing was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Processing completed successfully!"
    echo ""
    echo "To update your Open WebUI collection:"
    echo "1. Open http://localhost:3000/"
    echo "2. Go to Collections"
    echo "3. Click \"Import Collection\""
    echo "4. Select the file: $OPENWEBUI_DIR/ibm_knowledge_collection.json"
    echo "5. Verify the import was successful"
else
    echo "Processing encountered errors. Please check the logs."
    exit 1
fi
