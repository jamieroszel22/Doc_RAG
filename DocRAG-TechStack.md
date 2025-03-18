# DocRAG Technical Stack: A Comprehensive Breakdown

This document provides a detailed breakdown of the entire technical stack behind DocRAG, a document processing and RAG (Retrieval-Augmented Generation) system.

## Core Technologies

### Programming & Runtime
- **Python 3.12**: Primary programming language
- **Bash/Zsh**: Shell scripting for process management
- **macOS**: Operating system (darwin 24.3.0)

### Web Framework & UI
- **Streamlit**: Primary web framework for the interactive UI
- **HTML/CSS**: Custom styling embedded in Streamlit app
- **Plotly Express**: Interactive data visualization for document statistics

### Document Processing
- **PyPDF2**: PDF parsing and text extraction
- **Custom chunking logic**: Text segmentation for RAG processing
- **Markdown generator**: Custom functionality to convert text to structured Markdown

## Data Management

### Storage & Formats
- **JSON**: Primary data format for document metadata and chunks
- **JSONL**: Format used for Ollama integration
- **TXT**: Raw text storage of extracted documents
- **Markdown**: Generated structured content with headers and formatting

### File Management
- **pathlib**: Python's Path library for file operations
- **shutil**: For file copying during migrations

## Data Processing Pipeline

### Document Workflow
1. **Upload**: PDF documents stored in `/pdfs`
2. **Processing**: Text extraction via PyPDF2
3. **Structuring**: Creation of individual document folders with metadata
4. **Chunking**: Text segmentation for RAG operations
5. **Collection**: Assembly of multiple documents into searchable collections

### Integrations
- **Open WebUI**: External UI for RAG functionality
  - Uses a JSON collection format for document import
- **Ollama**: Local AI processing for embedding and generation
  - Uses JSONL format for document input

## Dependencies & Libraries

### Core Dependencies
- **docling**: Document processing framework
- **PyPDF2**: PDF handling
- **pandas**: Data manipulation for UI tables
- **streamlit**: Web application framework
- **plotly**: Visualization library

### Advanced Features
- **transformers**: NLP model integration
- **torch/torchvision**: Machine learning framework
- **easyocr**: OCR capabilities (for image-based PDFs)
- **safetensors**: Tensor handling

## System Architecture

### Directory Structure
- `/pdfs`: Raw PDF storage
- `/processed_docs`: Processed document storage
  - `/docs`: Individual document folders and files
  - `/chunks`: Chunked text for RAG
  - `/ollama`: Ollama-compatible formats
  - `/openwebui`: Open WebUI collections
  - `/embeddings_cache`: Cached embeddings

### Component Structure
- **app.py**: Main Streamlit application with UI logic
- **super_simple.py**: Core document processing engine
- **run_streamlit.sh**: Process management script
- **migrate_to_docrag.py**: Data migration utility

## Development Workflow

### Application Flow
1. **Upload Interface**: Web UI for document upload
2. **Processing Engine**: Background processing with status reporting
3. **Collection Management**: Organization of documents into collections
4. **Search Interface**: Simple keyword and advanced RAG search options

### Deployment Strategy
- Local deployment model with shell script launchers
- Background process management for resource-intensive operations
- Migration tools for system upgrades

## Challenges & Solutions

### Observed Issues
- Session state management in Streamlit threading
- Shell script syntax errors
- Compatibility with newer Streamlit API (experimental_rerun deprecation)
- Process termination handling

### Implementation Solutions
- Global message queue for thread communication
- Improved error handling and status reporting
- Graceful process termination and cleanup
- Backwards compatibility with existing data structure

The system was designed with modularity in mind, allowing for the successful rebranding from "IBM Redbooks RAG System" to the more generic "DocRAG" without major architectural changes. The migration script ensures backward compatibility with existing data.
