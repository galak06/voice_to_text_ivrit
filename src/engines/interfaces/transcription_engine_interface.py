"""
Transcription Engine Interface
Defines the contract for transcription engines
"""

from typing import Protocol, Any


class TranscriptionEngineInterface(Protocol):
    """Protocol defining the interface for transcription engines"""
    
    def transcribe(self, audio_file: str, language: str = 'he', word_timestamps: bool = True) -> Any:
        """
        Transcribe audio file and return segments
        
        Args:
            audio_file: Path to the audio file to transcribe
            language: Language code for transcription
            word_timestamps: Whether to include word-level timestamps
            
        Returns:
            Transcription result with segments
        """
        ... 