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
        """Default configuration optimized for 2-speaker conversations"""
        return SpeakerConfig(
            min_speakers=2,
            max_speakers=2,
            silence_threshold=1.5,
            vad_enabled=True,
            word_timestamps=True,
            language="he",
            beam_size=5,
            vad_min_silence_duration_ms=300
        )
    
    @staticmethod
    def _get_conversation_config() -> SpeakerConfig:
        """Configuration optimized for 2-speaker conversations"""
        return SpeakerConfig(
            min_speakers=2,
            max_speakers=2,
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
            "default": "Optimized for 2-speaker conversations",
            "conversation": "Sensitive to quick speaker changes, optimized for 2-speaker conversations",
            "interview": "Allows for thinking pauses, optimized for formal interviews",
            "custom": "Fast processing with moderate accuracy"
        }
        return descriptions.get(preset, "Unknown preset")
    
    @staticmethod
    def print_preset_info(preset: str):
        """Print detailed information about a preset"""
        config = SpeakerConfigFactory.get_config(preset)
        description = SpeakerConfigFactory.describe_preset(preset)
        
        # Return formatted string instead of printing
        info = f"{preset.title()} Configuration:\n"
        info += f"   Description: {description}\n"
        info += f"   min_speakers: {config.min_speakers}\n"
        info += f"   max_speakers: {config.max_speakers}\n"
        info += f"   silence_threshold: {config.silence_threshold}s\n"
        info += f"   beam_size: {config.beam_size}\n"
        info += f"   vad_min_silence_duration_ms: {config.vad_min_silence_duration_ms}\n"
        return info
    
    @staticmethod
    def get_all_presets_info():
        """Get information about all available presets"""
        info = "Available Speaker Configuration Presets:\n"
        info += "=" * 50 + "\n"
        
        for preset in SpeakerConfigFactory.list_presets():
            info += SpeakerConfigFactory.print_preset_info(preset) + "\n"
        return info 