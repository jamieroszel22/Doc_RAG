#!/usr/bin/env python3
"""
Redbook Processor for macOS
Uses Docling to process PDF files and prepare them for RAG
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
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.settings import settings
from docling_core.types.doc import ImageRefMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RedBookProcessor")

# Set offline mode for Hugging Face
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Check for GPU support
def check_gpu_available() -> bool:
    """Check if GPU is available for acceleration"""
    try:
        # For Mac with Apple Silicon, try to use MPS
        import platform
        import torch
        
        # Check if this is a Mac
        is_mac = platform.system() == "Darwin"
        
        # Check if MPS is available (Apple Silicon GPU)
        if is_mac and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # Try to set via environment variable instead of direct settings
            os.environ["DOCLING_DEVICE"] = "mps"
            logger.info("MPS (Metal Performance Shaders) GPU acceleration enabled")
            return True
        elif torch.cuda.is_available():
            # Try to set via environment variable for CUDA
            os.environ["DOCLING_DEVICE"] = "cuda"
            logger.info("CUDA GPU acceleration enabled")
            return True
        else:
            logger.info("No GPU acceleration available, using CPU")
            os.environ["DOCLING_DEVICE"] = "cpu"
            return False
    except Exception as e:
        logger.warning(f"Error checking GPU availability: {e}")
        # Set CPU as fallback
        os.environ["DOCLING_DEVICE"] = "cpu"
        logger.info("Using CPU for processing")
        return False

def process_pdfs(
    input_dir: Path,
    output_base_dir: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> Tuple[int, int, int]:
    """
    Process all PDFs in the input directory using Docling
    
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
    
    # Configure Docling
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_page_images = True
    
    # Try to enable GPU if available
    check_gpu_available()
    
    # Create document converter
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    # Process each PDF
    start_time = time.time()
    success_count = 0
    partial_success_count = 0
    failure_count = 0
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing {pdf_file.name}")
            result = doc_converter.convert(pdf_file)
            
            # Generate base filename
            base_filename = pdf_file.stem
            safe_filename = re.sub(r'[^\w\-_.]', '_', base_filename)
            
            # Save document in multiple formats
            result.document.save_as_json(
                docs_dir / f"{safe_filename}.json",
                image_mode=ImageRefMode.PLACEHOLDER,
            )
            result.document.save_as_html(
                docs_dir / f"{safe_filename}.html", 
                image_mode=ImageRefMode.EMBEDDED,
            )
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
            
            # Chunk the document
            chunks = chunk_document(
                text=full_text,
                doc_metadata={
                    "title": safe_filename,
                    "source": str(pdf_file.name),
                    "path": str(pdf_file),
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
    Split a document into chunks with overlap
    
    Args:
        text: The document text to chunk
        doc_metadata: Metadata about the document
        chunk_size: Maximum size of each chunk in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of chunks with text and metadata
    """
    # Simple sentence boundary detection
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_chunk_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        # If adding this sentence would exceed chunk size and we have content,
        # save the current chunk and create a new one with overlap
        if current_chunk_size + sentence_size > chunk_size and current_chunk:
            # Join the sentences in current chunk
            chunk_text = " ".join(current_chunk)
            
            # Add chunk with metadata
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    **doc_metadata,
                    "chunk_index": len(chunks),
                }
            })
            
            # Create overlap by keeping some sentences for the next chunk
            overlap_sentences = []
            overlap_size = 0
            
            # Work backwards through current_chunk to create overlap
            for s in reversed(current_chunk):
                if overlap_size + len(s) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_size += len(s) + 1  # +1 for space
                else:
                    break
            
            # Start new chunk with overlap sentences
            current_chunk = overlap_sentences
            current_chunk_size = overlap_size
        
        # Add the current sentence to the chunk
        current_chunk.append(sentence)
        current_chunk_size += sentence_size + 1  # +1 for space
    
    # Add the last chunk if not empty
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "text": chunk_text,
            "metadata": {
                **doc_metadata,
                "chunk_index": len(chunks),
            }
        })
    
    return chunks

def main():
    parser = argparse.ArgumentParser(description="Process Redbooks PDFs with Docling")
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
