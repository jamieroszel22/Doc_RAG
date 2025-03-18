#!/bin/bash
# Combine Ollama RAG parts into a single file

# Path to the combined file
COMBINED_FILE="/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag.py"

# Combine parts
cat "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_integration.py" > "$COMBINED_FILE"
tail -n +1 "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_part2.py" >> "$COMBINED_FILE"
tail -n +1 "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_part3.py" >> "$COMBINED_FILE"
tail -n +1 "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_part4.py" >> "$COMBINED_FILE"

# Make the combined file executable
chmod +x "$COMBINED_FILE"

echo "Combined Ollama RAG script created at $COMBINED_FILE"
echo "Removing parts..."

# Remove parts after successful combination
if [ -f "$COMBINED_FILE" ]; then
    rm "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_part2.py"
    rm "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_part3.py"
    rm "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_part4.py"
    rm "/Users/jamieroszel/Desktop/Docling RAG/scripts/ollama_rag_integration.py"
    echo "Parts removed."
else
    echo "Error: Combined file not created."
    exit 1
fi
