#!/usr/bin/env python3
"""
Speaker Configuration Factory
Provides predefined speaker diarization configurations
"""

import logging
from typing import Dict, Any
from ..models.speaker_models import SpeakerConfig

logger = logging.getLogger(__name__)


class SpeakerConfigFactory:
    """Factory for creating speaker diarization configurations"""
    
    @staticmethod
    def get_config(preset: str = "conversation") -> SpeakerConfig:
        """
        Get speaker configuration based on preset
        
        Args:
            preset: Configuration preset name (defaults to "conversation")
            
        Returns:
            SpeakerConfig instance
        """
        configs = {
            "default": SpeakerConfig(),
            
            "conversation": SpeakerConfig(
                min_speakers=2,
                max_speakers=4,
                silence_threshold=1.5,
                vad_enabled=True,
                word_timestamps=True,
                language="he",
                beam_size=5,
                vad_min_silence_duration_ms=300
            ),
            
            "interview": SpeakerConfig(
                min_speakers=2,
                max_speakers=3,
                silence_threshold=2.5,
                vad_enabled=True,
                word_timestamps=True,
                language="he",
                beam_size=5,
                vad_min_silence_duration_ms=500
            ),
            
            "meeting": SpeakerConfig(
                min_speakers=3,
                max_speakers=8,
                silence_threshold=1.0,
                vad_enabled=True,
                word_timestamps=False,
                language="he",
                beam_size=3,
                vad_min_silence_duration_ms=200
            ),
            
            "podcast": SpeakerConfig(
                min_speakers=2,
                max_speakers=6,
                silence_threshold=2.0,
                vad_enabled=True,
                word_timestamps=True,
                language="he",
                beam_size=5,
                vad_min_silence_duration_ms=400
            ),
            
            "lecture": SpeakerConfig(
                min_speakers=1,
                max_speakers=3,
                silence_threshold=3.0,
                vad_enabled=True,
                word_timestamps=True,
                language="he",
                beam_size=5,
                vad_min_silence_duration_ms=800
            )
        }
        
        if preset not in configs:
            logger.warning(f"Unknown preset '{preset}', using default configuration")
            return configs["default"]
        
        return configs[preset]
    
    @staticmethod
    def get_available_presets() -> list:
        """Get list of available configuration presets"""
        return ["conversation", "default", "interview", "meeting", "podcast", "lecture"]
    
    @staticmethod
    def create_custom_config(**kwargs) -> SpeakerConfig:
        """
        Create a custom speaker configuration
        
        Args:
            **kwargs: Configuration parameters
            
        Returns:
            SpeakerConfig instance
        """
        return SpeakerConfig(**kwargs) 