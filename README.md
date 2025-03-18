# DocRAG

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.27+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DocRAG is a comprehensive document processing system with RAG (Retrieval-Augmented Generation) capabilities. It allows you to upload PDF documents, extract text, create structured representations, and use them with LLM systems via a user-friendly interface.

![DocRAG Screenshot](docs/screenshot.png)

## Features

- **PDF Processing**: Upload and process PDF documents
- **Individual Document Views**: Each document gets its own folder with TXT, JSON, and Markdown formats
- **Chunking**: Automatic text chunking for RAG applications
- **Collections**: Create and manage document collections
- **Integration**: Ready for use with Open WebUI and Ollama
- **Search**: Simple keyword search across all documents

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Streamlit 1.27+
- PyPDF2
- Pandas, Plotly

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/docrag.git
   cd docrag
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   ./run_streamlit.sh
   ```

4. Open your browser at [http://localhost:8501](http://localhost:8501)

## Usage

### Uploading Documents

1. Navigate to the "Upload & Process" tab
2. Upload PDF files using the file uploader
3. Click "Save PDFs" to save the files
4. Click "Process PDFs" to extract text and create chunks

### Viewing Documents

1. Go to the "Collections" tab
2. Browse documents in the "Individual Document Collections" section
3. View or download the Markdown representation of any document

### Searching

1. Navigate to the "Search" tab
2. Enter a search query and click "Search"
3. View the matching results from across your documents

### Integration with Open WebUI

1. Process your documents in DocRAG
2. Open WebUI at http://localhost:3000
3. Go to Collections > Import Collection
4. Select the JSON file from `processed_docs/openwebui/knowledge_collection.json`

## Architecture

See the [DocRAG-TechStack.md](DocRAG-TechStack.md) file for a detailed breakdown of the system architecture and technical stack.

## Directory Structure

```
DocRAG/
├── app.py                 # Main Streamlit application
├── super_simple.py        # Core document processing engine
├── run_streamlit.sh       # Shell script to run the app
├── migrate_to_docrag.py   # Migration utility
├── requirements.txt       # Python dependencies
├── pdfs/                  # Store uploaded PDFs here
└── processed_docs/        # Processed documents
    ├── docs/              # Text, JSON and Markdown files
    ├── chunks/            # Chunked text for RAG
    ├── ollama/            # Ollama-compatible formats
    └── openwebui/         # Open WebUI collections
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Originally developed as "IBM Redbooks RAG System"
- Uses [Streamlit](https://streamlit.io/) for the web interface
- PDF processing with [PyPDF2](https://pypdf2.readthedocs.io/)
