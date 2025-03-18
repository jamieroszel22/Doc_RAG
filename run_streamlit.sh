#!/bin/bash

# DocRAG - Streamlit App Launcher
# This script starts the Streamlit app for DocRAG

echo "Starting DocRAG Streamlit App..."

# Stop any existing Streamlit processes
echo "Stopping any existing Streamlit processes..."
pkill -f "streamlit run app.py" || true

# Wait a moment for processes to terminate
sleep 1

# Start the Streamlit app
echo "Starting Streamlit app at http://localhost:8501"

# Set the Streamlit server port
export STREAMLIT_SERVER_PORT=8501

# Check if Python 3 is available
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo "Error: Python is not installed or not in PATH"
        exit 1
    fi
fi

# Run the Streamlit app
$PYTHON_CMD -m streamlit run app.py
