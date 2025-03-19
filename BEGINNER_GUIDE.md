# DocRAG: Beginner's Guide

This guide will help you get started with DocRAG, a document processing system with Retrieval-Augmented Generation (RAG) capabilities.

## 1. Introduction to DocRAG

DocRAG is a user-friendly tool that helps you:
- Extract text from PDF documents
- Create structured representations (TXT, JSON, Markdown)
- Organize documents into searchable collections
- Use documents with AI systems through RAG

No specialized knowledge is required to get started!

## 2. Installation

### Prerequisites
- Python 3.12 or higher
- Basic familiarity with using the terminal/command prompt

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/jamieroszel22/Doc_RAG.git
   cd Doc_RAG
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify installation:
   ```bash
   python -c "import streamlit, pandas, plotly, PyPDF2; print('Installation successful!')"
   ```

### Windows-specific Instructions

If you're installing on Windows:

1. Clone and install dependencies as described above
2. Create a batch file for running the application:
   ```powershell
   # Create a batch file for running streamlit
   echo python -m streamlit run app.py > run_streamlit.bat
   ```
3. When creating directories, use Windows path format:
   ```powershell
   mkdir pdfs
   mkdir processed_docs\docs processed_docs\chunks processed_docs\ollama processed_docs\openwebui
   ```
4. Run the application using the batch file:
   ```powershell
   run_streamlit.bat
   ```

## 3. Setting Up Your Documents

1. Create a folder for your PDFs:
   - By default, DocRAG looks for PDFs in the `pdfs/` directory
   - You can place your PDF documents there manually or upload them through the interface

2. Directory structure:
   ```
   DocRAG/
   ├── pdfs/                  # Place your PDFs here
   └── processed_docs/        # DocRAG will store processed files here
   ```

## 4. Using the System

You have three ways to interact with your documents:

### A. Streamlit GUI (Easiest)
```bash
./run_streamlit.sh
```
This opens a web-based graphical interface that lets you:
- Upload and manage PDFs with simple drag and drop
- Process documents with a single click
- Search through your documents
- View visualizations of your collections
- Monitor processing status and logs

The Streamlit interface is the most user-friendly way to use the system.

### B. Simple Search (Fastest)
```bash
python -c "from super_simple import run_simple_query; run_simple_query()"
```
This allows you to:
- Perform quick keyword searches across all your processed documents
- See context around matches
- Identify which documents contain your search terms

### C. Integration With AI Tools

1. **Open WebUI**:
   - Process your documents in DocRAG
   - Open WebUI at http://localhost:3000
   - Go to Collections > Import Collection
   - Select the JSON file from `processed_docs/openwebui/knowledge_collection.json`

2. **Ollama**:
   - DocRAG creates Ollama-compatible files in `processed_docs/ollama/`
   - Use these files with Ollama for local AI-powered question answering

## 5. Common Tasks

### Processing Your First PDF

1. Add PDFs to the `pdfs/` directory
2. Start the Streamlit interface:
   ```bash
   ./run_streamlit.sh
   ```
3. Go to the "Upload & Process" tab
4. Click "Process PDFs"
5. Wait for processing to complete
6. Check the "Collections" tab to view your processed documents

### Searching Your Documents

1. From the Streamlit interface:
   - Go to the "Search" tab
   - Enter your search query
   - Click "Search"
   - Browse the results

2. From the command line:
   ```bash
   python -c "from super_simple import run_simple_query; run_simple_query('your search term')"
   ```

### Viewing Document Collections

1. Streamlit Interface:
   - Go to the "Collections" tab
   - View individual document details
   - Browse documents by title
   - View statistics about your collection

2. File System:
   - Individual documents: `processed_docs/docs/[document_name]/`
   - Markdown files: `processed_docs/docs/[document_name]/[document_name].md`
   - JSON metadata: `processed_docs/docs/[document_name]/[document_name].json`

## 6. Troubleshooting

### Common Issues

1. **Streamlit app won't start**:
   - Make sure Python 3.12+ is installed
   - Check that all dependencies are installed
   - Verify the script is executable: `chmod +x run_streamlit.sh` (macOS/Linux only)
   - On Windows, try running `python -m streamlit run app.py` directly

2. **PDFs not processing correctly**:
   - Ensure PDFs are text-based (not scanned images)
   - Check file permissions
   - Look at the Processing Status & Log for error messages

3. **Search returning no results**:
   - Make sure documents have been processed first
   - Check spelling of search terms
   - Try more general terms

4. **Windows-specific issues**:
   - Windows does not support shell scripts (.sh files) natively
   - Use the provided batch files (.bat) or run Python commands directly
   - Use Windows path separators (backslashes) when specifying directories
   - If using PowerShell, some commands may differ from Command Prompt
   - If you encounter `UnicodeDecodeError` messages, make sure you're using the latest version which includes fixes for UTF-8 encoding issues

## 7. Getting Help

- Check the [README.md](README.md) file for detailed documentation
- Review the [DocRAG-TechStack.md](DocRAG-TechStack.md) for technical details
- Submit issues on GitHub if you encounter problems

Happy document processing with DocRAG!
