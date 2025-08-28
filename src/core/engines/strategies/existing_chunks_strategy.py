#!/usr/bin/env python3
"""
Existing Chunks Strategy
Handles transcription of pre-existing audio chunks
"""

import logging
import time
import os
import glob
from typing import TYPE_CHECKING

from src.core.engines.strategies.base_strategy import BaseTranscriptionStrategy
from src.models.speaker_models import TranscriptionResult, TranscriptionSegment

if TYPE_CHECKING:
    from src.core.engines.base_interface import TranscriptionEngine

logger = logging.getLogger(__name__)


class ExistingChunksStrategy(BaseTranscriptionStrategy):
    """Strategy for processing existing audio chunks"""
    
    def __init__(self, config_manager):
        """Initialize the strategy with ConfigManager dependency injection"""
        super().__init__(config_manager)
    
    def execute(self, audio_file_path: str, model_name: str, engine: 'TranscriptionEngine') -> TranscriptionResult:
        """Execute existing chunks strategy"""
        logger.info(f"🎯 Using ExistingChunksStrategy for: {audio_file_path}")
        
        chunks_dir = "examples/audio/voice/audio_chunks/"
        if not os.path.exists(chunks_dir):
            return self._fallback_to_chunked(audio_file_path, model_name, engine)
        
        chunk_files = glob.glob(os.path.join(chunks_dir, "audio_chunk_*.wav"))
        if not chunk_files:
            return self._fallback_to_chunked(audio_file_path, model_name, engine)
        
        chunk_files.sort()
        logger.info(f"🎯 Found {len(chunk_files)} existing audio chunks, processing them directly")
        
        all_segments, total_duration = self._process_existing_chunks(chunk_files, engine, model_name)
        
        if not all_segments:
            from src.models.speaker_models import TranscriptionResult
            return TranscriptionResult(
                success=False, speakers={}, full_text="", transcription_time=0.0,
                model_name=model_name, audio_file=audio_file_path, speaker_count=0,
                error_message="No segments were processed successfully"
            )
        
        return self._create_final_result(all_segments, total_duration, model_name, audio_file_path, len(chunk_files))
    
    def _fallback_to_chunked(self, audio_file_path: str, model_name: str, engine):
        """Fallback to chunked transcription strategy"""
        logger.warning(f"⚠️ Audio chunks directory not found or empty, falling back to chunked transcription")
        from .chunked_transcription_strategy import ChunkedTranscriptionStrategy
        fallback_strategy = ChunkedTranscriptionStrategy(self.config, self.app_config, self.config_manager)
        return fallback_strategy.execute(audio_file_path, model_name, engine)
    
    def _process_existing_chunks(self, chunk_files, engine, model_name: str):
        """Process existing audio chunks"""
        all_segments = []
        total_duration = 0.0
        start_time = time.time()
        
        for i, chunk_file in enumerate(chunk_files, 1):
            segment, chunk_duration = self._process_single_existing_chunk(chunk_file, i, total_duration, engine, model_name)
            if segment:
                all_segments.append(segment)
                total_duration += chunk_duration
        
        logger.info(f"🎯 Processing completed: {time.time() - start_time:.1f}s, {len(all_segments)} segments")
        return all_segments, total_duration
    
    def _process_single_existing_chunk(self, chunk_file: str, chunk_num: int, current_duration: float, engine, model_name: str):
        """Process a single existing chunk"""
        chunk_name = os.path.basename(chunk_file)
        logger.info(f"🔧 Processing existing chunk {chunk_num}: {chunk_name}")
        
        try:
            audio, sr = self._load_chunk_audio(chunk_file)
            chunk_duration = len(audio) / sr
            chunk_start = current_duration
            chunk_end = current_duration + chunk_duration
            
            return self._transcribe_chunk_and_create_segment(audio, chunk_num, chunk_start, chunk_end, chunk_duration, engine, model_name)
                
        except Exception as e:
            logger.error(f"❌ Error processing chunk {chunk_num} ({chunk_name}): {e}")
            return None, 0.0
    
    def _transcribe_chunk_and_create_segment(self, audio, chunk_num: int, chunk_start: float, chunk_end: float, chunk_duration: float, engine, model_name: str):
        """Transcribe chunk and create segment"""
        chunk_text = engine._transcribe_chunk(audio, chunk_num, chunk_start, chunk_end, model_name)
        
        if chunk_text and chunk_text.strip():
            segment = TranscriptionSegment(start=chunk_start, end=chunk_end, text=chunk_text.strip(), speaker="0")
            logger.info(f"✅ Chunk {chunk_num} completed")
            return segment, chunk_duration
        else:
            logger.warning(f"⚠️ Chunk {chunk_num} returned no text")
            return None, 0.0
    
    def _load_chunk_audio(self, chunk_file: str):
        """Load audio from chunk file"""
        import librosa
        return librosa.load(chunk_file, sr=16000)
    
    def _create_final_result(self, all_segments, total_duration: float, model_name: str, audio_file_path: str, chunk_count: int):
        """Create final transcription result"""
        speakers_dict = {"0": all_segments}
        final_result = TranscriptionResult(
            success=True, speakers=speakers_dict, full_text=" ".join([seg.text for seg in all_segments]),
            transcription_time=0.0, model_name=model_name, audio_file=audio_file_path, speaker_count=len(speakers_dict)
        )
        
        logger.info(f"🎉 Successfully processed {chunk_count} existing chunks")
        logger.info(f"📊 Total segments: {len(all_segments)}")
        logger.info(f"⏱️ Total duration: {total_duration:.1f}s")
        logger.info(f"🗣️ Speakers detected: {len(speakers_dict)}")
        
        return final_result
    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return "ExistingChunksStrategy"
