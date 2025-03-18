#!/usr/bin/env python3
"""
Simple Query System for Docling-processed Redbooks
Uses keyword-based search without requiring a full LLM
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import glob

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False
    class DummyFore:
        GREEN = ""
        YELLOW = ""
        RED = ""
        BLUE = ""
        RESET = ""
    class DummyStyle:
        BRIGHT = ""
        RESET_ALL = ""
    Fore = DummyFore()
    Style = DummyStyle()

def load_chunks(chunks_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all chunk files from directory
    
    Args:
        chunks_dir: Directory containing chunk JSON files
        
    Returns:
        List of all chunks with their metadata
    """
    all_chunks = []
    
    # Find all chunk JSON files
    chunk_files = list(chunks_dir.glob("*_chunks.json"))
    
    if not chunk_files:
        print(f"{Fore.RED}No chunk files found in {chunks_dir}{Style.RESET_ALL}")
        return []
    
    # Load each file
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
                print(f"{Fore.GREEN}Loaded {len(chunks)} chunks from {chunk_file.name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error loading {chunk_file}: {str(e)}{Style.RESET_ALL}")
    
    return all_chunks

def simple_search(chunks: List[Dict[str, Any]], query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Perform simple keyword search on chunks
    
    Args:
        chunks: List of text chunks with metadata
        query: Search query string
        top_k: Number of top results to return
        
    Returns:
        List of ranked results with highlighted text
    """
    if not chunks:
        return []
    
    # Tokenize query into terms
    query_terms = re.findall(r'\w+', query.lower())
    if not query_terms:
        return []
    
    # Score each chunk
    scored_chunks = []
    for chunk in chunks:
        text = chunk["text"].lower()
        score = 0
        
        # Simple term frequency scoring
        for term in query_terms:
            term_count = len(re.findall(r'\b' + re.escape(term) + r'\b', text))
            score += term_count
        
        # Only keep chunks with matches
        if score > 0:
            # Highlight matched terms in the text
            highlighted_text = highlight_terms(chunk["text"], query_terms)
            
            scored_chunks.append({
                "text": highlighted_text,
                "score": score,
                "metadata": chunk["metadata"]
            })
    
    # Sort by score (descending)
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    
    # Return top k results
    return scored_chunks[:top_k]

def highlight_terms(text: str, terms: List[str], context_size: int = 100) -> str:
    """
    Highlight search terms in text and provide context
    
    Args:
        text: Original text
        terms: Search terms to highlight
        context_size: Number of characters of context around matches
        
    Returns:
        Highlighted text with context
    """
    # Find all positions of all terms
    matches = []
    for term in terms:
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end()))
    
    # If no matches, return a snippet of the text
    if not matches:
        return text[:200] + "..."
    
    # Sort matches by position
    matches.sort()
    
    # Merge overlapping matches
    merged_matches = []
    for match in matches:
        if not merged_matches or match[0] > merged_matches[-1][1]:
            merged_matches.append(match)
        else:
            merged_matches[-1] = (merged_matches[-1][0], max(merged_matches[-1][1], match[1]))
    
    # Create highlighted text with context
    result = ""
    last_end = 0
    
    for i, (start, end) in enumerate(merged_matches):
        # Calculate context boundaries
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        
        # Add ellipsis if not starting from beginning
        if context_start > 0 and (i == 0 or context_start > merged_matches[i-1][1] + context_size):
            result += "... "
        
        # Add text before match
        if context_start < start:
            result += text[context_start:start]
        
        # Add highlighted match
        if COLOR_AVAILABLE:
            result += f"{Fore.YELLOW}{Style.BRIGHT}{text[start:end]}{Style.RESET_ALL}"
        else:
            result += f"**{text[start:end]}**"
        
        # Add text after match
        if end < context_end:
            result += text[end:context_end]
        
        # Add ellipsis if not ending at end of text
        if context_end < len(text) and (i == len(merged_matches) - 1 or context_end < merged_matches[i+1][0] - context_size):
            result += " ..."
        
        last_end = context_end
    
    return result

def interactive_search(chunks_dir: Path):
    """
    Run interactive search loop
    
    Args:
        chunks_dir: Directory containing chunk files
    """
    print(f"{Fore.BLUE}Loading chunks from {chunks_dir}...{Style.RESET_ALL}")
    chunks = load_chunks(chunks_dir)
    
    if not chunks:
        print(f"{Fore.RED}No chunks loaded. Exiting.{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}Loaded {len(chunks)} total chunks from {chunks_dir}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Enter search queries (type 'quit' to exit):{Style.RESET_ALL}")
    
    while True:
        query = input(f"{Fore.GREEN}> {Style.RESET_ALL}")
        
        if query.lower() in ["quit", "exit", "q"]:
            break
        
        if not query.strip():
            continue
        
        results = simple_search(chunks, query)
        
        if not results:
            print(f"{Fore.YELLOW}No results found for '{query}'{Style.RESET_ALL}")
            continue
        
        print(f"{Fore.GREEN}Found {len(results)} results for '{query}':{Style.RESET_ALL}\n")
        
        for i, result in enumerate(results):
            print(f"{Fore.BLUE}Result {i+1} (Score: {result['score']}):{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Source: {result['metadata']['source']}{Style.RESET_ALL}")
            print(f"{result['text']}\n")
            print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Simple search for Redbooks chunks")
    parser.add_argument(
        "--chunks-dir",
        type=str,
        default="/Users/jamieroszel/Desktop/Docling RAG/processed_redbooks/chunks",
        help="Directory containing chunk files"
    )
    
    args = parser.parse_args()
    
    try:
        interactive_search(Path(args.chunks_dir))
    except KeyboardInterrupt:
        print("\nExiting search")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
