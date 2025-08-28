#!/usr/bin/env python3
"""
Transcription script with speaker diarization for ivrit-ai models
Separates different speakers in the conversation
"""

from pathlib import Path
from src.core.orchestrator.transcription_service import TranscriptionService
from src.core.factories.speaker_config_factory import SpeakerConfigFactory
from src.utils.config_manager import ConfigManager
from src.output_data import OutputManager

def speaker_diarization(audio_file_path: str, model_name: str = None, save_output: bool = True, speaker_config_preset: str = "default", run_session_id: str = None, engine_type: str = None):
    """
    Transcribe an audio file with speaker diarization
    
    Args:
        audio_file_path (str): Path to the audio file
        model_name (str): Model to use for transcription
        save_output (bool): Whether to save outputs in all formats
        speaker_config_preset (str): Speaker configuration preset (default, conversation, interview, custom)
    """
    
    # Create config manager and output manager
    config_manager = ConfigManager()
    output_manager = OutputManager(config_manager)
    
    # Create unified transcription service
    service = TranscriptionService(config_manager, output_manager)
    
    # Prepare input data
    input_data = {
        'file_path': audio_file_path,
        'speaker_diarization': True,
        'speaker_preset': speaker_config_preset,
        'model': model_name,
        'save_output': save_output,
        'session_id': run_session_id,
        'engine': engine_type
    }
    
    # Perform transcription with speaker diarization
    result = service.transcribe(input_data)
    
    return result.get('success', False)

 