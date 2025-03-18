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
import threading
import queue
from datetime import datetime

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

# Create a queue for thread-safe communication
if 'process_queue' not in st.session_state:
    st.session_state.process_queue = queue.Queue()

# Initialize session state variables - always initialize at the beginning
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None
if 'processing_log' not in st.session_state:
    st.session_state.processing_log = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'thread_running' not in st.session_state:
    st.session_state.thread_running = False

# Custom CSS for better appearance
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
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
</style>
""", unsafe_allow_html=True)

# Function to add log messages from the thread to the queue
def add_log_message(message):
    if st.session_state.process_queue is not None:
        st.session_state.process_queue.put(message)

# Helper function to run super_simple.py in a thread
def process_pdfs(force=False, skip_openwebui=False):
    """Run the PDF processing script in a background thread"""
    # Update the status first
    st.session_state.processing_status = "PROCESSING"
    st.session_state.processing_log = []
    st.session_state.thread_running = True

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
                    add_log_message(line.strip())

            # Check for any errors
            for line in iter(process.stderr.readline, ''):
                if line.strip():
                    add_log_message(f"ERROR: {line.strip()}")

            process.stdout.close()
            process.stderr.close()
            return_code = process.wait()

            if return_code == 0:
                add_log_message("✅ Processing completed successfully!")
                add_log_message("STATUS:COMPLETE")
            else:
                add_log_message(f"❌ Processing failed with code {return_code}")
                add_log_message("STATUS:ERROR")

        except Exception as e:
            add_log_message(f"❌ Error: {str(e)}")
            add_log_message("STATUS:ERROR")

        # Mark thread as complete
        add_log_message("THREAD:COMPLETE")

    # Start processing thread
    thread = threading.Thread(target=run_process)
    thread.daemon = True
    thread.start()

# Helper function to check queue and update session state
def check_process_queue():
    # Check for any messages in the queue
    if hasattr(st.session_state, 'process_queue'):
        q = st.session_state.process_queue
        while not q.empty():
            message = q.get()

            # Check for special status messages
            if message.startswith("STATUS:"):
                st.session_state.processing_status = message[7:]
            elif message.startswith("THREAD:"):
                if message == "THREAD:COMPLETE":
                    st.session_state.thread_running = False
            else:
                # Regular log message
                st.session_state.processing_log.append(message)

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

# Main app layout
def main():
    # Check process queue for updates
    check_process_queue()

    st.title("IBM Redbooks RAG System")
    st.write("A comprehensive Retrieval-Augmented Generation system for IBM Redbooks documentation")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Upload & Process", "Search", "Collections", "Status"])

    # Page content
    if page == "Upload & Process":
        render_upload_page()
    elif page == "Search":
        render_search_page()
    elif page == "Collections":
        render_collections_page()
    elif page == "Status":
        render_status_page()

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

        process_button = st.button("Process PDFs", type="primary", disabled=st.session_state.thread_running)
        if process_button:
            process_pdfs(force=force_reprocess, skip_openwebui=skip_openwebui)
            st.info("⏳ Processing started. Check the Status page for progress.")
            # Add a delay to ensure the thread starts
            time.sleep(1)
            # Redirect to status page
            st.switch_page("app.py/Status")
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
            update_button = st.button("Update Collection", type="primary", disabled=st.session_state.thread_running)
            if update_button:
                process_pdfs(force=False, skip_openwebui=False)
                st.info("⏳ Collection update started. Check the Status page for progress.")
                # Add a delay to ensure the thread starts
                time.sleep(1)
                # Navigate to the status page
                st.switch_page("app.py/Status")

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

    # Auto-refresh if processing is happening
    if st.session_state.thread_running:
        st.empty()
        time.sleep(1)
        st.rerun()

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
        st.rerun()

# Run the app
if __name__ == "__main__":
    main()
