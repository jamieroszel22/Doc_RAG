#!/usr/bin/env python3
"""
DocRAG - A GUI for processing PDF documents using RAG
A GUI interface for processing PDF documents and managing RAG collections
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

# Initialize paths - using relative paths for portability
current_dir = Path(__file__).parent.absolute()
BASE_DIR = current_dir
PDFS_DIR = BASE_DIR / 'pdfs'
PROCESSED_DIR = BASE_DIR / 'processed_docs'  # Changed from processed_redbooks
CHUNKS_DIR = PROCESSED_DIR / 'chunks'
OPENWEBUI_DIR = PROCESSED_DIR / 'openwebui'
SCRIPTS_DIR = BASE_DIR / 'scripts'

# Make sure directories exist
PDFS_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Set page config at the very beginning
st.set_page_config(
    page_title="DocRAG",
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
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 0
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'process_queue' not in st.session_state:
    st.session_state.process_queue = None

# Reset processing status if it's stuck (processing status is PROCESSING but is_processing is False)
if st.session_state.processing_status == "PROCESSING" and not st.session_state.is_processing:
    st.session_state.processing_status = None
    st.session_state.processing_log.append("⚠️ Detected stale processing status - automatically reset")

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
    st.session_state.is_processing = True

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
        finally:
            # Make sure to set processing to False when done
            global_message_queue.put(("PROCESSING", False))

    # Start processing thread
    thread = threading.Thread(target=run_process)
    thread.daemon = True
    thread.start()

# Helper function to check queue and update session state
def check_message_queue():
    """Check the global message queue and update session state"""
    try:
        # Process up to 100 messages per check to avoid infinite loops
        max_messages = 100
        msg_count = 0

        while not global_message_queue.empty() and msg_count < max_messages:
            try:
                message_type, message = global_message_queue.get_nowait()
                msg_count += 1

                if message_type == "LOG":
                    # Append to logs
                    st.session_state.processing_log.append(message)
                elif message_type == "STATUS":
                    # Update status
                    st.session_state.processing_status = message
                    # If status is COMPLETE or ERROR, also update is_processing
                    if message in ["COMPLETE", "ERROR"]:
                        st.session_state.is_processing = False
                elif message_type == "PROCESSING":
                    # Update processing flag
                    st.session_state.is_processing = message
                else:
                    # Log unrecognized message types for debugging
                    st.session_state.processing_log.append(f"WARNING: Unknown message type: {message_type}")
            except queue.Empty:
                break
            except Exception as e:
                st.session_state.processing_log.append(f"ERROR: Failed to process message: {str(e)}")

        # Update the check time
        st.session_state.last_check_time = time.time()

    except Exception as e:
        # Add critical error to session state
        if 'processing_log' in st.session_state:
            st.session_state.processing_log.append(f"CRITICAL ERROR in message queue: {str(e)}")
        # Reset processing state on critical error
        st.session_state.is_processing = False
        st.session_state.processing_status = "ERROR"

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

    # Display a simple status message if processing
    if st.session_state.is_processing:
        st.info("⏳ Processing in progress... Use the 'Refresh PDF List' button to check status updates.")

    # Upload section
    st.subheader("1. Upload PDF Documents")

    uploaded_files = st.file_uploader(
        "Upload PDF Documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select one or more PDF files to upload"
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
                # Force refresh after saving files
                st.rerun()

    st.divider()

    # Current PDFs section
    st.subheader("2. Current PDFs")

    # Make the refresh button more prominent
    refresh_col1, refresh_col2 = st.columns([1, 3])
    with refresh_col1:
        refresh_button = st.button("🔄 Refresh PDF List", type="primary")
    with refresh_col2:
        st.info("Click this button to update processing status and view latest results")

    if refresh_button:
        # Check for messages first
        check_message_queue()
        st.rerun()

    # Status indicator and summary metrics
    col1, col2, col3, col4 = st.columns(4)
    pdf_count = len(list(PDFS_DIR.glob("*.pdf")))

    # Count processed files more accurately by checking both old and new structures
    processed_files = []
    if (PROCESSED_DIR / "docs").exists():
        # Count both top-level text files (old structure) and files in individual folders (new structure)
        for pdf_file in PDFS_DIR.glob("*.pdf"):
            pdf_stem = pdf_file.stem
            # Check if processed in new folder structure
            if (PROCESSED_DIR / "docs" / pdf_stem / f"{pdf_stem}.txt").exists():
                processed_files.append(pdf_stem)
            # Or if processed in old structure
            elif (PROCESSED_DIR / "docs" / f"{pdf_stem}.txt").exists():
                processed_files.append(pdf_stem)

    processed_count = len(processed_files)
    # Only count markdown files in the new structure
    md_count = len(list((PROCESSED_DIR / "docs").glob("*/*.md"))) if (PROCESSED_DIR / "docs").exists() else 0

    # Calculate a more accurate processing rate based on unique PDFs processed
    processing_rate = round((processed_count / max(1, pdf_count)) * 100)

    # Add tooltips (help text) to explain each metric
    col1.metric("PDF Files", pdf_count, help="Total number of PDF files in the pdfs directory")
    col2.metric("Processed Files", processed_count, help="Number of PDFs that have been processed into text files")
    col3.metric("Markdown Files", md_count, help="Number of PDFs that have been converted to Markdown format")
    col4.metric("Processing Rate", f"{processing_rate}%" if pdf_count > 0 else "0%",
               help="Percentage of available PDFs that have been successfully processed (Processed Files ÷ PDF Files × 100%)")

    # Processing status and log section - moved up to be more visible
    if st.session_state.is_processing or st.session_state.processing_log:
        st.subheader("Processing Status & Log")

        # Status indicators
        if st.session_state.processing_status == "PROCESSING":
            st.markdown("<p class='status-processing'>⏳ Processing in progress... Click 'Refresh PDF List' for updates</p>", unsafe_allow_html=True)
            st.progress(0.5)  # Indeterminate progress
        elif st.session_state.processing_status == "COMPLETE":
            st.markdown("<p class='status-success'>✅ Processing complete</p>", unsafe_allow_html=True)
        elif st.session_state.processing_status == "ERROR":
            st.markdown("<p class='status-error'>❌ Processing failed</p>", unsafe_allow_html=True)

        # Reset button for stuck processing
        if st.session_state.processing_status == "PROCESSING":
            reset_col1, reset_col2 = st.columns([1, 3])
            with reset_col1:
                reset_button = st.button("⚠️ Reset Status (If Stuck)")
                if reset_button:
                    st.session_state.processing_status = None
                    st.session_state.is_processing = False
                    st.session_state.processing_log = []
                    st.rerun()
            with reset_col2:
                st.info("If processing is stuck (no progress for >30 seconds), you can reset the status.")

        # Processing log
        if st.session_state.processing_log:
            st.markdown("<div class='log-container'>", unsafe_allow_html=True)
            for line in st.session_state.processing_log:
                st.text(line)
            st.markdown("</div>", unsafe_allow_html=True)

            # Clear log button
            clear_log = st.button("Clear Log")
            if clear_log:
                st.session_state.processing_log = []
                st.rerun()

    st.divider()

    # Show PDF list
    pdfs = list(PDFS_DIR.glob("*.pdf"))
    if pdfs:
        pdf_data = []
        for pdf in pdfs:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(pdf.stat().st_mtime).strftime("%Y-%m-%d %H:%M")

            # Check if processed in new folder structure
            individual_folder = (PROCESSED_DIR / "docs" / pdf.stem)
            if individual_folder.exists() and (individual_folder / f"{pdf.stem}.txt").exists():
                processed = True
                has_json = (individual_folder / f"{pdf.stem}.json").exists()
                has_md = (individual_folder / f"{pdf.stem}.md").exists()
            else:
                # Fallback to old structure for compatibility
                processed = (PROCESSED_DIR / "docs" / f"{pdf.stem}.txt").exists()
                has_json = False
                has_md = False

            pdf_data.append({
                "Filename": pdf.name,
                "Size (MB)": round(size_mb, 2),
                "Modified": mod_time,
                "Processed": "✅" if processed else "❌",
                "Individual Folder": "✅" if individual_folder.exists() else "❌",
                "Has JSON": "✅" if has_json else "❌",
                "Has Markdown": "✅" if has_md else "❌"
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
        is_processing = st.session_state.is_processing

        process_button = st.button("Process PDFs", type="primary", disabled=is_processing)
        if process_button:
            process_pdfs_in_thread(force=force_reprocess, skip_openwebui=skip_openwebui)
            st.info("⏳ Processing started. Check the processing log above for progress.")
    else:
        st.info("No PDFs found. Please upload PDFs first.")

# Search page
def render_search_page():
    st.header("Search Documents")

    # Add debug information at the top
    st.info("Debug info: Checking if chunks exist...")

    # Check if chunks exist
    chunk_files = list(CHUNKS_DIR.glob("*_chunks.json"))
    st.write(f"Found {len(chunk_files)} chunk files: {[f.name for f in chunk_files]}")

    if not chunk_files:
        st.warning("No processed content found. Please process PDFs first.")
        return

    # Simple search interface
    st.subheader("Simple Keyword Search")
    query = st.text_input("Enter search query:")
    search_button = st.button("Search")

    if search_button and query:
        with st.spinner("Searching..."):
            st.write(f"Searching for: '{query}'")
            results = run_simple_search(query)
            st.session_state.search_results = results

    # Display search results
    if st.session_state.search_results:
        st.subheader("Search Results")

        st.write(f"Result type: {type(st.session_state.search_results)}")

        if isinstance(st.session_state.search_results, str):
            st.info(st.session_state.search_results)
        else:
            st.write(f"Found {len(st.session_state.search_results)} results")
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
        - Import collections from `processed_docs/openwebui/`

    - **Ollama RAG**: Local AI-powered question answering
        - Run `./run_rag_interactive.sh` in terminal
        - Uses Ollama for embeddings and generation
    """)

# Collections page
def render_collections_page():
    st.header("Collection Management")

    # Add debug information
    st.info("Debug info: Checking OpenWebUI collection...")

    # Open WebUI Collections
    st.subheader("Open WebUI Collections")

    openwebui_file = OPENWEBUI_DIR / "knowledge_collection.json"  # Changed from ibm_knowledge_collection.json
    st.write(f"Looking for collection file: {openwebui_file}")
    st.write(f"File exists: {openwebui_file.exists()}")

    if openwebui_file.exists():
        try:
            st.write("Attempting to load collection file...")
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
            is_processing = st.session_state.is_processing
            update_button = st.button("Update Collection", type="primary", disabled=is_processing)
            if update_button:
                process_pdfs_in_thread(force=False, skip_openwebui=False)
                st.info("⏳ Collection update started. Check the Upload & Process tab for progress.")

        except Exception as e:
            st.error(f"Error loading collection: {str(e)}")
            st.exception(e)  # This will show the full exception traceback
    else:
        st.warning("No Open WebUI collection found. Please process PDFs first.")

    # Individual Document Collections
    st.divider()
    st.subheader("Individual Document Collections")

    # Find all document folders
    doc_folders = list((PROCESSED_DIR / "docs").glob("*/"))

    if doc_folders:
        # Get data about individual JSON files
        individual_docs = []
        for folder in doc_folders:
            doc_name = folder.name
            json_file = folder / f"{doc_name}.json"
            txt_file = folder / f"{doc_name}.txt"
            md_file = folder / f"{doc_name}.md"

            if json_file.exists() and txt_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        doc_data = json.load(f)

                    individual_docs.append({
                        "Title": doc_data.get("title", doc_name),
                        "Pages": doc_data.get("pages", "Unknown"),
                        "Chunks": doc_data.get("chunks_count", 0),
                        "Folder": str(folder),
                        "JSON": str(json_file),
                        "TXT": str(txt_file),
                        "MD": str(md_file) if md_file.exists() else "Not available",
                        "Has MD": "✅" if md_file.exists() else "❌",
                        "Date": doc_data.get("processed_date", "Unknown")
                    })
                except Exception as e:
                    st.error(f"Error loading {json_file}: {str(e)}")

        if individual_docs:
            st.markdown(f"Found {len(individual_docs)} individual document collections")
            df = pd.DataFrame(individual_docs)
            st.dataframe(df, use_container_width=True)

            # Add a section to view markdown files
            st.subheader("View Markdown Files")

            # Create a selectbox with document titles
            doc_titles = [doc["Title"] for doc in individual_docs if doc["Has MD"] == "✅"]

            if doc_titles:
                selected_doc = st.selectbox("Select a document to view", doc_titles)

                # Find the selected document
                selected_md_path = None
                for doc in individual_docs:
                    if doc["Title"] == selected_doc and doc["Has MD"] == "✅":
                        selected_md_path = Path(doc["MD"])
                        break

                if selected_md_path and selected_md_path.exists():
                    with open(selected_md_path, "r") as f:
                        md_content = f.read()

                    # Display the markdown content
                    st.markdown(md_content)

                    # Add a download button for the markdown file
                    st.download_button(
                        label="Download Markdown File",
                        data=md_content,
                        file_name=f"{selected_doc}.md",
                        mime="text/markdown"
                    )
            else:
                st.info("No Markdown files available. Process PDFs with the updated script to create them.")

            # Instructions for individual document import
            st.subheader("Individual Document Import")
            st.markdown("""
            You can import individual documents to Open WebUI:

            1. Open [Open WebUI](http://localhost:3000/)
            2. Go to Collections > Your Collection > Import Document
            3. Browse to the specific document JSON file in its folder
            4. Import the document

            This allows you to selectively add documents to collections.
            """)
        else:
            st.info("No individual document collections found with the new format.")
    else:
        st.info("No individual document folders found. Process PDFs with the updated script to create them.")

# Main app layout
def main():
    # Check the global message queue for updates
    check_message_queue()

    # Additional check to reset stale processing state
    if st.session_state.processing_status == "PROCESSING" and not st.session_state.is_processing:
        elapsed_time = time.time() - st.session_state.last_check_time
        if elapsed_time > 10:  # If more than 10 seconds have passed
            st.session_state.processing_status = None
            st.session_state.processing_log.append("⚠️ Processing state was stale - automatically reset")
            st.session_state.last_check_time = time.time()

    st.title("DocRAG")
    st.write("A comprehensive tool for processing PDF documents and generating RAG knowledge bases")

    # Simple tab system that doesn't rely on tracking active tabs
    tab_names = ["Upload & Process", "Search", "Collections"]
    tab1, tab2, tab3 = st.tabs(tab_names)

    # Display Upload tab
    with tab1:
        render_upload_page()

    # Display Search tab
    with tab2:
        render_search_page()

    # Display Collections tab
    with tab3:
        render_collections_page()

    # No more auto-refresh mechanism - we'll rely on manual refresh instead

# Run the app
if __name__ == "__main__":
    main()
