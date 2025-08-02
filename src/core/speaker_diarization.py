#!/usr/bin/env python3
"""
Transcription script with speaker diarization for ivrit-ai models
Separates different speakers in the conversation
"""

import sys
from pathlib import Path
from src.core.speaker_transcription_service import SpeakerTranscriptionService
from src.core.speaker_config_factory import SpeakerConfigFactory

def speaker_diarization(audio_file_path: str, model_name: str = None, save_output: bool = True, speaker_config_preset: str = "default", run_session_id: str = None):
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
    result = service.speaker_diarization(audio_file_path, model_name, save_output, run_session_id)
    
    # Display results
    service.display_results(result)
    
    return result.success

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python speaker_diarization.py <audio_file_path> [model]")
        print("Example: python speaker_diarization.py voice/rachel_1.wav")
        print("Example: python speaker_diarization.py voice/rachel_1.wav ivrit-ai/whisper-large-v3-ct2")
        print()
        print("Available models:")
        print("  - ivrit-ai/whisper-large-v3-turbo-ct2 (fast, recommended)")
        print("  - ivrit-ai/whisper-large-v3-ct2 (high accuracy)")
        print()
        print("Note: For best speaker diarization, install stable-whisper:")
        print("  pip install stable-whisper")
        return
    
    audio_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("🎤 ivrit-ai Speaker-Separated Audio Transcription")
    print("=" * 50)
    
    success = speaker_diarization(audio_file, model, save_output=True)
    
    if success:
        print("✅ Speaker-separated transcription completed successfully!")
    else:
        print("❌ Speaker-separated transcription failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 