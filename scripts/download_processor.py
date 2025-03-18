#!/usr/bin/env python3
"""
Download processor for macOS
Uses Docling to download required models first
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
logger = logging.getLogger("DownloadProcessor")

# Set MPS for Apple Silicon
os.environ["DOCLING_DEVICE"] = "mps"

# Enable online mode for initial model download
os.environ["TRANSFORMERS_OFFLINE"] = "0"
os.environ["HF_DATASETS_OFFLINE"] = "0"
os.environ["HF_HUB_OFFLINE"] = "0"

def download_models():
    """
    Download required models for Docling
    """
    logger.info("Attempting to download required models...")
    try:
        # Create a minimal document converter which will trigger model downloads
        converter = DocumentConverter()
        logger.info("Models should be downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download models: {str(e)}")
        return False

def main():
    # Download models
    success = download_models()
    
    if success:
        logger.info("Models downloaded successfully")
        logger.info("You can now process documents with MPS acceleration")
        logger.info("Run the simple processor with: ./simple_process.sh")
    else:
        logger.error("Failed to download models")
        logger.error("Try setting HF_HUB_OFFLINE=0 and running again")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
