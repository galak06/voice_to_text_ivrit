#!/usr/bin/env python3
"""
Speaker Configuration Factory
Provides preset configurations for different use cases
"""

from typing import Optional
from src.core.speaker_transcription_service import SpeakerConfig

class SpeakerConfigFactory:
    """Factory for creating speaker configuration presets"""
    
    @staticmethod
    def get_config(preset: str = "default") -> SpeakerConfig:
        """
        Get speaker configuration for the specified preset
        
        Args:
            preset: Configuration preset name
            
        Returns:
            SpeakerConfig instance
        """
        if preset == "default":
            return SpeakerConfigFactory._get_default_config()
        elif preset == "conversation":
            return SpeakerConfigFactory._get_conversation_config()
        elif preset == "interview":
            return SpeakerConfigFactory._get_interview_config()
        elif preset == "custom":
            return SpeakerConfigFactory._get_custom_config()
        else:
            raise ValueError(f"Unknown preset: {preset}")
    
    @staticmethod
    def _get_default_config() -> SpeakerConfig:
        """Default balanced configuration"""
        return SpeakerConfig(
            min_speakers=2,
            max_speakers=4,
            silence_threshold=2.0,
            vad_enabled=True,
            word_timestamps=True,
            language="he",
            beam_size=5,
            vad_min_silence_duration_ms=500
        )
    
    @staticmethod
    def _get_conversation_config() -> SpeakerConfig:
        """Configuration optimized for conversations"""
        return SpeakerConfig(
            min_speakers=2,
            max_speakers=6,
            silence_threshold=1.0,  # Very sensitive to speaker changes
            vad_enabled=True,
            word_timestamps=True,
            language="he",
            beam_size=5,
            vad_min_silence_duration_ms=200
        )
    
    @staticmethod
    def _get_interview_config() -> SpeakerConfig:
        """Configuration optimized for interviews"""
        return SpeakerConfig(
            min_speakers=2,
            max_speakers=4,
            silence_threshold=2.5,  # Less sensitive, allows for thinking pauses
            vad_enabled=True,
            word_timestamps=True,
            language="he",
            beam_size=7,  # Higher accuracy for interviews
            vad_min_silence_duration_ms=800
        )
    
    @staticmethod
    def _get_custom_config() -> SpeakerConfig:
        """Custom configuration for specific needs"""
        return SpeakerConfig(
            min_speakers=1,
            max_speakers=3,
            silence_threshold=1.5,
            vad_enabled=True,
            word_timestamps=True,
            language="he",
            beam_size=3,  # Faster but less accurate
            vad_min_silence_duration_ms=300
        )
    
    @staticmethod
    def list_presets() -> list:
        """List available configuration presets"""
        return ["default", "conversation", "interview", "custom"]
    
    @staticmethod
    def describe_preset(preset: str) -> str:
        """Get description of a configuration preset"""
        descriptions = {
            "default": "Balanced configuration for most scenarios",
            "conversation": "Sensitive to quick speaker changes, good for casual conversations",
            "interview": "Allows for thinking pauses, optimized for formal interviews",
            "custom": "Fast processing with moderate accuracy"
        }
        return descriptions.get(preset, "Unknown preset")
    
    @staticmethod
    def print_preset_info(preset: str):
        """Print detailed information about a preset"""
        config = SpeakerConfigFactory.get_config(preset)
        description = SpeakerConfigFactory.describe_preset(preset)
        
        print(f"🔧 {preset.title()} Configuration:")
        print(f"   Description: {description}")
        print(f"   min_speakers: {config.min_speakers}")
        print(f"   max_speakers: {config.max_speakers}")
        print(f"   silence_threshold: {config.silence_threshold}s")
        print(f"   beam_size: {config.beam_size}")
        print(f"   vad_min_silence_duration_ms: {config.vad_min_silence_duration_ms}")
        print()
    
    @staticmethod
    def print_all_presets():
        """Print information about all available presets"""
        print("📋 Available Speaker Configuration Presets:")
        print("=" * 50)
        
        for preset in SpeakerConfigFactory.list_presets():
            SpeakerConfigFactory.print_preset_info(preset) 