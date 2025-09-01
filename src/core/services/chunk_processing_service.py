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

from src.models.transcription_results import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class ChunkProcessor(ABC):
    """Abstract base class for chunk processors"""
    
    @abstractmethod
    def process_chunk(self, chunk_info: Dict[str, Any], model_name: str, 
                     engine, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """Process a single audio chunk"""
        pass


class AudioChunkProcessor(ChunkProcessor):
    """Processor for audio chunks with transcription and optional speaker diarization"""
    
    def __init__(self, config_manager):
        """Initialize with ConfigManager dependency injection"""
        self.config_manager = config_manager
        self.output_directories = self._get_output_directories()
        self._speaker_service = None
        
        # Create output manager for speaker service
        try:
            from src.output_data.managers.output_manager import OutputManager
            from src.output_data.utils.data_utils import DataUtils
            from src.output_data.formatters.text_formatter import TextFormatter
            
            # Create minimal dependencies for output manager
            data_utils = DataUtils()
            output_strategy = TextFormatter()  # Simple text formatter as fallback
            
            self.output_manager = OutputManager(
                output_base_path=self.output_directories.get('chunk_results', 'output/chunk_results'),
                data_utils=data_utils,
                output_strategy=output_strategy
            )
            logger.info("✅ Output manager created for speaker service")
        except Exception as e:
            logger.warning(f"⚠️ Could not create output manager: {e}")
            self.output_manager = None
        
        # Initialize speaker service if enabled
        self._initialize_speaker_service()
    
    def _initialize_speaker_service(self):
        """Initialize speaker service - fail fast if initialization fails"""
        try:
            if not self._is_speaker_diarization_enabled():
                logger.info("ℹ️ Speaker diarization disabled in configuration")
                return
            
            logger.info("🎤 Initializing speaker service...")
            
            # Create OutputManager for speaker service
            from src.core.factories.speaker_service_factory import SpeakerServiceFactory
            from src.output_data.managers.output_manager import OutputManager
            from src.output_data.utils.data_utils import DataUtils
            from src.output_data.formatters.text_formatter import TextFormatter
            
            data_utils = DataUtils()
            text_formatter = TextFormatter()
            output_manager = OutputManager(
                output_base_path="output",
                data_utils=data_utils,
                output_strategy=text_formatter
            )
            
            # Create speaker service through factory
            self._speaker_service = SpeakerServiceFactory.create_service(
                self.config_manager,
                output_manager=output_manager
            )
            
            if not self._speaker_service:
                raise RuntimeError("Speaker service factory returned None")
            
            logger.info(f"🎤 Speaker service initialized: {type(self._speaker_service).__name__}")
            
        except Exception as e:
            logger.error(f"❌ Speaker service initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize speaker service: {e}")
    
    def _is_speaker_diarization_enabled(self) -> bool:
        """Check if speaker diarization is enabled from config"""
        try:
            # Direct access to config value
            if hasattr(self.config_manager.config, 'speaker_diarization'):
                return getattr(self.config_manager.config.speaker_diarization, 'enabled', True)
            return True  # Default to enabled if no config section
        except Exception as e:
            logger.warning(f"⚠️ Error checking speaker diarization config: {e}")
            return True  # Default to enabled on error
    
    def _is_speaker_service_working(self) -> bool:
        """Check if the speaker service is actually working and functional"""
        try:
            if not self._speaker_service:
                return False
            
            # Check if the service has the required methods
            if not hasattr(self._speaker_service, 'speaker_diarization'):
                logger.warning("⚠️ Speaker service missing required method: speaker_diarization")
                return False
            
            # Check if the service can be called (basic validation)
            if not callable(getattr(self._speaker_service, 'speaker_diarization', None)):
                logger.warning("⚠️ Speaker service method is not callable")
                return False
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ Error checking speaker service functionality: {e}")
            return False
    
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
        """Process a single audio chunk with optional speaker recognition"""
        try:
            chunk_start = chunk_info['start']
            chunk_end = chunk_info['end']
            chunk_duration = chunk_end - chunk_start
            
            logger.info(f"🔧 Starting transcription for chunk {chunk_info['chunk_number']}")
            logger.info(f"   Time range: {chunk_start:.1f}s - {chunk_end:.1f}s (duration: {chunk_duration:.1f}s)")
            
            # Update progress: processing started
            self._update_chunk_json_progress(
                chunk_info, 
                "processing", 
                "Starting transcription for this chunk",
                processing_started=time.time()
            )
            
            # Get the audio chunk file path
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
            logger.info(f" Transcribing audio chunk: {audio_chunk_filename}")
            
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
                "Transcription completed, processing speaker recognition" if self._speaker_service else "Transcription completed, processing segments",
                processing_completed=time.time()
            )
            
            # Enhanced processing with speaker recognition if enabled
            logger.info(f"🔍 Speaker service check: _speaker_service={self._speaker_service is not None}, working={self._is_speaker_service_working()}")
            
            if self._speaker_service and self._is_speaker_service_working():
                logger.info("🎤 Attempting enhanced processing with speaker recognition")
                try:
                    enhanced_result = self._enhance_chunk_with_speakers(chunk_info, chunk_result, audio_chunk_path)
                    logger.info("✅ Speaker enhancement successful, creating enhanced JSON")
                    # Create enhanced JSON result for this chunk
                    self._create_enhanced_chunk_json_result(chunk_info, enhanced_result)
                    # Process transcription result
                    processed_segments = self._process_transcription_result(enhanced_result, chunk_info, chunk_start)
                    # Update progress: completed
                    text_content = self._extract_text_content(enhanced_result)
                    self._update_chunk_json_progress(
                        chunk_info, 
                        "completed", 
                        f"Chunk processing completed with {len(processed_segments)} segments and speaker recognition",
                        text=text_content,
                        transcription_length=len(text_content),
                        words_estimated=len(text_content.split()) if text_content else 0
                    )
                    
                    return {
                        'segments': processed_segments,
                        'chunk_info': chunk_info,
                        'enhanced_data': enhanced_result
                    }
                except Exception as e:
                    logger.warning(f"⚠️ Speaker recognition failed, falling back to basic processing: {e}")
                    logger.error(f"❌ Full error details: {e}", exc_info=True)
                    # Fall back to basic processing if speaker recognition fails
                    self._speaker_service = None
            else:
                logger.info(f"ℹ️ Speaker service not available or not working, using basic processing")
            
            # Create enhanced JSON result for this chunk
            self._create_enhanced_chunk_json_result(chunk_info, enhanced_result)
            
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
    
    def _enhance_chunk_with_speakers(self, chunk_info: Dict[str, Any], 
                                   transcription_result: Any, 
                                   audio_chunk_path: str) -> Dict[str, Any]:
        """Enhance chunk with speaker recognition using existing speaker service and models"""
        try:
            # Extract text content for speaker analysis
            text_content = self._extract_text_content(transcription_result)
            
            # Use existing speaker service to analyze speakers
            speaker_result = self._speaker_service.speaker_diarization(audio_chunk_path)
            
            # Create enhanced result structure using existing Pydantic models
            enhanced_result = {
                'chunk_info': {
                    'chunk_id': chunk_info['filename'],
                    'start_time': chunk_info['start'],
                    'end_time': chunk_info['end'],
                    'duration': chunk_info['end'] - chunk_info['start'],
                    'chunk_number': chunk_info['chunk_number'],
                    'chunking_strategy': chunk_info.get('chunking_strategy', 'overlapping'),
                    'overlap_info': {
                        'overlap_start': chunk_info.get('overlap_start', 0),
                        'overlap_end': chunk_info.get('overlap_end', 0),
                        'stride_length': chunk_info.get('stride_length', 5)
                    }
                },
                'transcription': {
                    'text': text_content,
                    'segments': self._extract_segments(transcription_result),
                    'language': 'he',  # Default for Hebrew
                    'confidence': getattr(transcription_result, 'confidence', 0.95),
                    'processing_status': 'completed'
                },
                'speaker_recognition': self._extract_speaker_recognition(speaker_result),
                'processing_type': 'enhanced_with_speakers'
            }
            
            return enhanced_result
                
        except Exception as e:
            logger.warning(f"⚠️ Speaker enhancement failed: {e}, falling back to basic")
            return self._create_basic_enhanced_result(chunk_info, transcription_result)
    
    def _extract_speaker_recognition(self, speaker_result: TranscriptionResult) -> Dict[str, Any]:
        """Extract speaker recognition data from existing TranscriptionResult Pydantic model"""
        try:
            if not speaker_result.success:
                return self._get_fallback_speaker_info()
            
            # Extract speaker information from the existing Pydantic model
            speakers = speaker_result.speakers
            speaker_count = speaker_result.speaker_count
            
            if not speakers:
                return self._get_fallback_speaker_info()
            
            # Get primary speaker (first speaker with segments)
            primary_speaker = None
            primary_confidence = 0.0
            secondary_speakers = []
            
            for speaker_name, segments in speakers.items():
                if segments and not primary_speaker:
                    primary_speaker = speaker_name
                    # Calculate average confidence from segments
                    confidences = [seg.confidence for seg in segments if seg.confidence is not None]
                    primary_confidence = sum(confidences) / len(confidences) if confidences else 0.8
                elif segments:
                    secondary_speakers.append(speaker_name)
            
            return {
                'primary_speaker': primary_speaker or 'UNKNOWN',
                'primary_confidence': primary_confidence,
                'secondary_speakers': secondary_speakers,
                'overlap_resolution': 'multiple_speakers_detected' if len(speakers) > 1 else 'single_speaker',
                'has_multiple_speakers': len(speakers) > 1,
                'speaker_mapping_id': f"chunk_{hash(str(speakers)) % 10000}",
                'total_speakers': speaker_count,
                'speaker_names': list(speakers.keys())
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting speaker recognition: {e}")
            return self._get_fallback_speaker_info()
    
    def _get_fallback_speaker_info(self) -> Dict[str, Any]:
        """Get fallback speaker information when analysis fails"""
        return {
            'primary_speaker': 'UNKNOWN',
            'primary_confidence': 0.0,
            'secondary_speakers': [],
            'overlap_resolution': 'analysis_failed',
            'has_multiple_speakers': False,
            'speaker_mapping_id': None,
            'total_speakers': 0,
            'speaker_names': []
        }
    
    def _create_basic_enhanced_result(self, chunk_info: Dict[str, Any], 
                                    transcription_result: Any) -> Dict[str, Any]:
        """Create basic enhanced result when enhanced processing is not available"""
        return {
            'chunk_info': {
                'chunk_id': chunk_info['filename'],
                'start_time': chunk_info['start'],
                'end_time': chunk_info['end'],
                'duration': chunk_info['end'] - chunk_info['start'],
                'chunk_number': chunk_info['chunk_number'],
                'chunking_strategy': chunk_info.get('chunking_strategy', 'overlapping'),
                'overlap_info': {
                    'overlap_start': chunk_info.get('overlap_start', 0),
                    'overlap_end': chunk_info.get('overlap_end', 0),
                    'stride_length': chunk_info.get('stride_length', 5)
                }
            },
            'transcription': {
                'text': self._extract_text_content(transcription_result),
                'segments': self._extract_segments(transcription_result),
                'language': 'he',
                'confidence': getattr(transcription_result, 'confidence', 0.95),
                'processing_status': 'completed'
            },
            'speaker_recognition': self._get_fallback_speaker_info(),
            'processing_type': 'basic_without_speakers'
        }
    
    def _extract_segments(self, transcription_result: Any) -> List[Dict[str, Any]]:
        """Extract segments from transcription result using existing TranscriptionSegment model"""
        segments = []
        
        if hasattr(transcription_result, 'segments') and transcription_result.segments:
            for segment in transcription_result.segments:
                if hasattr(segment, 'text'):
                    segments.append({
                        'text': segment.text,
                        'start': getattr(segment, 'start', 0),
                        'end': getattr(segment, 'end', 0),
                        'confidence': getattr(segment, 'confidence', 0.0),
                        'speaker': getattr(segment, 'speaker', 'unknown')
                    })
        
        return segments
    
    def _process_transcription_result(self, transcription_result: Any, chunk_info: Dict[str, Any], 
                                    chunk_start: float) -> List[Dict[str, Any]]:
        """Process transcription result and extract segments using existing models"""
        processed_segments = []
        
        # Handle enhanced result structure
        if isinstance(transcription_result, dict) and 'transcription' in transcription_result:
            transcription_data = transcription_result['transcription']
            if 'segments' in transcription_data:
                for segment in transcription_data['segments']:
                    processed_segment = self._process_segment(segment, chunk_start, chunk_info)
                    if processed_segment:
                        processed_segments.append(processed_segment)
            elif 'text' in transcription_data:
                # Single text segment
                processed_segment = {
                    'text': transcription_data['text'],
                    'start': chunk_start,
                    'end': chunk_info['end'],
                    'confidence': transcription_data.get('confidence', 1.0),
                    'chunk_file': chunk_info.get('filename', ''),
                    'chunk_number': chunk_info.get('chunk_number', 0),
                    'speaker_id': transcription_result.get('speaker_recognition', {}).get('primary_speaker', 'unknown')
                }
                processed_segments.append(processed_segment)
        
        # Fallback to original processing if enhanced structure not found
        elif hasattr(transcription_result, 'text') and transcription_result.text:
            processed_segment = {
                'text': transcription_result.text.strip(),
                'start': chunk_start,
                'end': chunk_info['end'],
                'confidence': getattr(transcription_result, 'confidence', 1.0),
                'chunk_file': chunk_info.get('filename', ''),
                'chunk_number': chunk_info.get('chunk_number', 0),
                'speaker_id': self._get_config_value('default_speaker_id', 'speaker_1')
            }
            processed_segments.append(processed_segment)
        elif hasattr(transcription_result, 'speakers') and transcription_result.speakers:
            # Handle case where result has speakers with segments using existing TranscriptionSegment model
            for speaker_id, speaker_segments in transcription_result.speakers.items():
                for segment in speaker_segments:
                    processed_segment = self._process_segment(segment, chunk_start, chunk_info)
                    if processed_segment:
                        processed_segments.append(processed_segment)
        elif hasattr(transcription_result, 'segments') and transcription_result.segments:
            # Handle case where result has segments using existing TranscriptionSegment model
            for segment in transcription_result.segments:
                processed_segment = self._process_segment(segment, chunk_start, chunk_info)
                if processed_segment:
                    processed_segments.append(processed_segment)
        
        return processed_segments
    
    def _process_segment(self, segment: Any, chunk_start: float, 
                        chunk_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single segment using existing TranscriptionSegment model"""
        try:
            # Handle both dict and TranscriptionSegment objects
            if hasattr(segment, 'text'):
                # TranscriptionSegment object - use existing model
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
        # Handle enhanced result structure
        if isinstance(transcription_result, dict) and 'transcription' in transcription_result:
            return transcription_result['transcription'].get('text', '')
        
        # Handle original structure
        if hasattr(transcription_result, 'text') and transcription_result.text:
            return transcription_result.text.strip()
        elif hasattr(transcription_result, 'full_text'):
            return getattr(transcription_result, 'full_text', '')
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
        """Create basic JSON result file for a chunk without speaker recognition"""
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
    
    def _create_enhanced_chunk_json_result(self, chunk_info: Dict[str, Any], enhanced_result: Dict[str, Any]) -> None:
        """Create enhanced JSON result file for a chunk with speaker recognition using existing models"""
        try:
            json_filename = f"{chunk_info['filename']}.json"
            json_path = os.path.join(self.output_directories['chunk_results'], json_filename)
            
            # Extract data from enhanced result
            chunk_data = enhanced_result.get('chunk_info', {})
            transcription_data = enhanced_result.get('transcription', {})
            speaker_data = enhanced_result.get('speaker_recognition', {})
            
            # Create enhanced JSON result data
            text_content = transcription_data.get('text', '')
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
                'enhancement_applied': True,
                'enhancement_strategy': 'enhanced_with_speakers',
                'transcription_length': transcription_length,
                'words_estimated': words_estimated,
                'chunk_metadata': chunk_info,
                'chunking_strategy': chunk_info.get('chunking_strategy', 'overlapping'),
                'overlap_start': chunk_info.get('overlap_start', 0),
                'overlap_end': chunk_info.get('overlap_end', 0),
                'stride_length': chunk_info.get('stride_length', 5),
                
                # 🎯 NEW: Speaker Recognition Data using existing Pydantic model structure
                'speaker_recognition': {
                    'primary_speaker': speaker_data.get('primary_speaker', 'UNKNOWN'),
                    'primary_confidence': speaker_data.get('primary_confidence', 0.0),
                    'secondary_speakers': speaker_data.get('secondary_speakers', []),
                    'overlap_resolution': speaker_data.get('overlap_resolution', 'no_speaker_data'),
                    'has_multiple_speakers': speaker_data.get('has_multiple_speakers', False),
                    'speaker_mapping_id': speaker_data.get('speaker_mapping_id'),
                    'total_speakers': speaker_data.get('total_speakers', 0),
                    'speaker_names': speaker_data.get('speaker_names', [])
                },
                
                # 🎯 NEW: Enhanced Segments with Speaker Info
                'segments': transcription_data.get('segments', []),
                
                # 🎯 NEW: Processing Type
                'processing_type': enhanced_result.get('processing_type', 'enhanced_with_speakers'),
                
                # 🎯 NEW: Language and Confidence
                'language': transcription_data.get('language', 'he'),
                'confidence': transcription_data.get('confidence', 0.95)
            }
            
            # Save enhanced JSON result
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"🚀 Saved enhanced chunk JSON result with speaker recognition: {json_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error creating enhanced chunk JSON result: {e}")
            # No fallback - enhanced JSON should be created by DirectTranscriptionStrategy
            logger.info("ℹ️ Enhanced JSON creation failed, no fallback JSON will be created")
    



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
