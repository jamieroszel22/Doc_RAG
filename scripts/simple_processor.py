#!/usr/bin/env python3
"""
Simple Redbook Processor for macOS
Uses Docling to process PDF files with minimal configuration
"""
import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import Docling components
from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimpleProcessor")

# Set offline mode for Hugging Face
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Set MPS for Apple Silicon
os.environ["DOCLING_DEVICE"] = "mps"

def process_pdfs(
    input_dir: Path,
    output_base_dir: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> Tuple[int, int, int]:
    """
    Process all PDFs in the input directory using Docling with minimal configuration
    
    Args:
        input_dir: Directory containing PDF files
        output_base_dir: Base directory for outputs
        chunk_size: Size of chunks for RAG
        chunk_overlap: Overlap between chunks
        
    Returns:
        Tuple of (success_count, partial_success_count, failure_count)
    """
    # Create output directories
    docs_dir = output_base_dir / "docs"
    chunks_dir = output_base_dir / "chunks"
    ollama_dir = output_base_dir / "ollama"
    
    for directory in [docs_dir, chunks_dir, ollama_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files
    pdf_files = list(input_dir.glob("**/*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return 0, 0, 0
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Create document converter with minimal configuration - try both with and without offline mode
    try:
        # First attempt with offline mode in case models are already downloaded
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"
        doc_converter = DocumentConverter()
        logger.info("Using offline mode with pre-downloaded models")
    except Exception as e:
        # If that fails, try with online mode
        logger.warning(f"Failed to load in offline mode: {e}")
        logger.info("Trying with online mode - this will download models")
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        os.environ["HF_DATASETS_OFFLINE"] = "0"
        os.environ["HF_HUB_OFFLINE"] = "0"
        doc_converter = DocumentConverter()
    
    # Process each PDF
    start_time = time.time()
    success_count = 0
    partial_success_count = 0
    failure_count = 0
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing {pdf_file.name}")
            
            # Simple conversion with minimal options
            result = doc_converter.convert(pdf_file)
            
            # Generate base filename
            base_filename = pdf_file.stem
            safe_filename = re.sub(r'[^\w\-_.]', '_', base_filename)
            
            # Save document in multiple formats
            result.document.save_as_markdown(
                docs_dir / f"{safe_filename}.md",
                image_mode=ImageRefMode.PLACEHOLDER,
            )
            result.document.save_as_markdown(
                docs_dir / f"{safe_filename}.txt",
                image_mode=ImageRefMode.PLACEHOLDER,
                strict_text=True,
            )
            
            # Get full text for chunking
            full_text = result.document.export_to_markdown(strict_text=True)
            
            # Chunk the document - simple version
            chunks = chunk_document(
                text=full_text,
                doc_metadata={
                    "title": safe_filename,
                    "source": str(pdf_file.name),
                },
                chunk_size=chunk_size,
                overlap=chunk_overlap,
            )
            
            # Save chunks
            chunk_file = chunks_dir / f"{safe_filename}_chunks.json"
            with open(chunk_file, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            
            # Create Ollama compatible format
            ollama_chunks = []
            for i, chunk in enumerate(chunks):
                ollama_chunks.append({
                    "text": chunk["text"],
                    "metadata": {
                        "source": chunk["metadata"]["source"],
                        "chunk_id": i,
                        "total_chunks": len(chunks)
                    }
                })
            
            # Save Ollama format
            ollama_file = ollama_dir / f"{safe_filename}_ollama.jsonl"
            with open(ollama_file, "w", encoding="utf-8") as f:
                for chunk in ollama_chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            
            success_count += 1
            logger.info(f"Successfully processed {pdf_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {str(e)}")
            failure_count += 1
    
    end_time = time.time() - start_time
    logger.info(f"Processed {len(pdf_files)} documents in {end_time:.2f} seconds")
    logger.info(f"Success: {success_count}, Partial: {partial_success_count}, Failed: {failure_count}")
    
    return success_count, partial_success_count, failure_count

def chunk_document(
    text: str,
    doc_metadata: Dict[str, Any],
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Split a document into chunks with overlap - simple version
    
    Args:
        text: The document text to chunk
        doc_metadata: Metadata about the document
        chunk_size: Maximum size of each chunk in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of chunks with text and metadata
    """
    chunks = []
    
    # Simple paragraph-based chunking
    paragraphs = text.split("\n\n")
    
    current_chunk_text = ""
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size and we have content,
        # save the current chunk and start a new one
        if len(current_chunk_text) + len(paragraph) > chunk_size and current_chunk_text:
            # Add chunk with metadata
            chunks.append({
                "text": current_chunk_text,
                "metadata": {
                    **doc_metadata,
                    "chunk_index": len(chunks),
                }
            })
            
            # Start a new chunk with some overlap
            # Take the last part of the previous chunk for overlap
            words = current_chunk_text.split()
            overlap_text = ""
            if len(words) > 50:  # arbitrary number of words for overlap
                overlap_text = " ".join(words[-50:]) + "\n\n"
            current_chunk_text = overlap_text
        
        # Add the paragraph to the current chunk
        if current_chunk_text and not current_chunk_text.endswith("\n\n"):
            current_chunk_text += "\n\n"
        current_chunk_text += paragraph
    
    # Add the last chunk if not empty
    if current_chunk_text:
        chunks.append({
            "text": current_chunk_text,
            "metadata": {
                **doc_metadata,
                "chunk_index": len(chunks),
            }
        })
    
    return chunks

def main():
    parser = argparse.ArgumentParser(description="Simple Redbooks PDFs Processor with Docling")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="/Users/jamieroszel/Desktop/Docling RAG/pdfs",
        help="Directory containing PDF files to process"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/Users/jamieroszel/Desktop/Docling RAG/processed_redbooks",
        help="Base directory for output files"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Size of chunks for RAG"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Overlap between chunks"
    )
    
    args = parser.parse_args()
    
    # Process PDFs
    success, partial, failed = process_pdfs(
        input_dir=Path(args.input_dir),
        output_base_dir=Path(args.output_dir),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    
    if failed > 0:
        logger.warning(f"Failed to process {failed} documents")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
