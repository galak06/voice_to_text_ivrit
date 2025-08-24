#!/usr/bin/env python3
"""
Direct Transcription Strategy
Handles transcription of small files without chunking
"""

import logging
import time
from typing import TYPE_CHECKING

from src.core.engines.strategies.base_strategy import BaseTranscriptionStrategy
from src.models.speaker_models import TranscriptionResult, TranscriptionSegment

if TYPE_CHECKING:
    from src.core.engines.base_interface import TranscriptionEngine

logger = logging.getLogger(__name__)


class DirectTranscriptionStrategy(BaseTranscriptionStrategy):
    """Strategy for direct transcription of small files"""
    
    def execute(self, audio_file_path: str, model_name: str, engine: 'TranscriptionEngine') -> TranscriptionResult:
        """Execute direct transcription strategy"""
        logger.info(f"🎯 Using DirectTranscriptionStrategy for: {audio_file_path}")
        
        try:
            audio_data, sample_rate = self._load_audio(audio_file_path)
            chunk_text = self._transcribe_audio(audio_data, sample_rate, engine, model_name)
            
            if chunk_text and chunk_text.strip():
                return self._create_result(audio_data, sample_rate, chunk_text, model_name, audio_file_path)
            else:
                raise ValueError("No transcription text produced")
                
        except Exception as e:
            logger.error(f"❌ Error in direct transcription: {e}")
            raise
    
    def _load_audio(self, audio_file_path: str):
        """Load audio file"""
        import librosa
        return librosa.load(audio_file_path, sr=16000, mono=True)
    
    def _transcribe_audio(self, audio_data, sample_rate, engine, model_name: str) -> str:
        """Transcribe audio data"""
        start_time = time.time()
        return engine._transcribe_chunk(audio_data, 1, 0, len(audio_data) / sample_rate, model_name)
    
    def _create_result(self, audio_data, sample_rate, chunk_text: str, model_name: str, audio_file_path: str) -> TranscriptionResult:
        """Create transcription result"""
        segment = TranscriptionSegment(start=0, end=len(audio_data) / sample_rate, text=chunk_text, speaker="0")
        
        return TranscriptionResult(
            success=True, speakers={"0": [segment]}, full_text=chunk_text,
            transcription_time=0.0, model_name=model_name, audio_file=audio_file_path, speaker_count=1
        )
    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return "DirectTranscriptionStrategy"
