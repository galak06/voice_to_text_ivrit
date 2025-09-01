#!/usr/bin/env python3
"""
Test script to verify speaker logic is disabled
"""

import logging
from src.utils.config_manager import ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_speaker_config():
    """Test if speaker configuration is properly disabled"""
    logger.info("🔍 Testing speaker configuration...")
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        
        # Check speaker configuration
        if hasattr(config_manager.config, 'speaker'):
            speaker_config = config_manager.config.speaker
            logger.info(f"📋 Speaker config found: {speaker_config}")
            
            if hasattr(speaker_config, 'enabled'):
                enabled = speaker_config.enabled
                logger.info(f"🎤 Speaker enabled: {enabled}")
            else:
                logger.info("🎤 Speaker enabled field not found")
                
            if hasattr(speaker_config, 'disable_completely'):
                disabled = speaker_config.disable_completely
                logger.info(f"🚫 Speaker disable_completely: {disabled}")
            else:
                logger.info("🚫 Speaker disable_completely field not found")
        else:
            logger.info("📋 No speaker config section found")
        
        # Check speaker_diarization configuration
        if hasattr(config_manager.config, 'speaker_diarization'):
            speaker_diarization_config = config_manager.config.speaker_diarization
            logger.info(f"📋 Speaker diarization config found: {speaker_diarization_config}")
            
            if hasattr(speaker_diarization_config, 'enabled'):
                enabled = speaker_diarization_config.enabled
                logger.info(f"🎤 Speaker diarization enabled: {enabled}")
            else:
                logger.info("🎤 Speaker diarization enabled field not found")
        else:
            logger.info("📋 No speaker_diarization config section found")
        
        # Check chunking configuration
        if hasattr(config_manager.config, 'chunking'):
            chunking_config = config_manager.config.chunking
            logger.info(f"📋 Chunking config found: {chunking_config}")
            
            if hasattr(chunking_config, 'default_enhancement_strategy'):
                strategy = chunking_config.default_enhancement_strategy
                logger.info(f"🎯 Default enhancement strategy: {strategy}")
            else:
                logger.info("🎯 Default enhancement strategy field not found")
        else:
            logger.info("📋 No chunking config section found")
            
        logger.info("✅ Configuration test completed")
        
    except Exception as e:
        logger.error(f"❌ Error testing configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_speaker_config()
