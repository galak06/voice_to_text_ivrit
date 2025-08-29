#!/usr/bin/env python3
"""
Chunked transcription strategy for large audio files using overlapping chunks
Follows SOLID principles with dependency injection
"""

import logging
import time
from typing import TYPE_CHECKING, List, Optional, Dict, Any
import os # Added for os.path.join
import json # Added for JSON file handling
import time # Added for timestamp handling

from src.core.engines.strategies.base_strategy import BaseTranscriptionStrategy
from src.models.speaker_models import TranscriptionResult, TranscriptionSegment

if TYPE_CHECKING:
    from src.core.engines.base_interface import TranscriptionEngine

logger = logging.getLogger(__name__)


class ChunkedTranscriptionStrategy(BaseTranscriptionStrategy):
    """Strategy for chunked transcription of large files using overlapping chunks"""
    
    def __init__(self, config_manager):
        """Initialize the strategy with ConfigManager dependency injection"""
        super().__init__(config_manager)
        
        # Get chunk duration from ConfigManager
        if hasattr(self.config_manager.config, 'chunking') and hasattr(self.config_manager.config.chunking, 'chunk_duration_seconds'):
            self.chunk_duration_seconds = self.config_manager.config.chunking.chunk_duration_seconds
        elif hasattr(self.config_manager.config, 'processing') and hasattr(self.config_manager.config.processing, 'chunk_duration_seconds'):
            self.chunk_duration_seconds = self.config_manager.config.processing.chunk_duration_seconds
        else:
            raise ValueError("Chunk duration not found in ConfigManager configuration")
        
        # Enhanced initialization logging
        logger.info("🚀 Initializing ChunkedTranscriptionStrategy")
        logger.info(f"🎯 Configuration: chunk_duration={self.chunk_duration_seconds}s")
        logger.info(f"🔧 ConfigManager: {type(self.config_manager).__name__}")
        
        # Use ConfigManager directory paths exclusively
        dir_paths = self.config_manager.get_directory_paths()
        self.output_directories = {
            'chunk_results': dir_paths.get('chunk_results_dir'),
            'audio_chunks': dir_paths.get('audio_chunks_dir')
        }
        
        # Validate that all required directories are available
        if not self.output_directories['chunk_results']:
            raise ValueError("Chunk results directory not found in ConfigManager")
        if not self.output_directories['audio_chunks']:
            raise ValueError("Audio chunks directory not found in ConfigManager")
            
        logger.info(f"📁 Output directories configured:")
        logger.info(f"   📂 Chunk results: {self.output_directories['chunk_results']}")
        logger.info(f"   🎵 Audio chunks: {self.output_directories['audio_chunks']}")
        
        # Initialize other attributes
        self.chunks = []
        self.current_chunk_index = 0
        self.engine = None
        self.transcription_engine = None
        
        # Get sample rate from configuration or use None to detect from audio file
        self.sample_rate = self._get_config_value('sample_rate', None)
        
        # Initialize injected services
        self._initialize_services()
        
        # Inject DirectTranscriptionStrategy for consistent chunk processing
        self._initialize_direct_strategy()
        
        # Initialize output strategy with dependency injection
        self._initialize_output_strategy()
        
        logger.info(f"✅ ChunkedTranscriptionStrategy initialized successfully")
        logger.info(f"   🎯 Chunk duration: {self.chunk_duration_seconds}s")
        logger.info(f"   🎵 Sample rate: {self.sample_rate}Hz (will be detected from audio file if not specified)")
    
    def _initialize_services(self):
        """Initialize injected services"""
        try:
            from ...services.chunk_management_service import ChunkManagementService
            from ...services.chunk_processing_service import ChunkProcessingService
            
            # Initialize chunk management service
            self.chunk_management_service = ChunkManagementService(self.config_manager)
            
            # Initialize chunk processing service
            self.chunk_processing_service = ChunkProcessingService(self.config_manager)
            
            logger.info("✅ Injected services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing injected services: {e}")
            raise RuntimeError(f"Failed to initialize injected services: {e}")
    
    def _initialize_direct_strategy(self):
        """Initialize and inject DirectTranscriptionStrategy"""
        try:
            from .direct_transcription_strategy import DirectTranscriptionStrategy
            
            self.direct_transcription_strategy = DirectTranscriptionStrategy(self.config_manager)
            
            logger.info("✅ DirectTranscriptionStrategy injected successfully")
            
        except Exception as e:
            logger.error(f"❌ Error injecting DirectTranscriptionStrategy: {e}")
            raise RuntimeError(f"Failed to inject DirectTranscriptionStrategy: {e}")
    
    def _initialize_output_strategy(self):
        """Initialize and inject output strategy with dependency injection"""
        try:
            from ...factories.output_strategy_factory import OutputStrategyFactory
            
            # Create output strategy using factory with dependency injection
            self.output_strategy = OutputStrategyFactory.create_merged_output_strategy(self.config_manager)
            
            logger.info("✅ Output strategy injected successfully with dependency injection")
            
        except Exception as e:
            logger.error(f"❌ Error injecting output strategy: {e}")
            raise RuntimeError(f"Failed to inject output strategy: {e}")
    
    def _print_progress_bar(self, current: int, total: int, prefix: str = "Progress", suffix: str = "", length: int = 50):
        """Print a progress bar to the console"""
        try:
            filled_length = int(length * current // total)
            bar = '█' * filled_length + '-' * (length - filled_length)
            percent = 100.0 * current / total
            print(f'\r{prefix}: |{bar}| {percent:.1f}% {suffix}', end='', flush=True)
            if current == total:
                print()  # New line when complete
        except Exception:
            # Fallback to simple progress if progress bar fails
            pass
    
    def _format_time(self, seconds: float) -> str:
        """Format time in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def _log_chunk_progress_header(self, total_chunks: int, audio_duration: float):
        """Log a header showing chunking strategy and expected results"""
        logger.info("=" * 80)
        logger.info("🎯 CHUNKED TRANSCRIPTION STRATEGY INITIALIZED")
        logger.info("=" * 80)
        logger.info(f"📊 Audio file duration: {audio_duration:.1f}s ({self._format_time(audio_duration)})")
        logger.info(f"🎯 Chunk duration: {self.chunk_duration_seconds}s")
        logger.info(f"📈 Expected chunks: {total_chunks}")
        logger.info(f"⏱️  Estimated processing time: {self._format_time(total_chunks * 2)} (rough estimate)")
        logger.info(f"💾 Output directories:")
        logger.info(f"   📂 Chunk results: {self.output_directories['chunk_results']}")
        logger.info(f"   🎵 Audio chunks: {self.output_directories['audio_chunks']}")
        logger.info("=" * 80)
    
    def _log_chunk_processing_start(self, chunk_num: int, total_chunks: int, chunk_info: Dict[str, Any]):
        """Log detailed information when starting to process a chunk"""
        progress_percent = (chunk_num / total_chunks) * 100
        chunk_duration = chunk_info['end'] - chunk_info['start']
        
        logger.info("─" * 60)
        logger.info(f"🔄 PROCESSING CHUNK {chunk_num + 1}/{total_chunks} ({progress_percent:.1f}%)")
        logger.info(f"   📍 Time range: {chunk_info['start']:.1f}s - {chunk_info['end']:.1f}s")
        logger.info(f"   ⏱️  Duration: {chunk_duration:.1f}s")
        logger.info(f"   📁 Filename: {chunk_info['filename']}")
        logger.info(f"   🎯 Chunk number: {chunk_info['chunk_number']}")
        logger.info("─" * 60)
    
    def _log_chunk_processing_result(self, chunk_num: int, total_chunks: int, chunk_info: Dict[str, Any], 
                                   processing_time: float, success: bool, text_length: int = 0):
        """Log the result of processing a chunk"""
        progress_percent = (chunk_num / total_chunks) * 100
        status_icon = "✅" if success else "❌"
        status_text = "COMPLETED" if success else "FAILED"
        
        logger.info(f"{status_icon} CHUNK {chunk_num + 1}/{total_chunks} {status_text} ({progress_percent:.1f}%)")
        logger.info(f"   ⏱️  Processing time: {processing_time:.1f}s")
        if success and text_length > 0:
            logger.info(f"   📝 Text length: {text_length} characters")
            logger.info(f"   📊 Words estimated: {text_length // 5} (rough estimate)")
        logger.info(f"   📍 Time range: {chunk_info['start']:.1f}s - {chunk_info['end']:.1f}s")
        logger.info("─" * 60)
    
    def _log_overall_progress(self, completed_chunks: int, total_chunks: int, failed_chunks: int, 
                             elapsed_time: float, estimated_remaining: float):
        """Log overall progress summary"""
        overall_progress = (completed_chunks / total_chunks) * 100
        success_rate = (completed_chunks / (completed_chunks + failed_chunks)) * 100 if (completed_chunks + failed_chunks) > 0 else 0
        
        logger.info("📈 OVERALL PROGRESS SUMMARY")
        logger.info(f"   🎯 Progress: {overall_progress:.1f}% ({completed_chunks}/{total_chunks} chunks)")
        logger.info(f"   ✅ Successful: {completed_chunks} chunks")
        logger.info(f"   ❌ Failed: {failed_chunks} chunks")
        logger.info(f"   📊 Success rate: {success_rate:.1f}%")
        logger.info(f"   ⏱️  Elapsed time: {self._format_time(elapsed_time)}")
        logger.info(f"   ⏳ Estimated remaining: {self._format_time(estimated_remaining)}")
        logger.info(f"   🎯 Estimated completion: {self._format_time(elapsed_time + estimated_remaining)}")
        logger.info("─" * 60)
    
    def _log_final_summary(self, total_time: float, completed_chunks: int, failed_chunks: int, 
                          total_segments: int, audio_duration: float):
        """Log final transcription summary"""
        logger.info("=" * 80)
        logger.info("🎯 TRANSCRIPTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"📊 Final Results:")
        logger.info(f"   ✅ Successful chunks: {completed_chunks}")
        logger.info(f"   ❌ Failed chunks: {failed_chunks}")
        logger.info(f"   📝 Total segments: {total_segments}")
        logger.info(f"   🎵 Audio duration: {self._format_time(audio_duration)}")
        logger.info(f"   ⏱️  Total processing time: {self._format_time(total_time)}")
        logger.info(f"   🚀 Processing speed: {audio_duration/total_time:.2f}x real-time")
        logger.info(f"   📁 Output saved to:")
        logger.info(f"      📂 Chunk results: {self.output_directories['chunk_results']}")
        logger.info(f"      🎵 Audio chunks: {self.output_directories['audio_chunks']}")
        logger.info("=" * 80)
    
    def _log_error_summary(self, total_time: float, error_message: str, completed_chunks: int, failed_chunks: int):
        """Log error summary when transcription fails"""
        logger.error("=" * 80)
        logger.error("❌ TRANSCRIPTION FAILED")
        logger.error("=" * 80)
        logger.error(f"🚨 Error: {error_message}")
        logger.error(f"📊 Partial Results:")
        logger.error(f"   ✅ Completed chunks: {completed_chunks}")
        logger.error(f"   ❌ Failed chunks: {failed_chunks}")
        logger.error(f"   ⏱️  Time before failure: {self._format_time(total_time)}")
        logger.error(f"   📁 Partial output saved to:")
        logger.error(f"      📂 Chunk results: {self.output_directories['chunk_results']}")
        logger.error(f"      🎵 Audio chunks: {self.output_directories['audio_chunks']}")
        logger.error("=" * 80)
    
    def _get_config_value(self, key: str, default_value=None):
        """Get configuration value from ConfigManager"""
        try:
            if hasattr(self.config_manager.config, key):
                return getattr(self.config_manager.config, key)
            return default_value
        except Exception:
            return default_value
    
    def execute(self, audio_file_path: str, model_name: str, engine: 'TranscriptionEngine') -> TranscriptionResult:
        """Execute chunked transcription strategy"""
        start_time = time.time()
        
        # Clean up any existing chunks before starting using dedicated CleanupService
        try:
            from src.core.services.cleanup_service import CleanupService
            logger.info("🧹 Cleaning up existing chunks before starting chunked transcription...")
            cleanup_service = CleanupService(self.config_manager)
            cleanup_results = cleanup_service.cleanup_before_transcription(
                clear_console=False, 
                clear_files=True, 
                clear_output=False
            )
            logger.info("🧹 Chunk cleanup completed before transcription")
            logger.info(f"📊 Cleanup results: {cleanup_results}")
        except Exception as e:
            logger.warning(f"⚠️ Chunk cleanup failed: {e}")
        
        try:
            # Get audio duration
            audio_duration = self._get_audio_duration(audio_file_path)
            
            # Create chunks using injected chunk management service
            chunks = self.chunk_management_service.create_and_save_chunks(audio_file_path, audio_duration)
            total_chunks = len(chunks)
            
            # Log chunking strategy header
            self._log_chunk_progress_header(total_chunks, audio_duration)
            
            # Initialize progress tracking
            completed_chunks = 0
            failed_chunks = 0
            
            # Process each chunk using the injected DirectTranscriptionStrategy
            all_segments = []
            for chunk_index, chunk_info in enumerate(chunks):
                chunk_num = chunk_info['chunk_number']
                chunk_start_time_individual = time.time()
                
                # Log detailed chunk processing start
                self._log_chunk_processing_start(chunk_index, total_chunks, chunk_info)
                
                # Mark chunk as processing started
                self._mark_chunk_processing_started(chunk_info)
                
                # Process the chunk using the injected DirectTranscriptionStrategy
                chunk_result = self._process_chunk_with_direct_strategy(
                    chunk_info, model_name, engine, audio_file_path
                )
                
                # Verify chunk result before continuing
                if chunk_result is None:
                    failed_chunks += 1
                    chunk_processing_time = time.time() - chunk_start_time_individual
                    self._log_chunk_processing_result(chunk_index, total_chunks, chunk_info, chunk_processing_time, False)
                    self._mark_chunk_failed(chunk_info, "Chunk processing failed due to unknown error.")
                    logger.error(f"🛑 Breaking chunk processing due to failure in chunk {chunk_num}")
                    break
                
                # Check if chunk has error message
                if isinstance(chunk_result, dict) and chunk_result.get('error_message'):
                    failed_chunks += 1
                    error_msg = chunk_result['error_message']
                    chunk_processing_time = time.time() - chunk_start_time_individual
                    self._log_chunk_processing_result(chunk_index, total_chunks, chunk_info, chunk_processing_time, False)
                    self._mark_chunk_failed(chunk_info, error_msg)
                    logger.error(f"🛑 Breaking chunk processing due to error in chunk {chunk_num}")
                    break
                
                # Check if chunk result indicates failure
                if isinstance(chunk_result, dict) and chunk_result.get('status') == 'error':
                    failed_chunks += 1
                    error_msg = chunk_result.get('error_message', 'Unknown error')
                    chunk_processing_time = time.time() - chunk_start_time_individual
                    self._log_chunk_processing_result(chunk_index, total_chunks, chunk_info, chunk_processing_time, False)
                    self._mark_chunk_failed(chunk_info, error_msg)
                    logger.error(f"🛑 Breaking chunk processing due to error status in chunk {chunk_num}")
                    break
                
                # Check JSON file for errors as additional verification
                if self.chunk_processing_service.check_chunk_errors(chunk_info):
                    failed_chunks += 1
                    chunk_processing_time = time.time() - chunk_start_time_individual
                    self._log_chunk_processing_result(chunk_index, total_chunks, chunk_info, chunk_processing_time, False)
                    self._mark_chunk_failed(chunk_info, "Chunk processing failed due to JSON error.")
                    logger.error(f"🛑 Breaking chunk processing due to JSON error in chunk {chunk_num}")
                    break
                
                # Update progress after processing
                chunk_processing_time = time.time() - chunk_start_time_individual
                
                # Process chunk result
                if isinstance(chunk_result, dict) and 'segments' in chunk_result:
                    completed_chunks += 1
                    segments = chunk_result['segments']
                    all_segments.extend(segments)
                    text_content = " ".join([seg.get('text', '') for seg in segments if seg.get('text')])
                    self._log_chunk_processing_result(chunk_index, total_chunks, chunk_info, chunk_processing_time, True, len(text_content))
                    self._mark_chunk_completed(chunk_info, text_content)
                else:
                    failed_chunks += 1
                    self._log_chunk_processing_result(chunk_index, total_chunks, chunk_info, chunk_processing_time, False)
                    self._mark_chunk_failed(chunk_info, "Chunk processing failed due to no segments.")
                
                # Log overall progress summary
                elapsed_time = time.time() - start_time
                estimated_total_time = (elapsed_time / (chunk_index + 1)) * total_chunks if chunk_index > 0 else 0
                estimated_remaining = estimated_total_time - elapsed_time
                self._log_overall_progress(completed_chunks, total_chunks, failed_chunks, elapsed_time, estimated_remaining)
                
                # Print progress bar
                self._print_progress_bar(completed_chunks + failed_chunks, total_chunks, "Chunk Processing", f"{completed_chunks}/{total_chunks}")
            
            # Log final results
            total_time = time.time() - start_time
            
            if all_segments:
                self._log_final_summary(total_time, completed_chunks, failed_chunks, len(all_segments), audio_duration)
                return self._create_final_result(audio_file_path, all_segments, start_time, model_name)
            else:
                self._log_error_summary(total_time, "No segments generated", completed_chunks, failed_chunks)
                return self._create_error_result(audio_file_path, "No segments generated")
                
        except Exception as e:
            total_time = time.time() - start_time
            # Initialize variables in case they weren't set in the try block
            completed_chunks = getattr(self, 'completed_chunks', 0)
            failed_chunks = getattr(self, 'failed_chunks', 0)
            self._log_error_summary(total_time, str(e), completed_chunks, failed_chunks)
            return self._create_error_result(audio_file_path, str(e))
    
    def _process_chunk_with_direct_strategy(self, chunk_info: Dict[str, Any], model_name: str, engine, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """Process a single chunk using the injected DirectTranscriptionStrategy"""
        try:
            chunk_start = chunk_info['start']
            chunk_end = chunk_info['end']
            chunk_duration = chunk_end - chunk_start
            
            logger.info(f"🔧 Starting transcription for chunk {chunk_info['chunk_number']}")
            logger.info(f"   📍 Time range: {chunk_start:.1f}s - {chunk_end:.1f}s (duration: {chunk_duration:.1f}s)")
            
            # Get the audio chunk file path
            chunk_number = chunk_info['chunk_number']
            start_time = int(chunk_info['start'])
            end_time = int(chunk_info['end'])
            audio_chunk_filename = f"audio_chunk_{chunk_number:03d}_{start_time}s_{end_time}s.wav"
            audio_chunk_path = os.path.join(self.output_directories['audio_chunks'], audio_chunk_filename)
            
            if not os.path.exists(audio_chunk_path):
                logger.error(f"❌ Audio chunk file not found: {audio_chunk_path}")
                return None
            
            # Clean model memory before processing this chunk (but don't reload the model)
            if hasattr(engine, 'cleanup_memory_only'):
                engine.cleanup_memory_only()
                logger.debug(f"🧹 Model memory cleaned for chunk {chunk_number}")
            else:
                # If memory-only cleanup is not available, just log a warning but don't reload the model
                logger.warning(f"⚠️ Memory-only cleanup not available for chunk {chunk_number} - model will remain loaded")
            
            # Use the injected DirectTranscriptionStrategy to process this chunk
            # This ensures we get exactly the same transcription logic and results
            logger.info(f"🎯 Processing chunk {chunk_number} with DirectTranscriptionStrategy")
            chunk_result = self.direct_transcription_strategy.execute(audio_chunk_path, model_name, engine)
            
            if not chunk_result or not chunk_result.success:
                logger.warning(f"⚠️ Chunk transcription failed: {chunk_info['filename']}")
                return None
            
            # Convert TranscriptionResult to the expected dict format for consistency
            if hasattr(chunk_result, 'speakers') and chunk_result.speakers:
                segments = []
                for speaker_id, speaker_segments in chunk_result.speakers.items():
                    for segment in speaker_segments:
                        # Adjust segment timing to match the chunk's position in the full audio
                        adjusted_start = segment.start + chunk_start
                        adjusted_end = segment.end + chunk_start
                        
                        segments.append({
                            'start': adjusted_start,
                            'end': adjusted_end,
                            'text': segment.text,
                            'speaker': speaker_id
                        })
                
                # Get the full text from the chunk result
                full_text = chunk_result.full_text if hasattr(chunk_result, 'full_text') else ' '.join([seg.get('text', '') for seg in segments])
                
                logger.info(f"✅ Chunk {chunk_number} processed successfully: {len(segments)} segments, {len(full_text)} characters")
                
                return {
                    'segments': segments,
                    'success': True,
                    'text': full_text,
                    'chunk_number': chunk_number,
                    'chunk_start': chunk_start,
                    'chunk_end': chunk_end
                }
            else:
                logger.warning(f"⚠️ No segments found in chunk result: {chunk_info['filename']}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing chunk {chunk_info.get('filename', 'unknown')}: {e}")
            return None
    
    def _get_audio_duration(self, audio_file_path: str) -> float:
        """Get audio file duration"""
        try:
            import librosa
            duration = librosa.get_duration(path=audio_file_path)
            return duration
        except Exception as e:
            logger.warning(f"⚠️ Could not get audio duration: {e}")
            return 30.0  # Default fallback
    
    def _create_final_result(self, audio_file_path: str, segments: List[Dict[str, Any]], start_time: float, model_name: str) -> TranscriptionResult:
        """Create final transcription result using injected output strategy with intelligent deduplication"""
        processing_time = time.time() - start_time
        
        # Use injected output strategy to create final result
        full_text = self.output_strategy.create_final_output(segments)
        deduplicated_segments = self.output_strategy.create_segmented_output(segments)
        
        logger.info(f"✅ Output strategy processed: {len(segments)} → {len(deduplicated_segments)} segments")
        logger.info(f"✅ Final text created: {len(full_text)} characters")
        
        # Convert deduplicated segments to proper format
        speakers_dict = {}
        
        for segment in deduplicated_segments:
            speaker_id = segment.get('speaker_id', 'unknown')
            if speaker_id not in speakers_dict:
                speakers_dict[speaker_id] = []
            
            # Create TranscriptionSegment from segment data
            from src.models.speaker_models import TranscriptionSegment
            transcription_segment = TranscriptionSegment(
                text=segment.get('text', ''),
                start=segment.get('start', 0.0),
                end=segment.get('end', 0.0),
                speaker=speaker_id,
                confidence=segment.get('confidence', 0.0),
                chunk_file=segment.get('chunk_file', ''),
                chunk_number=segment.get('chunk_number', 0),
                metadata=segment.get('metadata', {})
            )
            speakers_dict[speaker_id].append(transcription_segment)
        
        speaker_count = len(speakers_dict)
        
        logger.info(f"📝 Final transcript: {len(full_text)} characters, {len(full_text.split())} words")
        logger.info(f"🎯 Output strategy completed with {len(deduplicated_segments)} deduplicated segments")
        
        return TranscriptionResult(
            success=True,
            speakers=speakers_dict,
            full_text=full_text,
            transcription_time=processing_time,
            model_name=model_name,
            audio_file=audio_file_path,
            speaker_count=speaker_count
        )
    
    def _create_error_result(self, audio_file_path: str, error_message: str) -> TranscriptionResult:
        """Create error result"""
        return TranscriptionResult(
            success=False,
            speakers={},
            full_text="",
            transcription_time=0.0,
            model_name="unknown",
            audio_file=audio_file_path,
            speaker_count=0,
            error_message=error_message
        )
    
    def _update_chunk_json_progress(self, chunk_info: Dict[str, Any], status: str, message: str, **kwargs) -> None:
        """Update JSON progress file for a chunk directly within this strategy"""
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
    
    def _mark_chunk_processing_started(self, chunk_info: Dict[str, Any]) -> None:
        """Mark chunk as processing started"""
        self._update_chunk_json_progress(
            chunk_info, 
            "processing", 
            f"Transcription started for chunk {chunk_info['chunk_number']}",
            processing_started=time.time()
        )
    
    def _mark_chunk_completed(self, chunk_info: Dict[str, Any], transcription_text: str) -> None:
        """Mark chunk as completed with transcription results"""
        self._update_chunk_json_progress(
            chunk_info, 
            "completed", 
            f"Transcription completed successfully for chunk {chunk_info['chunk_number']}",
            text=transcription_text,
            transcription_length=len(transcription_text),
            words_estimated=len(transcription_text.split()),
            processing_completed=time.time()
        )
    
    def _mark_chunk_failed(self, chunk_info: Dict[str, Any], error_message: str) -> None:
        """Mark chunk as failed with error message"""
        self._update_chunk_json_progress(
            chunk_info, 
            "error", 
            f"Transcription failed for chunk {chunk_info['chunk_number']}",
            error_message=error_message,
            processing_completed=time.time()
        )
    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return "ChunkedTranscriptionStrategy"
