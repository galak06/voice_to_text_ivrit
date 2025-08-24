#!/usr/bin/env python3
"""
Transcription script with speaker diarization for ivrit-ai models
Separates different speakers in the conversation
"""

from pathlib import Path
from src.core.orchestrator.speaker_transcription_service import SpeakerTranscriptionService
from src.core.factories.speaker_config_factory import SpeakerConfigFactory

def speaker_diarization(audio_file_path: str, model_name: str = None, save_output: bool = True, speaker_config_preset: str = "default", run_session_id: str = None, engine_type: str = None):
    """
    Transcribe an audio file with speaker diarization
    
    Args:
        audio_file_path (str): Path to the audio file
        model_name (str): Model to use for transcription
        save_output (bool): Whether to save outputs in all formats
        speaker_config_preset (str): Speaker configuration preset (default, conversation, interview, custom)
    """
    
    # Get configuration from factory
    config = SpeakerConfigFactory.get_config(speaker_config_preset)
    
    # Create speaker transcription service with specified configuration
    service = SpeakerTranscriptionService(config)
    
    # Perform transcription
    result = service.speaker_diarization(audio_file_path, model_name, save_output, run_session_id, engine_type)
    
    # Display results
    service.display_results(result)
    
    return result.success

 