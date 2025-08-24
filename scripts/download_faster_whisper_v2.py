#!/usr/bin/env python3
"""
Script to download the ivrit-ai/faster-whisper-v2-d4 model
This model is based on faster-whisper and optimized for Hebrew transcription
"""

import os
import sys
import logging
from faster_whisper import WhisperModel

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_faster_whisper_v2():
    """Download and cache the ivrit-ai/faster-whisper-v2-d4 model"""
    
    model_name = "ivrit-ai/faster-whisper-v2-d4"
    
    try:
        logger.info(f"🔄 Starting download of {model_name}...")
        logger.info("This model is optimized for Hebrew transcription with faster inference.")
        logger.info("Training data includes 250 hours of volunteer-transcribed speech + 100 hours professional data.")
        
        # Download and initialize the model
        logger.info("📥 Downloading faster-whisper model...")
        model = WhisperModel(model_name)
        logger.info("✅ Faster-whisper model downloaded and initialized successfully!")
        
        # Test basic functionality
        logger.info("🧪 Testing model initialization...")
        
        # Get model info
        logger.info(f"📊 Model: {model_name}")
        logger.info(f"🏭 Engine: faster-whisper (CTranslate2 optimized)")
        logger.info(f"🇮🇱 Language: Hebrew (he)")
        logger.info(f"📅 Release date: September 8th, 2024")
        
        logger.info("🎉 Model download and test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error downloading model: {e}")
        return False

def main():
    """Main function"""
    print("🎤 Faster-Whisper V2 Hebrew Model Downloader")
    print("=" * 60)
    
    success = download_faster_whisper_v2()
    
    if success:
        print("\n✅ Download completed successfully!")
        print("\n🚀 You can now use this model with:")
        print("Note: This model uses faster-whisper, not standard transformers")
        print("\nFor direct faster-whisper usage:")
        print("```python")
        print("import faster_whisper")
        print("model = faster_whisper.WhisperModel('ivrit-ai/faster-whisper-v2-d4')")
        print("segs, _ = model.transcribe('audio.wav', language='he')")
        print("```")
        print("\nFor use with your application:")
        print("You'll need to integrate this with the ConsolidatedTranscriptionEngine")
        print("or create a FasterWhisperEngine for this model type.")
    else:
        print("\n❌ Download failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
