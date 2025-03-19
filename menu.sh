#!/bin/bash
# DocRAG Menu

echo "DocRAG System"
echo "1) Process PDFs"
echo "2) Run simple search"
echo "3) Run Ollama RAG"
echo "4) Exit"
read -p "Choose an option (1-4): " choice

case $choice in
  1)
    echo "Processing PDFs..."
    python3 super_simple.py
    ;;
  2)
    echo "Starting simple query search..."
    if [ -f "./run_simple_query.sh" ]; then
      ./run_simple_query.sh
    else
      echo "Simple query script not found."
    fi
    ;;
  3)
    echo "Starting Ollama RAG..."
    if [ -f "./run_rag_interactive.sh" ]; then
      ./run_rag_interactive.sh
    else
      echo "Ollama RAG script not found."
    fi
    ;;
  4)
    echo "Exiting..."
    exit 0
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac
