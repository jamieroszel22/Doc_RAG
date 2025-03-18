#!/usr/bin/env python3
"""
Ollama RAG Integration for Docling-processed Redbooks
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
import requests
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

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

class OllamaRagSystem:
    """Integration with Ollama for embeddings and RAG"""
    
    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "granite3.2:8b-instruct-fp16",
        chunks_dir: Path = None,
        embeddings_cache_dir: Path = None,
        top_k: int = 5,
    ):
        self.ollama_base_url = ollama_base_url
        self.model = model
        self.chunks_dir = chunks_dir
        self.embeddings_cache_dir = embeddings_cache_dir
        self.top_k = top_k
        self.chunks = []
        self.embeddings = []
        
        # Create embeddings cache directory if needed
        if self.embeddings_cache_dir:
            self.embeddings_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # System prompt for IBM technical documentation
        self.system_prompt = """You are an IBM technical expert assistant specializing in IBM Redbooks and technical documentation. 
Your task is to provide accurate, detailed technical information based on the retrieved content.

Guidelines:
1. Focus on providing factual, technical answers based strictly on the provided context
2. When discussing IBM products, be precise about version numbers, compatibility, and technical specifications
3. For technical procedures, provide step-by-step instructions with clear explanations
4. If the answer is not in the provided context, admit that you don't know rather than guessing
5. For complex technical concepts, break them down into clear, understandable explanations
6. Include relevant technical details like command syntax, configuration parameters, or system requirements when available
7. Always cite the source document when providing information
8. Format code snippets, commands, and technical output appropriately

Remember that users are consulting IBM technical documentation to solve specific technical problems or learn about IBM technologies."""
    
    def check_ollama_connection(self) -> bool:
        """Check connection to Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"{Fore.GREEN}Connected to Ollama. Available models:{Style.RESET_ALL}")
                for model in models:
                    print(f"  - {model.get('name')}")
                return True
            else:
                print(f"{Fore.RED}Failed to connect to Ollama: Status code {response.status_code}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}Failed to connect to Ollama: {str(e)}{Style.RESET_ALL}")
            return False
    
    def load_chunks(self) -> bool:
        """Load all chunks from directory"""
        if not self.chunks_dir or not self.chunks_dir.exists():
            print(f"{Fore.RED}Chunks directory does not exist: {self.chunks_dir}{Style.RESET_ALL}")
            return False
        
        # Find all chunk JSON files
        chunk_files = list(self.chunks_dir.glob("*_chunks.json"))
        if not chunk_files:
            print(f"{Fore.RED}No chunk files found in {self.chunks_dir}{Style.RESET_ALL}")
            return False
        
        # Load each file
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                    self.chunks.extend(chunks)
                    print(f"{Fore.GREEN}Loaded {len(chunks)} chunks from {chunk_file.name}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error loading {chunk_file}: {str(e)}{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Loaded {len(self.chunks)} total chunks{Style.RESET_ALL}")
        return len(self.chunks) > 0
    def get_embedding_cache_file(self) -> Path:
        """Get path to embedding cache file for current model"""
        if not self.embeddings_cache_dir:
            return None
        
        # Use model name in cache filename
        safe_model_name = self.model.replace(":", "_").replace("/", "_")
        return self.embeddings_cache_dir / f"embeddings_cache_{safe_model_name}.json"
    
    def load_or_generate_embeddings(self) -> bool:
        """Load embeddings from cache or generate them"""
        cache_file = self.get_embedding_cache_file()
        
        # Try to load from cache first
        if cache_file and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    
                # Check if cache matches current chunks
                if len(cache_data) == len(self.chunks):
                    print(f"{Fore.GREEN}Loaded embeddings from cache: {cache_file}{Style.RESET_ALL}")
                    self.embeddings = [np.array(emb) for emb in cache_data]
                    return True
                else:
                    print(f"{Fore.YELLOW}Embedding cache size mismatch ({len(cache_data)} vs {len(self.chunks)} chunks), regenerating...{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Failed to load embeddings cache: {str(e)}, regenerating...{Style.RESET_ALL}")
        
        # Generate embeddings
        print(f"{Fore.BLUE}Generating embeddings for {len(self.chunks)} chunks using {self.model}...{Style.RESET_ALL}")
        self.embeddings = []
        
        for i, chunk in enumerate(self.chunks):
            try:
                if i % 10 == 0:
                    print(f"{Fore.BLUE}Processing chunk {i+1}/{len(self.chunks)}{Style.RESET_ALL}")
                
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={"model": self.model, "prompt": chunk["text"]}
                )
                
                if response.status_code == 200:
                    embedding = response.json().get("embedding", [])
                    self.embeddings.append(np.array(embedding))
                else:
                    print(f"{Fore.RED}Failed to get embedding for chunk {i}: Status code {response.status_code}{Style.RESET_ALL}")
                    return False
                
                # Add a small delay to avoid overwhelming Ollama
                time.sleep(0.1)
                
            except Exception as e:
                print(f"{Fore.RED}Error generating embedding for chunk {i}: {str(e)}{Style.RESET_ALL}")
                return False
        
        # Save to cache
        if cache_file:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump([emb.tolist() for emb in self.embeddings], f)
                print(f"{Fore.GREEN}Saved embeddings to cache: {cache_file}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Failed to save embeddings cache: {str(e)}{Style.RESET_ALL}")
        
        return True
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0
        return np.dot(vec1, vec2) / (norm1 * norm2)
    def semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """Search for chunks semantically similar to query"""
        # Get embedding for query
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={"model": self.model, "prompt": query}
            )
            
            if response.status_code != 200:
                print(f"{Fore.RED}Failed to get query embedding: Status code {response.status_code}{Style.RESET_ALL}")
                return []
            
            query_embedding = np.array(response.json().get("embedding", []))
            
            # Calculate similarity scores
            scores = [self.cosine_similarity(query_embedding, emb) for emb in self.embeddings]
            
            # Get top k results
            top_indices = np.argsort(scores)[-self.top_k:][::-1]
            results = []
            
            for i in top_indices:
                results.append({
                    "text": self.chunks[i]["text"],
                    "score": float(scores[i]),
                    "metadata": self.chunks[i]["metadata"]
                })
            
            return results
            
        except Exception as e:
            print(f"{Fore.RED}Error in semantic search: {str(e)}{Style.RESET_ALL}")
            return []
    
    def generate_rag_response(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate RAG response using Ollama"""
        if not results:
            return "No relevant information found in the IBM Redbooks."
        
        # Prepare context from results
        context = ""
        for i, result in enumerate(results):
            context += f"Document: {result['metadata']['source']}\n"
            context += f"Text: {result['text']}\n\n"
        
        # Prepare message for Ollama
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Context information:\n\n{context}\n\nBased on the above IBM documentation, answer this question: {query}"}
        ]
        
        try:
            # Call Ollama chat completion API
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False}
            )
            
            if response.status_code != 200:
                print(f"{Fore.RED}Failed to generate response: Status code {response.status_code}{Style.RESET_ALL}")
                return f"Error generating response: Status code {response.status_code}"
            
            # Extract content from response
            response_content = response.json().get("message", {}).get("content", "")
            return response_content
            
        except Exception as e:
            print(f"{Fore.RED}Error generating response: {str(e)}{Style.RESET_ALL}")
            return f"Error generating response: {str(e)}"
    
    def interactive_rag(self):
        """Run interactive RAG session"""
        print(f"{Fore.BLUE}Starting interactive RAG session with {self.model}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Type 'quit' to exit{Style.RESET_ALL}")
        
        while True:
            query = input(f"{Fore.GREEN}> {Style.RESET_ALL}")
            
            if query.lower() in ["quit", "exit", "q"]:
                break
            
            if not query.strip():
                continue
            
            # Get semantically similar chunks
            print(f"{Fore.BLUE}Searching for relevant information...{Style.RESET_ALL}")
            results = self.semantic_search(query)
            
            if not results:
                print(f"{Fore.YELLOW}No relevant information found{Style.RESET_ALL}")
                continue
            
            # Generate RAG response
            print(f"{Fore.BLUE}Generating response...{Style.RESET_ALL}")
            response = self.generate_rag_response(query, results)
            
            # Print response
            print(f"\n{Fore.YELLOW}Response:{Style.RESET_ALL}")
            print(response)
            print("\n" + "-" * 80 + "\n")
def main():
    parser = argparse.ArgumentParser(description="Ollama RAG for Redbooks")
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API base URL"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="granite3.2:8b-instruct-fp16",
        help="Ollama model to use"
    )
    parser.add_argument(
        "--chunks-dir",
        type=str,
        default="/Users/jamieroszel/Desktop/Docling RAG/processed_redbooks/chunks",
        help="Directory containing chunk files"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="/Users/jamieroszel/Desktop/Docling RAG/processed_redbooks/embeddings_cache",
        help="Directory for embeddings cache"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top chunks to retrieve"
    )
    
    args = parser.parse_args()
    
    # Create RAG system
    rag_system = OllamaRagSystem(
        ollama_base_url=args.ollama_url,
        model=args.model,
        chunks_dir=Path(args.chunks_dir),
        embeddings_cache_dir=Path(args.cache_dir),
        top_k=args.top_k,
    )
    
    # Check Ollama connection
    if not rag_system.check_ollama_connection():
        print(f"{Fore.RED}Cannot connect to Ollama. Make sure it's running.{Style.RESET_ALL}")
        return 1
    
    # Load chunks
    if not rag_system.load_chunks():
        print(f"{Fore.RED}Failed to load chunks. Process some documents first.{Style.RESET_ALL}")
        return 1
    
    # Load or generate embeddings
    if not rag_system.load_or_generate_embeddings():
        print(f"{Fore.RED}Failed to load or generate embeddings.{Style.RESET_ALL}")
        return 1
    
    # Run interactive RAG
    try:
        rag_system.interactive_rag()
    except KeyboardInterrupt:
        print("\nExiting RAG session")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
