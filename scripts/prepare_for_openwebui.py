#!/usr/bin/env python3
"""
Prepare Docling-processed Redbooks for Open WebUI
Converts processed chunks to Open WebUI collection format
"""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any

def load_chunks(chunks_dir: Path) -> List[Dict[str, Any]]:
    """Load all chunks from directory"""
    all_chunks = []
    
    # Find all chunk JSON files
    chunk_files = list(chunks_dir.glob("*_chunks.json"))
    
    if not chunk_files:
        print(f"No chunk files found in {chunks_dir}")
        return []
    
    # Load each file
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
                print(f"Loaded {len(chunks)} chunks from {chunk_file.name}")
        except Exception as e:
            print(f"Error loading {chunk_file}: {str(e)}")
    
    return all_chunks

def prepare_for_openwebui(
    chunks_dir: Path,
    output_file: Path,
    collection_name: str = "IBM Knowledge Base",
):
    """
    Prepare chunks for Open WebUI
    
    Args:
        chunks_dir: Directory containing chunk files
        output_file: Output JSON file for Open WebUI
        collection_name: Name of the collection in Open WebUI
    """
    # Load all chunks
    chunks = load_chunks(chunks_dir)
    
    if not chunks:
        print("No chunks found. Exiting.")
        return
    
    print(f"Loaded {len(chunks)} total chunks")
    
    # Group chunks by document source
    docs_by_source = {}
    for chunk in chunks:
        source = chunk["metadata"]["source"]
        if source not in docs_by_source:
            docs_by_source[source] = []
        docs_by_source[source].append(chunk)
    
    # Create Open WebUI collection structure
    collection = {
        "name": collection_name,
        "documents": []
    }
    
    # Process each document
    for source, doc_chunks in docs_by_source.items():
        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "url": "",
            "title": source,
            "content_chunks": []
        }
        
        # Add chunks for this document
        for i, chunk in enumerate(doc_chunks):
            chunk_id = str(uuid.uuid4())
            document["content_chunks"].append({
                "id": chunk_id,
                "doc_id": doc_id,
                "content": chunk["text"],
                "metadata": {
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(doc_chunks)
                }
            })
        
        collection["documents"].append(document)
    
    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)
    
    print(f"Created Open WebUI collection with {len(collection['documents'])} documents")
    print(f"Saved to {output_file}")
    
    # Create instructions
    instructions = f"""
Open WebUI Collection Created: {collection_name}

To import this collection into Open WebUI:

1. Open the Open WebUI interface 
2. Go to Collections
3. Click "Import Collection"
4. Select the file: {output_file}
5. Verify the import was successful

You can now use this collection in your RAG workflows in Open WebUI.
"""
    
    print(instructions)
    
    # Save instructions to file
    instructions_file = output_file.parent / f"{output_file.stem}_import_instructions.txt"
    with open(instructions_file, "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print(f"Import instructions saved to {instructions_file}")

def main():
    parser = argparse.ArgumentParser(description="Prepare Redbooks chunks for Open WebUI")
    parser.add_argument(
        "--chunks-dir",
        type=str,
        default="/Users/jamieroszel/Desktop/Docling RAG/processed_redbooks/chunks",
        help="Directory containing chunk files"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="/Users/jamieroszel/Desktop/Docling RAG/processed_redbooks/openwebui/ibm_knowledge_collection.json",
        help="Output JSON file for Open WebUI"
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="IBM Z Knowledge Base",
        help="Name of the collection in Open WebUI"
    )
    
    args = parser.parse_args()
    
    # Prepare chunks for Open WebUI
    prepare_for_openwebui(
        chunks_dir=Path(args.chunks_dir),
        output_file=Path(args.output_file),
        collection_name=args.collection_name,
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
