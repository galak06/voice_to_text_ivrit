#!/usr/bin/env python3
"""
Chunk processing service for handling audio chunk transcription
Follows SOLID principles with dependency injection
"""

import logging
import os
import time
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from src.models.speaker_models import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class ChunkProcessor(ABC):
    """Abstract base class for chunk processors"""
    
    @abstractmethod
    def process_chunk(self, chunk_info: Dict[str, Any], model_name: str, 
                     engine, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """Process a single audio chunk"""
        pass


class AudioChunkProcessor(ChunkProcessor):
    """Processor for audio chunks with transcription"""
    
    def __init__(self, config_manager):
        """Initialize with ConfigManager dependency injection"""
        self.config_manager = config_manager
        self.output_directories = self._get_output_directories()
    
    def _get_output_directories(self) -> Dict[str, str]:
        """Get output directories from ConfigManager"""
        try:
            dir_paths = self.config_manager.get_directory_paths()
            return {
                'chunk_results': dir_paths.get('chunk_results_dir'),
                'audio_chunks': dir_paths.get('audio_chunks_dir')
            }
        except Exception as e:
            logger.error(f"❌ Error getting output directories: {e}")
            raise RuntimeError(f"Failed to get output directories: {e}")
    
    def process_chunk(self, chunk_info: Dict[str, Any], model_name: str, 
                     engine, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """Process a single audio chunk"""
        try:
            chunk_start = chunk_info['start']
            chunk_end = chunk_info['end']
            chunk_duration = chunk_end - chunk_start
            
            logger.info(f"🔧 Starting transcription for chunk {chunk_info['chunk_number']}")
            logger.info(f"   📍 Time range: {chunk_start:.1f}s - {chunk_end:.1f}s (duration: {chunk_duration:.1f}s)")
            
            # Update progress: processing started
            self._update_chunk_json_progress(
                chunk_info, 
                "processing", 
                "Starting transcription for this chunk",
                processing_started=time.time()
            )
            
            # Get the audio chunk file path
            # The chunk management service creates files with 'audio_chunk_' prefix
            # chunk_info['filename'] is 'chunk_001_0s_30s', but the actual file is 'audio_chunk_001_0s_30s.wav'
            chunk_number = chunk_info['chunk_number']
            start_time = int(chunk_info['start'])
            end_time = int(chunk_info['end'])
            audio_chunk_filename = f"audio_chunk_{chunk_number:03d}_{start_time}s_{end_time}s.wav"
            audio_chunk_path = os.path.join(self.output_directories['audio_chunks'], audio_chunk_filename)
            
            if not os.path.exists(audio_chunk_path):
                logger.error(f"❌ Audio chunk file not found: {audio_chunk_path}")
                self._update_chunk_json_progress(
                    chunk_info, 
                    "error", 
                    f"Audio chunk file not found: {audio_chunk_filename}",
                    error_message="Audio chunk file missing",
                    processing_completed=time.time()
                )
                return None
            
            # Transcribe the actual audio chunk using the engine directly
            logger.info(f"🎤 Transcribing audio chunk: {audio_chunk_filename}")
            
            # Load the audio chunk data for transcription
            audio_chunk_data, sample_rate, duration = self._load_audio(audio_chunk_path)
            
            chunk_result = engine._transcribe_chunk(
                audio_chunk_data,
                chunk_info['chunk_number'],
                chunk_start,
                chunk_end,
                model_name
            )
            
            if not chunk_result or not chunk_result.success:
                # Update progress: failed
                self._update_chunk_json_progress(
                    chunk_info, 
                    "failed", 
                    f"Transcription failed for chunk {chunk_info['filename']}",
                    error_message="Transcription engine returned failure",
                    processing_completed=time.time()
                )
                logger.warning(f"⚠️ Chunk transcription failed: {chunk_info['filename']}")
                return None
            
            # Update progress: transcription completed
            self._update_chunk_json_progress(
                chunk_info, 
                "transcribed", 
                "Transcription completed, processing segments",
                processing_completed=time.time()
            )
            
            # Create JSON result for this chunk
            self._create_chunk_json_result(chunk_info, chunk_result)
            
            # Process transcription result
            processed_segments = self._process_transcription_result(chunk_result, chunk_info, chunk_start)
            
            # Update progress: completed
            text_content = self._extract_text_content(chunk_result)
            self._update_chunk_json_progress(
                chunk_info, 
                "completed", 
                f"Chunk processing completed with {len(processed_segments)} segments",
                text=text_content,
                transcription_length=len(text_content),
                words_estimated=len(text_content.split()) if text_content else 0
            )
            
            return {
                'segments': processed_segments,
                'chunk_info': chunk_info
            }
            
        except Exception as e:
            # Update progress: error
            self._update_chunk_json_progress(
                chunk_info, 
                "error", 
                f"Error processing chunk: {str(e)}",
                error_message=str(e),
                processing_completed=time.time()
            )
            logger.error(f"❌ Error processing chunk: {e}")
            return None
    
    def _process_transcription_result(self, transcription_result: Any, chunk_info: Dict[str, Any], 
                                    chunk_start: float) -> List[Dict[str, Any]]:
        """Process transcription result and extract segments"""
        processed_segments = []
        
        if hasattr(transcription_result, 'full_text') and transcription_result.full_text:
            # The engine returns a TranscriptionResult object, so create a single segment
            processed_segment = {
                'text': transcription_result.full_text.strip(),
                'start': chunk_start,
                'end': chunk_info['end'],
                'confidence': getattr(transcription_result, 'confidence', 1.0),
                'chunk_file': chunk_info.get('filename', ''),
                'chunk_number': chunk_info.get('chunk_number', 0),
                'speaker_id': self._get_config_value('default_speaker_id', 'speaker_1')
            }
            processed_segments.append(processed_segment)
        elif hasattr(transcription_result, 'speakers') and transcription_result.speakers:
            # Handle case where result has speakers with segments
            for speaker_id, speaker_segments in transcription_result.speakers.items():
                for segment in speaker_segments:
                    processed_segment = self._process_segment(segment, chunk_start, chunk_info)
                    if processed_segment:
                        processed_segments.append(processed_segment)
        elif hasattr(transcription_result, 'segments') and transcription_result.segments:
            # Handle case where result has segments
            for segment in transcription_result.segments:
                processed_segment = self._process_segment(segment, chunk_start, chunk_info)
                if processed_segment:
                    processed_segments.append(processed_segment)
        
        return processed_segments
    
    def _process_segment(self, segment: Any, chunk_start: float, 
                        chunk_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single segment with proper speaker handling"""
        try:
            # Handle both dict and TranscriptionSegment objects
            if hasattr(segment, 'text'):
                # TranscriptionSegment object
                text = segment.text
                start = getattr(segment, 'start', 0)
                end = getattr(segment, 'end', 0)
                confidence = getattr(segment, 'confidence', 0.0)
                speaker = getattr(segment, 'speaker', 'unknown')
            else:
                # Dict object
                text = segment.get('text', '')
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                confidence = segment.get('confidence', 0.0)
                speaker = segment.get('speaker', 'unknown')
            
            # Extract basic segment data
            chunk_data = {
                'text': text,
                'start': start + chunk_start,
                'end': end + chunk_start,
                'confidence': confidence,
                'chunk_file': chunk_info.get('filename', ''),
                'chunk_number': chunk_info.get('chunk_number', 0),
                'speaker_id': speaker
            }
            
            return chunk_data
            
        except Exception as e:
            logger.error(f"❌ Error processing segment: {e}")
            return None
    
    def _extract_text_content(self, transcription_result: Any) -> str:
        """Extract text content from transcription result"""
        if hasattr(transcription_result, 'full_text') and transcription_result.full_text:
            return transcription_result.full_text.strip()
        elif hasattr(transcription_result, 'text'):
            return getattr(transcription_result, 'text', '')
        return ''
    
    def _load_audio(self, audio_file_path: str):
        """Load and validate audio file"""
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        try:
            import librosa
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None, mono=True)
            duration = len(audio_data) / sample_rate
            logger.info(f"✅ Audio loaded: {duration:.1f}s at {sample_rate}Hz")
            return audio_data, sample_rate, duration
        except ImportError:
            logger.error("❌ Librosa not available")
            raise ImportError("Librosa is required for audio processing")
        except Exception as e:
            logger.error(f"❌ Error loading audio: {e}")
            raise
    
    def _get_config_value(self, key: str, default_value):
        """Get configuration value from ConfigManager"""
        try:
            if hasattr(self.config_manager.config, 'chunking') and hasattr(self.config_manager.config.chunking, key):
                return getattr(self.config_manager.config.chunking, key)
            
            if hasattr(self.config_manager.config, 'processing') and hasattr(self.config_manager.config.processing, key):
                return getattr(self.config_manager.config.processing, key)
            
            if hasattr(self.config_manager.config, key):
                return getattr(self.config_manager.config, key)
            
            return default_value
            
        except Exception as e:
            logger.debug(f"Error getting config value for {key}: {e}")
            return default_value
    
    def _update_chunk_json_progress(self, chunk_info: Dict[str, Any], status: str, message: str, **kwargs) -> None:
        """Update JSON progress file for a chunk"""
        try:
            json_filename = f"{chunk_info['filename']}.json"
            json_path = os.path.join(self.output_directories['chunk_results'], json_filename)
            
            if os.path.exists(json_path):
                # Read existing JSON
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Update progress
                json_data['status'] = status
                json_data['progress'] = {
                    'stage': status,
                    'message': message,
                    'timestamp': time.time()
                }
                
                # Update additional fields
                for key, value in kwargs.items():
                    if key in json_data:
                        json_data[key] = value
                
                # Save updated JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"📝 Updated chunk progress: {json_filename} - {status}: {message}")
            
        except Exception as e:
            logger.error(f"❌ Error updating chunk JSON progress: {e}")
    
    def _create_chunk_json_result(self, chunk_info: Dict[str, Any], transcription_result: Any) -> None:
        """Create JSON result file for a chunk"""
        try:
            json_filename = f"{chunk_info['filename']}.json"
            json_path = os.path.join(self.output_directories['chunk_results'], json_filename)
            
            # Create JSON result data
            text_content = self._extract_text_content(transcription_result)
            transcription_length = len(text_content)
            words_estimated = len(text_content.split()) if text_content else 0
            
            json_data = {
                'chunk_number': chunk_info['chunk_number'],
                'start_time': chunk_info['start'],
                'end_time': chunk_info['end'],
                'status': 'completed',
                'created_at': time.time(),
                'text': text_content,
                'processing_started': None,
                'processing_completed': time.time(),
                'audio_chunk_metadata': chunk_info,
                'error_message': None,
                'enhancement_applied': False,
                'enhancement_strategy': self._get_config_value('default_enhancement_strategy', 'basic'),
                'transcription_length': transcription_length,
                'words_estimated': words_estimated,
                'chunk_metadata': chunk_info,
                'chunking_strategy': chunk_info.get('chunking_strategy', 'overlapping'),
                'overlap_start': chunk_info.get('overlap_start', 0),
                'overlap_end': chunk_info.get('overlap_end', 0),
                'stride_length': chunk_info.get('stride_length', 5)
            }
            
            # Save JSON result
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Saved chunk JSON result: {json_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error creating chunk JSON result: {e}")


class ChunkProcessingService:
    """Service for managing chunk processing operations"""
    
    def __init__(self, config_manager):
        """Initialize with ConfigManager dependency injection"""
        self.config_manager = config_manager
        self.chunk_processor = AudioChunkProcessor(config_manager)
    
    def process_chunks(self, chunks: List[Dict[str, Any]], model_name: str, 
                      engine, audio_file_path: str) -> List[Dict[str, Any]]:
        """Process multiple chunks and return results"""
        processed_chunks = []
        
        for chunk_info in chunks:
            result = self.chunk_processor.process_chunk(chunk_info, model_name, engine, audio_file_path)
            if result:
                processed_chunks.append(result)
        
        return processed_chunks
    
    def check_chunk_errors(self, chunk_info: Dict[str, Any]) -> bool:
        """Check if a chunk has errors in its JSON file"""
        try:
            json_filename = f"{chunk_info['filename']}.json"
            json_path = os.path.join(self.chunk_processor.output_directories['chunk_results'], json_filename)
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                # Check for error status or error messages
                if chunk_data.get('status') == 'error':
                    error_msg = chunk_data.get('error_message', 'Unknown error')
                    logger.error(f"❌ JSON check: Chunk {chunk_info['chunk_number']} has error status: {error_msg}")
                    return True
                
                if chunk_data.get('error_message'):
                    error_msg = chunk_data['error_message']
                    logger.error(f"❌ JSON check: Chunk {chunk_info['chunk_number']} has error message: {error_msg}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Could not check chunk JSON for errors: {e}")
            return False
