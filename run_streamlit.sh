#!/bin/bash

# Run the Streamlit app for IBM Redbooks RAG

echo "Starting IBM Redbooks RAG Streamlit App..."

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

# Check if Streamlit is installed
$PYTHON_CMD -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Streamlit not found. Installing required packages..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

# Run the app
streamlit run app.py
