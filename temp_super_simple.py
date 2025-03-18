#!/usr/bin/env python3
"""
Super Simple Processor - The absolute simplest approach that's guaranteed to work
"""
import os
import sys
import json
from pathlib import Path

def process_pdfs():
    """Process PDFs using a very simple approach"""
    # Install PyPDF2 if needed
    try:
        import PyPDF2
    except ImportError:
        print("Installing PyPDF2...")
        os.system(f"{sys.executable} -m pip install PyPDF2")
        import PyPDF2

    # Paths
    pdfs_dir = Path("/Users/jamieroszel/Desktop/Docling RAG/pdfs")
    output_dir = Path("/Users/jamieroszel/Desktop/Docling RAG/processed_redbooks")
    docs_dir = output_dir / "docs"
    chunks_dir = output_dir / "chunks"
    ollama_dir = output_dir / "ollama"

    # Create directories
    for d in [docs_dir, chunks_dir, ollama_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Get PDF files
    pdf_files = list(pdfs_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")

    # Process each PDF
    for pdf_file in pdf_files:
        try:
            print(f"Processing {pdf_file.name}")

            # Extract text
            reader = PyPDF2.PdfReader(str(pdf_file))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"

            # Save full text
            name = pdf_file.stem
            with open(docs_dir / f"{name}.txt", "w", encoding="utf-8") as f:
                f.write(text)

            # Create basic chunks (500 chars each with 50 char overlap)
            chunks = []
            chunk_size = 1000
            overlap = 100

            # Simple chunking by characters with overlap
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if chunk:  # Only add non-empty chunks
                    chunks.append({
                        "text": chunk,
                        "metadata": {
                            "source": pdf_file.name,
                            "chunk_index": len(chunks),
                            "total_chunks": (len(text) // (chunk_size - overlap)) + 1
                        }
                    })

            # Save chunks
            with open(chunks_dir / f"{name}_chunks.json", "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2)

            # Save for Ollama
            with open(ollama_dir / f"{name}_ollama.jsonl", "w", encoding="utf-8") as f:
                for chunk in chunks:
                    f.write(json.dumps(chunk) + "\n")

            print(f"Successfully processed {pdf_file.name}")

        except Exception as e:
            print(f"Error with {pdf_file.name}: {e}")

    # Check if we've processed any files
    if len(list(chunks_dir.glob("*_chunks.json"))) > 0:
        return True
    return False

# Run the processor
if process_pdfs():
    print("\nProcessing completed successfully!")
    print("\nYou can now run:")
    print("1. Simple query: ./run_simple_query.sh")
    print("2. Ollama RAG: ./run_rag_interactive.sh")
    sys.exit(0)
else:
    print("\nNo files were processed successfully!")
    sys.exit(1)
