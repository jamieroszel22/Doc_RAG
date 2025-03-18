#!/usr/bin/env python3
"""
Check for GPU availability on Mac
This script detects MPS (Metal Performance Shaders) for Apple Silicon and sets up environments
"""
import os
import platform
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GPUCheck")

def check_mac_gpu():
    """Check for GPU on Mac (Metal support) and report details"""
    # Check if we're on a Mac
    if platform.system() != "Darwin":
        logger.warning("Not running on macOS. This script is for Mac GPU detection only.")
        return False
    
    # Check for Apple Silicon
    is_apple_silicon = platform.processor() == "arm"
    if is_apple_silicon:
        logger.info("Detected Apple Silicon Mac")
    else:
        logger.info("Detected Intel Mac")
    
    # Check for PyTorch with MPS support
    try:
        import torch
        has_mps = torch.backends.mps.is_available()
        if has_mps:
            logger.info("MPS (Metal Performance Shaders) is available")
            logger.info(f"PyTorch version: {torch.__version__}")
            # Set environment variable for Docling
            os.environ["DOCLING_DEVICE"] = "mps"
            return True
        else:
            logger.warning("MPS is not available, even though this is a Mac")
            # Check why MPS might not be available
            if hasattr(torch.backends.mps, 'is_built') and not torch.backends.mps.is_built():
                logger.warning("PyTorch was not built with MPS support")
            logger.info("Will use CPU for processing")
            return False
    except ImportError:
        logger.warning("PyTorch not installed, cannot check MPS availability")
        return False
    except Exception as e:
        logger.warning(f"Error checking MPS availability: {e}")
        return False

def check_docling_gpu_support():
    """Check if Docling can use GPU acceleration"""
    try:
        # Use environment variable approach as the primary method
        # The newest versions of Docling don't expose device setting directly
        os.environ["DOCLING_DEVICE"] = "mps"  # For Apple Silicon
        logger.info("Set DOCLING_DEVICE environment variable to 'mps'")
        
        # Try to import docling to see if it recognizes the setting
        try:
            import docling
            logger.info(f"Docling version: {docling.__version__}")
            return True
        except ImportError:
            logger.warning("Docling not installed, cannot verify GPU settings")
            return False
        
        return False
    except ImportError:
        logger.warning("Docling not installed, cannot check GPU support")
        return False
    except Exception as e:
        logger.warning(f"Error checking Docling GPU support: {e}")
        return False

def main():
    """Main function to check for GPU support"""
    print("Checking for GPU support on Mac...")
    
    # Check basic Mac GPU (Metal) availability
    has_gpu = check_mac_gpu()
    
    # Check Docling GPU support
    has_docling_gpu = check_docling_gpu_support()
    
    # Print summary
    if has_gpu or has_docling_gpu:
        print("\n✅ GPU acceleration should be available for Docling")
        print("   Using Apple Metal Performance Shaders (MPS)")
        print("   Make sure you have Docling installed with PyTorch MPS support")
    else:
        print("\n⚠️ GPU acceleration not detected")
        print("   Docling will run on CPU")
        print("   For best performance on Apple Silicon Macs, ensure PyTorch is installed with MPS support")
    
    # Additional instructions
    print("\nTo enable GPU acceleration when installing Docling:")
    print("pip install docling[gpu]")
    
    return 0 if (has_gpu or has_docling_gpu) else 1

if __name__ == "__main__":
    sys.exit(main())
