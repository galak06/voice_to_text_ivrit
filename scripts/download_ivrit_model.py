#!/usr/bin/env python3
"""
Script to download the ivrit-ai/whisper-large-v3 model
This will cache the model locally for faster subsequent use
"""

import os
import sys
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_ivrit_model():
    """Download and cache the ivrit-ai/whisper-large-v3 model"""
    
    model_name = "ivrit-ai/whisper-large-v3"
    
    try:
        logger.info(f"🔄 Starting download of {model_name}...")
        logger.info("This may take several minutes depending on your internet connection.")
        
        # Download the processor
        logger.info("📥 Downloading WhisperProcessor...")
        processor = WhisperProcessor.from_pretrained(model_name)
        logger.info("✅ WhisperProcessor downloaded successfully!")
        
        # Download the model
        logger.info("📥 Downloading WhisperForConditionalGeneration model...")
        model = WhisperForConditionalGeneration.from_pretrained(model_name)
        logger.info("✅ WhisperForConditionalGeneration model downloaded successfully!")
        
        # Test the model with a simple operation
        logger.info("🧪 Testing model functionality...")
        
        # Get model info
        model_size = sum(p.numel() for p in model.parameters())
        logger.info(f"📊 Model size: {model_size:,} parameters")
        
        # Check if model supports Hebrew
        if hasattr(model.config, 'language_codes'):
            hebrew_support = 'he' in model.config.language_codes
            logger.info(f"🇮🇱 Hebrew language support: {'✅ Yes' if hebrew_support else '❌ No'}")
        
        logger.info("🎉 Model download and test completed successfully!")
        logger.info(f"📁 Model cached at: {model.config._name_or_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error downloading model: {e}")
        return False

def main():
    """Main function"""
    print("🎤 Ivrit Model Downloader")
    print("=" * 50)
    
    success = download_ivrit_model()
    
    if success:
        print("\n✅ Download completed successfully!")
        print("\n🚀 You can now use the model with:")
        print("python main_app.py single audio.wav --model ivrit-ai/whisper-large-v3 --engine custom-whisper")
        print("\nOr using the configuration file:")
        print("python main_app.py --config-file config/environments/ivrit.json single audio.wav")
    else:
        print("\n❌ Download failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 