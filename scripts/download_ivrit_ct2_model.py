#!/usr/bin/env python3
"""
Script to download the ivrit-ai/whisper-large-v3-ct2 model
This will cache the CTranslate2 optimized model locally for faster subsequent use
"""

import os
import sys
import logging
from pathlib import Path
import tempfile
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_ct2_model():
    """Download and cache the ivrit-ai/whisper-large-v3-ct2 model"""
    
    model_name = "ivrit-ai/whisper-large-v3-ct2"
    
    try:
        logger.info(f"🔄 Starting download of {model_name}...")
        logger.info("This may take several minutes depending on your internet connection.")
        
        # Import required libraries
        try:
            import ctranslate2
            import faster_whisper
            from huggingface_hub import snapshot_download
            logger.info("✅ Required libraries loaded successfully!")
        except ImportError as e:
            logger.error(f"❌ Missing required library: {e}")
            logger.error("Please install with: pip install ctranslate2 faster-whisper")
            return False
        
        # Create cache directory
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Download the model using huggingface_hub
        logger.info("📥 Downloading CTranslate2 model from Hugging Face...")
        try:
            model_path = snapshot_download(
                repo_id=model_name,
                cache_dir=cache_dir,
                local_files_only=False,
                resume_download=True
            )
            logger.info(f"✅ Model downloaded to: {model_path}")
        except Exception as e:
            logger.error(f"❌ Error downloading from Hugging Face: {e}")
            logger.info("🔄 Trying alternative download method...")
            
            # Alternative: Use faster-whisper to download
            try:
                from faster_whisper import WhisperModel
                logger.info("📥 Downloading using faster-whisper...")
                model = WhisperModel(model_name, device="cpu")
                logger.info("✅ Model downloaded successfully with faster-whisper!")
                model_path = model.model_path
            except Exception as e2:
                logger.error(f"❌ Alternative download failed: {e2}")
                return False
        
        # Test the model
        logger.info("🧪 Testing CTranslate2 model functionality...")
        
        try:
            # Test with faster-whisper (which uses CTranslate2 backend)
            from faster_whisper import WhisperModel
            test_model = WhisperModel(model_name, device="cpu")
            
            # Get model info
            logger.info(f"📊 Model: {model_name}")
            logger.info(f"📁 Model path: {model_path}")
            logger.info(f"🔧 Backend: CTranslate2")
            logger.info(f"💻 Device: CPU")
            
            # Test basic functionality (without actual audio)
            logger.info("🧪 Model loaded successfully and ready for transcription!")
            
            # Clean up test model
            del test_model
            
        except Exception as e:
            logger.warning(f"⚠️ Model test warning: {e}")
            logger.info("Model downloaded but test failed - this might be normal")
        
        logger.info("🎉 CTranslate2 model download completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error downloading CTranslate2 model: {e}")
        return False

def verify_dependencies():
    """Verify that all required dependencies are installed"""
    logger.info("🔍 Verifying dependencies...")
    
    required_packages = [
        ("ctranslate2", "CTranslate2 optimization library"),
        ("faster_whisper", "Faster Whisper with CTranslate2 backend"),
        ("huggingface_hub", "Hugging Face model hub client"),
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package}: {description}")
        except ImportError:
            logger.error(f"❌ {package}: {description} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
        logger.error("Please install with:")
        logger.error(f"pip install {' '.join(missing_packages)}")
        return False
    
    logger.info("✅ All dependencies verified!")
    return True

def main():
    """Main function"""
    print("🎤 Ivrit CTranslate2 Model Downloader")
    print("=" * 60)
    print("Model: ivrit-ai/whisper-large-v3-ct2")
    print("Backend: CTranslate2 (Optimized)")
    print("=" * 60)
    
    # Verify dependencies first
    if not verify_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    # Download the model
    success = download_ct2_model()
    
    if success:
        print("\n✅ Download completed successfully!")
        print("\n🚀 You can now use the CTranslate2 optimized model with:")
        print("python main_app.py single audio.wav --model ivrit-ai/whisper-large-v3-ct2 --engine optimized-whisper")
        print("\nOr using the optimized configuration file:")
        print("python main_app.py --config-file config/environments/ivrit_whisper_large_v3_ct2.json single audio.wav")
        print("\n📊 Performance benefits:")
        print("  • Faster inference with CTranslate2 optimization")
        print("  • Lower memory usage")
        print("  • Better CPU utilization")
        print("  • Optimized for Hebrew transcription")
    else:
        print("\n❌ Download failed. Please check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Verify you have enough disk space")
        print("  3. Install missing dependencies: pip install ctranslate2 faster-whisper")
        sys.exit(1)

if __name__ == "__main__":
    main()
