# IBM Redbooks RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system for IBM Redbooks documentation, supporting multiple query interfaces including simple search, Ollama RAG, and Open WebUI collections.

## Directory Structure

```
/
├── pdfs/                      # Place your IBM Redbooks PDFs here
├── processed_redbooks/        # All processed outputs
│   ├── docs/                 # Full text extracted from PDFs
│   ├── chunks/               # JSON files containing text chunks
│   ├── ollama/              # JSONL files for Ollama RAG
│   ├── openwebui/           # Collection files for Open WebUI
│   └── embeddings_cache/    # Cached embeddings for faster processing
├── super_simple.py           # Main processing script
├── menu.sh                   # Menu interface script
├── run_simple_query.sh       # Simple keyword search script
├── run_rag_interactive.sh    # Ollama RAG interface script
└── requirements.txt          # Python dependencies
```

## Processing Flow

### 1. Initial Setup

Before using the system, you'll need to create two important directories that aren't included in the repository:

1. Create a `pdfs` directory in the project root:
   ```bash
   mkdir pdfs
   ```
   This is where you'll place your IBM Redbooks PDFs for processing.

2. The system will automatically create a `processed_redbooks` directory when needed:
   ```
   processed_redbooks/
   ├── docs/          # Extracted text
   ├── chunks/        # Processed chunks
   ├── ollama/        # Ollama RAG files
   └── openwebui/     # Open WebUI collection
   ```

These directories are excluded from version control as they contain user-specific content.

a. **Environment Setup**:
   ```bash
   # Make scripts executable
   ./make_fix_executable.sh

   # Install Python dependencies (automatic)
   # The script will install PyPDF2 if needed
   ```

b. **PDF Preparation**:
   - Place your IBM Redbooks PDFs in the `pdfs/` directory
   - The system will process any PDF files found in this directory

### 2. Processing PDFs

The main processing script (`super_simple.py`) handles:
- PDF text extraction
- Text chunking
- Multiple output format generation
- Open WebUI collection creation

Run the processor:
```bash
python3 super_simple.py [options]

Options:
  --force           Force reprocess all PDFs
  --skip-openwebui  Skip Open WebUI collection preparation
```

### 3. Output Formats

The system generates multiple output formats for different use cases:

a. **Full Text** (`docs/`):
   - Complete extracted text from each PDF
   - Useful for archival and full-text search

b. **Chunks** (`chunks/`):
   - JSON files containing text chunks
   - 1000 characters per chunk with 100 character overlap
   - Includes metadata and source information

c. **Ollama Files** (`ollama/`):
   - JSONL format for Ollama RAG
   - Optimized for Ollama's retrieval system

d. **Open WebUI Collection** (`openwebui/`):
   - Single collection file combining all processed documents
   - Ready for import into Open WebUI
   - Includes document metadata and chunk information

### 4. Using the Processed Content

#### Simple Keyword Search
```bash
./run_simple_query.sh
```
- Fast text-based search
- Highlights matching content
- Shows source document information

#### Ollama RAG Interface
```bash
./run_rag_interactive.sh
```
- AI-powered question answering
- Uses Ollama for embeddings and generation
- Provides context-aware responses

#### Open WebUI Integration
1. Process your PDFs:
   ```bash
   python3 super_simple.py
   ```
2. Find the collection file:
   ```
   processed_redbooks/openwebui/ibm_knowledge_collection.json
   ```
3. Import into Open WebUI:
   - Open the Open WebUI interface
   - Go to Collections
   - Click "Import Collection"
   - Select the collection file
   - Verify the import

#### Automated Collection Updates
To keep your Open WebUI collection current as you add new IBM Z content:

1. **Adding New Content**:
   - Place new IBM Z PDFs in the `pdfs/` directory
   - Run the update script:
     ```bash
     ./update_collection.sh
     ```
   - The script automatically:
     - Processes only new PDFs (skips already processed ones)
     - Generates updated chunks
     - Creates a new Open WebUI collection file

2. **Updating Open WebUI**:
   - After running the script, go to http://localhost:3000/
   - Navigate to Collections
   - Click "Import Collection"
   - Select the updated collection file at `processed_redbooks/openwebui/ibm_knowledge_collection.json`

3. **Best Practices**:
   - Run the update script whenever you add new PDFs
   - The script is incremental, so it only processes new files
   - If you need to reprocess all files, use `python3 super_simple.py --force`
   - The collection file is automatically updated with all processed content

4. **Monitoring**:
   - The script provides clear feedback about:
     - Number of PDFs found
     - Processing status
     - Success/failure of operations
     - Next steps for updating Open WebUI

### 5. Processing Details

The system provides detailed information during processing:

- File statistics:
  - Original PDF size
  - Number of pages
  - Modification dates

- Processing metrics:
  - Number of chunks generated
  - Text extraction size
  - Processing status

- Collection statistics:
  - Total documents processed
  - Chunk counts per document
  - Collection file sizes

### 6. Incremental Processing

The system is designed to be incremental:
- Only processes new PDFs by default
- Tracks processed files to avoid duplication
- Updates collections automatically
- Use `--force` to reprocess all files

## Advanced Usage

### Force Reprocessing
To reprocess all PDFs, even if already processed:
```bash
python3 super_simple.py --force
```

### Skip Open WebUI Collection
To process PDFs without updating the Open WebUI collection:
```bash
python3 super_simple.py --skip-openwebui
```

### Menu Interface
For a guided interface to all functions:
```bash
./menu.sh
```

### Streamlit GUI
For a modern web-based GUI interface:
```bash
./run_streamlit.sh
```

The Streamlit interface provides:
- PDF upload and management
- Visual processing status and logs
- Simple search interface
- Collection management
- System status dashboard

![Streamlit GUI](streamlit_screenshot.png)

## Troubleshooting

1. **PDF Processing Issues**:
   - Check PDF permissions
   - Ensure PDF is text-based (not scanned)
   - Verify PDF is not corrupted

2. **Ollama Integration**:
   - Ensure Ollama is running
   - Check model availability
   - Verify network connectivity

3. **Open WebUI Import**:
   - Validate collection file format
   - Check file permissions
   - Ensure collection name uniqueness

## Requirements

- Python 3.x
- PyPDF2 (auto-installed if needed)
- Ollama (for RAG functionality)
- Open WebUI (for collection import)

## Credits

This system uses:
- PyPDF2 for text extraction
- Ollama for embeddings and AI text generation
- Open WebUI for collection management

For more information on using Ollama: https://ollama.ai/
