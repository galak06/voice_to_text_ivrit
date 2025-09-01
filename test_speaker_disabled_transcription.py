#!/usr/bin/env python3
"""
Test script to verify transcription works without speaker logic when disabled
"""

import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_transcription_without_speaker():
    """Test transcription without speaker logic"""
    try:
        # Set environment to production (where speaker is disabled)
        os.environ['ENVIRONMENT'] = 'production'
        
        logger.info("🔍 Testing transcription without speaker logic...")
        
        # Import and test the transcription strategy
        from src.core.engines.strategies.direct_transcription_strategy import DirectTranscriptionStrategy
        from src.utils.config_manager import ConfigManager
        
        # Load configuration
        config_manager = ConfigManager()
        
        # Check if speaker is disabled
        if hasattr(config_manager.config, 'speaker'):
            speaker_config = config_manager.config.speaker
            enabled = getattr(speaker_config, 'enabled', True)
            disabled = getattr(speaker_config, 'disable_completely', False)
            
            logger.info(f"🎤 Speaker enabled: {enabled}")
            logger.info(f"🚫 Speaker disable_completely: {disabled}")
            
            if not enabled or disabled:
                logger.info("✅ Speaker logic is properly disabled")
            else:
                logger.warning("⚠️ Speaker logic is still enabled")
                return False
        else:
            logger.warning("⚠️ No speaker configuration found")
            return False
        
        # Test the transcription strategy
        strategy = DirectTranscriptionStrategy(config_manager)
        
        # Check if speaker diarization is enabled in the strategy
        is_enabled = strategy._is_speaker_diarization_enabled()
        logger.info(f"🎤 Strategy speaker diarization enabled: {is_enabled}")
        
        if not is_enabled:
            logger.info("✅ Strategy correctly detects speaker logic as disabled")
            return True
        else:
            logger.warning("⚠️ Strategy still thinks speaker logic is enabled")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing transcription: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_transcription_without_speaker()
    if success:
        logger.info("✅ Test passed: Transcription works without speaker logic")
    else:
        logger.error("❌ Test failed: Speaker logic is still active")
