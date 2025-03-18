#!/usr/bin/env python3
"""
IBM Redbooks RAG System - Streamlit App
A GUI interface for processing IBM Redbooks PDFs and managing RAG collections
"""

import os
import json
import time
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import subprocess
import tempfile
import shutil
import sys
from datetime import datetime
import threading
import queue

# Initialize paths
BASE_DIR = Path('/Users/jamieroszel/Desktop/Docling RAG')
PDFS_DIR = BASE_DIR / 'pdfs'
PROCESSED_DIR = BASE_DIR / 'processed_redbooks'
CHUNKS_DIR = PROCESSED_DIR / 'chunks'
OPENWEBUI_DIR = PROCESSED_DIR / 'openwebui'
SCRIPTS_DIR = BASE_DIR / 'scripts'

# Make sure directories exist
PDFS_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Set page config at the very beginning
st.set_page_config(
    page_title="IBM Redbooks RAG System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global message queue (outside of session state)
# This is a workaround for thread communication
global_message_queue = queue.Queue()

# Initialize session state variables
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None
if 'processing_log' not in st.session_state:
    st.session_state.processing_log = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'last_check_time' not in st.session_state:
    st.session_state.last_check_time = time.time()
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Upload & Process"

# Custom CSS for better appearance
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .block-container {
        max-width: 1200px;
        margin: 0 auto;
        padding-top: 2rem;
    }
    .file-uploader {
        border: 2px dashed #0e77ca;
        border-radius: 8px;
        padding: 30px;
        text-align: center;
        margin-bottom: 20px;
    }
    .status-success {
        color: #00cc66;
        font-weight: bold;
    }
    .status-processing {
        color: #ff9900;
        font-weight: bold;
    }
    .status-error {
        color: #ff3366;
        font-weight: bold;
    }
    .log-container {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        max-height: 300px;
        overflow-y: auto;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f5f7f9;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-radius: 4px 4px 0 0;
        border-right: 1px solid #f0f2f6;
        border-left: 1px solid #f0f2f6;
        border-top: 2px solid #4da6ff;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to run super_simple.py in a thread
def process_pdfs_in_thread(force=False, skip_openwebui=False):
    """Run the PDF processing script in a background thread"""
    # Update the status first
    st.session_state.processing_status = "PROCESSING"
    st.session_state.processing_log = []

    def run_process():
        try:
            cmd = [sys.executable, str(BASE_DIR / 'super_simple.py')]
            if force:
                cmd.append('--force')
            if skip_openwebui:
                cmd.append('--skip-openwebui')

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Capture output line by line
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    global_message_queue.put(("LOG", line.strip()))

            # Check for any errors
            for line in iter(process.stderr.readline, ''):
                if line.strip():
                    global_message_queue.put(("LOG", f"ERROR: {line.strip()}"))

            process.stdout.close()
            process.stderr.close()
            return_code = process.wait()

            if return_code == 0:
                global_message_queue.put(("LOG", "✅ Processing completed successfully!"))
                global_message_queue.put(("STATUS", "COMPLETE"))
            else:
                global_message_queue.put(("LOG", f"❌ Processing failed with code {return_code}"))
                global_message_queue.put(("STATUS", "ERROR"))

        except Exception as e:
            global_message_queue.put(("LOG", f"❌ Error: {str(e)}"))
            global_message_queue.put(("STATUS", "ERROR"))

    # Start processing thread
    thread = threading.Thread(target=run_process)
    thread.daemon = True
    thread.start()

# Helper function to check queue and update session state
def check_message_queue():
    """Check the global message queue and update session state"""
    while not global_message_queue.empty():
        try:
            message_type, message = global_message_queue.get_nowait()
            if message_type == "LOG":
                st.session_state.processing_log.append(message)
            elif message_type == "STATUS":
                st.session_state.processing_status = message
        except queue.Empty:
            break

# Helper function to run simple search
def run_simple_search(query):
    """Run a simple search query and return results"""
    try:
        # Get all chunk files
        chunk_files = list(CHUNKS_DIR.glob("*_chunks.json"))
        if not chunk_files:
            return "No chunk files found. Please process PDFs first."

        # Load all chunks
        all_chunks = []
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                    all_chunks.extend(chunks)
            except Exception as e:
                return f"Error loading {chunk_file.name}: {str(e)}"

        # Simple search function (case insensitive)
        results = []
        for chunk in all_chunks:
            if query.lower() in chunk["text"].lower():
                results.append({
                    "text": chunk["text"],
                    "source": chunk["metadata"]["source"],
                    "score": chunk["text"].lower().count(query.lower())
                })

        # Sort by relevance score
        results.sort(key=lambda x: x["score"], reverse=True)

        # Limit to top 10 results
        return results[:10] if results else "No results found."

    except Exception as e:
        return f"Search error: {str(e)}"

# Upload and Process page
def render_upload_page():
    st.header("Upload & Process PDFs")

    # Upload section
    st.subheader("1. Upload IBM Redbooks PDFs")

    uploaded_files = st.file_uploader(
        "Upload IBM Redbooks PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select one or more IBM Redbooks PDF files to upload"
    )

    if uploaded_files:
        save_button = st.button("Save PDFs")
        if save_button:
            success_count = 0
            for uploaded_file in uploaded_files:
                try:
                    # Save the uploaded file to the pdfs directory
                    pdf_path = PDFS_DIR / uploaded_file.name
                    with open(pdf_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    success_count += 1
                    st.success(f"✅ Saved: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"❌ Error saving {uploaded_file.name}: {str(e)}")

            if success_count > 0:
                st.success(f"Successfully saved {success_count} PDF files")

    st.divider()

    # Current PDFs section
    st.subheader("2. Current PDFs")

    pdfs = list(PDFS_DIR.glob("*.pdf"))
    if pdfs:
        pdf_data = []
        for pdf in pdfs:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(pdf.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            processed = (PROCESSED_DIR / "docs" / f"{pdf.stem}.txt").exists()
            pdf_data.append({
                "Filename": pdf.name,
                "Size (MB)": round(size_mb, 2),
                "Modified": mod_time,
                "Processed": "✅" if processed else "❌"
            })

        df = pd.DataFrame(pdf_data)
        st.dataframe(df, use_container_width=True)

        # Processing options
        st.subheader("3. Process PDFs")
        col1, col2 = st.columns(2)
        with col1:
            force_reprocess = st.checkbox("Force reprocess all",
                                         help="Process all PDFs even if already processed")
        with col2:
            skip_openwebui = st.checkbox("Skip Open WebUI collection",
                                        help="Don't prepare Open WebUI collection")

        # Check if processing is active
        is_processing = st.session_state.processing_status == "PROCESSING"

        process_button = st.button("Process PDFs", type="primary", disabled=is_processing)
        if process_button:
            process_pdfs_in_thread(force=force_reprocess, skip_openwebui=skip_openwebui)
            st.info("⏳ Processing started. View status below.")
            # Change to the status tab within this page (no redirect)
            st.session_state.current_page = "Status"
            st.experimental_rerun()
    else:
        st.info("No PDFs found. Please upload PDFs first.")

# Search page
def render_search_page():
    st.header("Search IBM Redbooks")

    # Check if chunks exist
    chunk_files = list(CHUNKS_DIR.glob("*_chunks.json"))
    if not chunk_files:
        st.warning("No processed content found. Please process PDFs first.")
        return

    # Simple search interface
    st.subheader("Simple Keyword Search")
    query = st.text_input("Enter search query:")
    search_button = st.button("Search")

    if search_button and query:
        with st.spinner("Searching..."):
            results = run_simple_search(query)
            st.session_state.search_results = results

    # Display search results
    if st.session_state.search_results:
        st.subheader("Search Results")

        if isinstance(st.session_state.search_results, str):
            st.info(st.session_state.search_results)
        else:
            for i, result in enumerate(st.session_state.search_results):
                with st.expander(f"Result {i+1} (Source: {result['source']})"):
                    st.markdown(f"**Score:** {result['score']}")
                    st.text(result['text'])

    # Links to other search options
    st.divider()
    st.subheader("Advanced Search Options")

    st.markdown("""
    - **Open WebUI**: Powerful RAG interface with collection management
        - Open [http://localhost:3000/](http://localhost:3000/) to use Open WebUI
        - Import collections from `processed_redbooks/openwebui/`

    - **Ollama RAG**: Local AI-powered question answering
        - Run `./run_rag_interactive.sh` in terminal
        - Uses Ollama for embeddings and generation
    """)

# Collections page
def render_collections_page():
    st.header("Collection Management")

    # Open WebUI Collections
    st.subheader("Open WebUI Collections")

    openwebui_file = OPENWEBUI_DIR / "ibm_knowledge_collection.json"
    if openwebui_file.exists():
        try:
            with open(openwebui_file, "r", encoding="utf-8") as f:
                collection = json.load(f)

            # Collection stats
            st.success(f"✅ Collection: {collection['name']}")
            st.markdown(f"📚 **Documents**: {len(collection['documents'])}")

            # Document details
            doc_data = []
            for doc in collection['documents']:
                doc_data.append({
                    "Title": doc['title'],
                    "Chunks": len(doc['content_chunks'])
                })

            df = pd.DataFrame(doc_data)
            st.dataframe(df, use_container_width=True)

            # Chart of chunks by document
            fig = px.bar(df, x='Title', y='Chunks',
                        title='Number of Chunks by Document',
                        labels={'Title': 'Document', 'Chunks': 'Number of Chunks'})
            st.plotly_chart(fig, use_container_width=True)

            # Import instructions
            st.subheader("Import Instructions")
            st.markdown(f"""
            1. Open [Open WebUI](http://localhost:3000/)
            2. Go to Collections
            3. Click "Import Collection"
            4. Select the file: `{openwebui_file}`
            5. Verify the import was successful
            """)

            # Update collection button
            st.divider()
            is_processing = st.session_state.processing_status == "PROCESSING"
            update_button = st.button("Update Collection", type="primary", disabled=is_processing)
            if update_button:
                process_pdfs_in_thread(force=False, skip_openwebui=False)
                st.info("⏳ Collection update started. Check the Status page for progress.")
                st.session_state.current_page = "Status"
                st.experimental_rerun()

        except Exception as e:
            st.error(f"Error loading collection: {str(e)}")
    else:
        st.warning("No Open WebUI collection found. Please process PDFs first.")

# Status page
def render_status_page():
    st.header("Processing Status")

    # Status indicator
    if st.session_state.processing_status == "PROCESSING":
        st.markdown("<p class='status-processing'>⏳ Processing in progress...</p>", unsafe_allow_html=True)
        st.progress(0.5)  # Indeterminate progress
    elif st.session_state.processing_status == "COMPLETE":
        st.markdown("<p class='status-success'>✅ Processing complete</p>", unsafe_allow_html=True)
    elif st.session_state.processing_status == "ERROR":
        st.markdown("<p class='status-error'>❌ Processing failed</p>", unsafe_allow_html=True)
    else:
        st.info("No active processing")

    # Processing log
    st.subheader("Processing Log")
    if st.session_state.processing_log:
        st.markdown("<div class='log-container'>", unsafe_allow_html=True)
        for line in st.session_state.processing_log:
            st.text(line)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.text("No log entries")

    # System information
    st.divider()
    st.subheader("System Information")

    # PDF counts
    pdf_count = len(list(PDFS_DIR.glob("*.pdf")))
    processed_count = len(list((PROCESSED_DIR / "docs").glob("*.txt"))) if (PROCESSED_DIR / "docs").exists() else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("PDF Files", pdf_count)
    col2.metric("Processed Files", processed_count)
    col3.metric("Processing Rate", f"{round(processed_count/max(1, pdf_count)*100)}%")

    # Directory status
    st.subheader("Directory Status")
    dirs = {
        "PDFs Directory": PDFS_DIR,
        "Processed Directory": PROCESSED_DIR,
        "Chunks Directory": CHUNKS_DIR,
        "Open WebUI Directory": OPENWEBUI_DIR
    }

    dir_data = []
    for name, path in dirs.items():
        exists = path.exists()
        size = sum(f.stat().st_size for f in path.glob('**/*') if f.is_file()) / (1024*1024) if exists else 0
        dir_data.append({
            "Directory": name,
            "Status": "✅ Exists" if exists else "❌ Missing",
            "Size (MB)": round(size, 2)
        })

    st.dataframe(pd.DataFrame(dir_data), use_container_width=True)

    # Actions
    st.divider()
    refresh_button = st.button("Refresh Status")
    if refresh_button:
        st.experimental_rerun()

# Main app layout
def main():
    # Check the global message queue for updates
    check_message_queue()

    st.title("IBM Redbooks RAG System")
    st.write("A comprehensive Retrieval-Augmented Generation system for IBM Redbooks documentation")

    # If processing is active, periodically check for updates
    if st.session_state.processing_status == "PROCESSING":
        current_time = time.time()
        if current_time - st.session_state.last_check_time > 1.0:
            st.session_state.last_check_time = current_time
            st.experimental_rerun()

    # Create tabs for each section
    tab1, tab2, tab3, tab4 = st.tabs(["Upload & Process", "Search", "Collections", "Status"])

    # Display content in selected tab
    with tab1:
        if st.session_state.current_page == "Upload & Process" or tab1.active:
            render_upload_page()

    with tab2:
        if st.session_state.current_page == "Search" or tab2.active:
            render_search_page()

    with tab3:
        if st.session_state.current_page == "Collections" or tab3.active:
            render_collections_page()

    with tab4:
        if st.session_state.current_page == "Status" or tab4.active:
            render_status_page()

# Run the app
if __name__ == "__main__":
    main()
