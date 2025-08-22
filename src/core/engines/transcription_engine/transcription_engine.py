#!/usr/bin/env python3
"""
Transcription Engine Base Class
Provides common functionality for all transcription engines
"""

import json
import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from src.models.speaker_models import TranscriptionResult, TranscriptionSegment
from src.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class TranscriptionEngine(ABC):
    """Abstract base class for transcription engines"""
    
    def __init__(self, config, app_config=None):
        """
        Initialize transcription engine with configuration
        
        Args:
            config: Speaker configuration with optional cleanup settings
            app_config: Application configuration (optional)
            
        Configuration options:
            - cleanup_logs_before_run: Whether to clean logs before each run (default: True)
            - max_output_files: Maximum number of output files to keep (default: 5)
        """
        self.config = config
        self.app_config = app_config
        self.temp_chunks_dir = "output/temp_chunks"
        self.cleanup_logs_before_run = getattr(config, 'cleanup_logs_before_run', True)
        self.max_output_files = getattr(config, 'max_output_files', 5)
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe audio file using the most appropriate method"""
        import os
        
        # Check if we have existing audio chunks first
        chunks_dir = "examples/audio/voice/audio_chunks/"
        if os.path.exists(chunks_dir):
            chunk_files = [f for f in os.listdir(chunks_dir) if f.startswith("audio_chunk_") and f.endswith(".wav")]
            if chunk_files:
                logger.info(f"🎯 Found {len(chunk_files)} existing audio chunks, processing them directly")
                return self._process_existing_audio_chunks(audio_file_path, model_name)
        
        # If no existing chunks, check file size and use appropriate method
        if os.path.exists(audio_file_path):
            file_size = os.path.getsize(audio_file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > 100:  # Files larger than 100MB
                logger.info(f"📁 Large file detected ({file_size_mb:.1f}MB), using audio chunk processing")
                return self._transcribe_with_audio_chunks(audio_file_path, model_name, 120)
            else:
                logger.info(f"📁 Small file detected ({file_size_mb:.1f}MB), processing directly")
                # For small files, we need to load the audio first
                try:
                    import librosa
                    audio_data, sample_rate = librosa.load(audio_file_path, sr=16000, mono=True)
                    return self._transcribe_directly(audio_file_path, model_name, audio_data, sample_rate)
                except Exception as e:
                    logger.error(f"❌ Error loading audio for direct processing: {e}")
                    # Fallback to chunk processing
                    return self._transcribe_with_audio_chunks(audio_file_path, model_name, 120)
        else:
            logger.error(f"❌ Audio file not found: {audio_file_path}")
            # Return a failed result instead of None
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0.0,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message="Audio file not found"
            )
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available"""
        pass
    
    @abstractmethod
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk - to be implemented by each engine"""
        pass
    
    def _cleanup_model_memory(self):
        """Clean up model memory - to be overridden by engines that need it"""
        # This method is now a placeholder and will be overridden by specific engines
        pass
    
    @abstractmethod
    def cleanup_models(self):
        """Clean up loaded models and free memory - to be overridden by specific engines"""
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the engine - to be overridden by specific engines"""
        pass
    
    def _transcribe_chunk_with_fallback(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str, recursion_depth: int = 0) -> str:
        """
        Fallback transcription method that splits large chunks into smaller sub-chunks.
        This helps when large chunks fail due to memory or processing issues.
        
        Args:
            audio_chunk: Audio data to transcribe
            chunk_count: Current chunk number for logging
            chunk_start: Start time of chunk in seconds
            chunk_end: End time of chunk in seconds
            model_name: Name of the transcription model to use
            recursion_depth: Current recursion depth to prevent infinite loops (default: 0)
            
        Returns:
            Combined transcription text from all sub-chunks
            
        Raises:
            ValueError: If chunk is too small for sub-division or recursion depth exceeded
        """
        # Prevent infinite recursion - if we're already in fallback mode, don't recurse further
        # This prevents the stack overflow issue where fallback calls itself infinitely
        if recursion_depth > 2:
            logger.error(f"❌ Maximum recursion depth ({recursion_depth}) exceeded for chunk {chunk_count}. Stopping to prevent stack overflow.")
            raise ValueError(f"Maximum recursion depth exceeded ({recursion_depth}) - preventing stack overflow")
        
        # Warn when recursion depth is getting high
        if recursion_depth > 1:
            logger.warning(f"⚠️ High recursion depth ({recursion_depth}) detected for chunk {chunk_count}. This may indicate underlying transcription issues.")
        
        # Log fallback attempt with key information
        logger.info(f"🔧 Fallback for chunk {chunk_count} ({chunk_start:.1f}s - {chunk_end:.1f}s) [depth: {recursion_depth}]")
        
        # Validate chunk parameters
        chunk_duration = chunk_end - chunk_start
        total_chunk_duration = len(audio_chunk) / 16000
        
        if chunk_duration < 30:
            raise ValueError("Chunk too small for sub-division")
        
        # Check for duration mismatches
        if abs(chunk_duration - total_chunk_duration) > 1.0:
            logger.warning(f"⚠️ Duration mismatch: expected {chunk_duration:.1f}s, got {total_chunk_duration:.1f}s")
        
        # Handle small chunks directly
        if total_chunk_duration < 30:
            logger.info(f"📊 Small chunk ({total_chunk_duration:.1f}s), processing directly")
            try:
                return self._transcribe_chunk(audio_chunk, 1, chunk_start, chunk_end, model_name)
            except Exception as e:
                logger.error(f"❌ Direct processing failed: {e}")
                raise
        
        # Configure sub-chunking
        sub_chunk_duration = 30.0
        overlap = 5.0
        effective_chunk_size = sub_chunk_duration - overlap
        num_sub_chunks = max(1, int((total_chunk_duration + overlap - 1) // effective_chunk_size))
        
        logger.info(f"📊 Sub-chunking: {total_chunk_duration:.1f}s → {num_sub_chunks} chunks of {effective_chunk_size:.1f}s")
        
        sub_results = []
        for sub_chunk_num in range(1, num_sub_chunks + 1):
            # Calculate chunk boundaries
            current_start = (sub_chunk_num - 1) * effective_chunk_size
            current_end = min(current_start + sub_chunk_duration, total_chunk_duration)
            
            # Safety checks
            if current_start >= total_chunk_duration:
                break
            if sub_chunk_num > 100:
                logger.error(f"❌ Too many sub-chunks ({sub_chunk_num}), stopping")
                break
                
            # Extract and validate sub-chunk
            start_sample = int(current_start * 16000)
            end_sample = int(current_end * 16000)
            sub_audio = audio_chunk[start_sample:end_sample]
            
            if len(sub_audio) == 0:
                continue
                
            # Process sub-chunk
            absolute_start = chunk_start + current_start
            absolute_end = chunk_start + current_end
            
            logger.info(f"🔧 Sub-chunk {sub_chunk_num}/{num_sub_chunks}: {absolute_start:.1f}s - {absolute_end:.1f}s")
            
            try:
                sub_result = self._transcribe_chunk(sub_audio, sub_chunk_num, absolute_start, absolute_end, model_name)
                sub_results.append(sub_result)
                logger.debug(f"✅ Sub-chunk {sub_chunk_num} completed")
            except Exception as sub_error:
                logger.warning(f"⚠️ Sub-chunk {sub_chunk_num} failed: {sub_error}")
                sub_results.append(f"ERROR: {str(sub_error)}")
        
        # Combine results
        if sub_results:
            combined_result = " ".join(sub_results)
            logger.info(f"✅ Fallback completed: {len(sub_results)} sub-chunks")
            return combined_result
        else:
            raise ValueError("No sub-chunks were processed successfully")
    
    def _transcribe_in_chunks(self, audio_file_path: str, model_name: str, chunk_duration_seconds: int = 120) -> TranscriptionResult:
        """
        Transcribe audio file with automatic chunking decision based on file size
        """
        # Clean up logs before starting new transcription
        self._cleanup_logs()
        
        logger.info(f"🎯 Starting transcription: {audio_file_path}")
        
        # Load and validate audio
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        try:
            import librosa
            audio_data, sample_rate = librosa.load(audio_file_path, sr=16000, mono=True)
            duration = len(audio_data) / sample_rate
            logger.info(f"✅ Audio loaded: {duration:.1f}s at {sample_rate}Hz")
        except ImportError:
            logger.error("❌ Librosa not available")
            raise ImportError("Librosa is required for audio processing")
        except Exception as e:
            logger.error(f"❌ Error loading audio: {e}")
            raise
        
        # Always use the new audio chunk method for better speaker diarization
        logger.info(f"📊 Audio duration ({duration:.1f}s), using new audio chunk processing method")
        logger.info(f"🔧 Chunk size: {chunk_duration_seconds}s")
        
        # Use the new audio chunk method that creates actual audio files
        return self._transcribe_with_audio_chunks(audio_file_path, model_name, chunk_duration_seconds)
    
    def _transcribe_directly(self, audio_file_path: str, model_name: str, audio_data, sample_rate) -> TranscriptionResult:
        """
        Transcribe audio file directly without chunking (for small files)
        """
        logger.info(f"🎯 Processing audio directly (no chunking needed)")
        
        start_time = time.time()
        
        try:
            # Transcribe the entire audio as one chunk
            chunk_text = self._transcribe_chunk(audio_data, 1, 0, len(audio_data) / sample_rate, model_name)
            
            if chunk_text and chunk_text.strip():
                segment = TranscriptionSegment(
                    start=0,
                    end=len(audio_data) / sample_rate,
                    text=chunk_text,
                    speaker="0"
                )
                
                total_time = time.time() - start_time
                total_text = chunk_text
                
                result = TranscriptionResult(
                    success=True,
                    speakers={"0": [segment]},
                    full_text=total_text,
                    transcription_time=total_time,
                    model_name=model_name,
                    audio_file=audio_file_path,
                    speaker_count=1
                )
                
                logger.info(f"🎯 Direct transcription completed: {total_time:.1f}s, {len(total_text)} chars")
                return result
            else:
                raise ValueError("No transcription text produced")
                
        except Exception as e:
            logger.error(f"❌ Error in direct transcription: {e}")
            raise
    
    def _transcribe_with_audio_chunks(self, audio_file_path: str, model_name: str, chunk_duration_seconds: int = 120) -> TranscriptionResult:
        """
        Transcribe audio file by first creating audio chunks, then processing them one by one
        This approach is more memory efficient and reliable than processing in memory
        """
        # Clean up logs before starting new transcription
        self._cleanup_logs()
        
        logger.info(f"🎯 Starting transcription with audio chunks: {audio_file_path}")
        
        # Load and validate audio
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        try:
            import librosa
            audio_data, sample_rate = librosa.load(audio_file_path, sr=16000, mono=True)
            duration = len(audio_data) / sample_rate
            logger.info(f"✅ Audio loaded: {duration:.1f}s at {sample_rate}Hz")
        except ImportError:
            logger.error("❌ Librosa not available")
            raise ImportError("Librosa is required for audio processing")
        except Exception as e:
            logger.error(f"❌ Error loading audio: {e}")
            raise
        
        # Always process in chunks for better speaker diarization
        logger.info(f"📊 Audio duration ({duration:.1f}s), using audio chunk processing")
        logger.info(f"🔧 Chunk size: {chunk_duration_seconds}s")
        
        # Calculate chunks
        samples_per_chunk = chunk_duration_seconds * sample_rate
        total_chunks = max(1, int((len(audio_data) + samples_per_chunk - 1) // samples_per_chunk))
        logger.info(f"📊 Processing {total_chunks} chunks")
        
        # Create directories for audio chunks and transcription chunks
        audio_chunks_dir = "examples/audio/voice/audio_chunks"
        temp_chunks_dir = "output/temp_chunks"
        os.makedirs(audio_chunks_dir, exist_ok=True)
        os.makedirs(temp_chunks_dir, exist_ok=True)
        
        # STEP 1: Create all audio chunk files first
        logger.info("🔧 STEP 1: Creating audio chunk files...")
        audio_chunk_files = []
        
        for chunk_num in range(total_chunks):
            chunk_start = chunk_num * chunk_duration_seconds
            chunk_end = min((chunk_num + 1) * chunk_duration_seconds, len(audio_data) / sample_rate)
            
            # Extract chunk
            start_sample = int(chunk_start * sample_rate)
            end_sample = int(chunk_end * sample_rate)
            audio_chunk = audio_data[start_sample:end_sample]
            
            if len(audio_chunk) == 0:
                continue
            
            # Create audio chunk file
            audio_chunk_filename = f"audio_chunk_{chunk_num + 1:03d}_{chunk_start:.0f}s_{chunk_end:.0f}s.wav"
            audio_chunk_filepath = os.path.join(audio_chunks_dir, audio_chunk_filename)
            
            try:
                import soundfile as sf
                sf.write(audio_chunk_filepath, audio_chunk, sample_rate)
                audio_chunk_files.append({
                    'filepath': audio_chunk_filepath,
                    'chunk_num': chunk_num + 1,
                    'start_time': chunk_start,
                    'end_time': chunk_end
                })
                logger.info(f"✅ Created audio chunk: {audio_chunk_filename}")
            except ImportError:
                logger.error("❌ Soundfile not available, falling back to scipy")
                try:
                    import scipy.io.wavfile as wavfile
                    wavfile.write(audio_chunk_filepath, sample_rate, audio_chunk)
                    audio_chunk_files.append({
                        'filepath': audio_chunk_filepath,
                        'chunk_num': chunk_num + 1,
                        'start_time': chunk_start,
                        'end_time': chunk_end
                    })
                    logger.info(f"✅ Created audio chunk: {audio_chunk_filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to create audio chunk {chunk_num + 1}: {e}")
                    continue
            except Exception as e:
                logger.error(f"❌ Failed to create audio chunk {chunk_num + 1}: {e}")
                continue
        
        logger.info(f"✅ Created {len(audio_chunk_files)} audio chunk files")
        
        # Clean up original audio data from memory
        del audio_data
        logger.info("🧹 Freed original audio data from memory")
        
        # STEP 2: Process audio chunks one by one
        logger.info("🔧 STEP 2: Processing audio chunks one by one...")
        all_segments = []
        start_time = time.time()
        
        for audio_chunk_info in audio_chunk_files:
            chunk_num = audio_chunk_info['chunk_num']
            chunk_start = audio_chunk_info['start_time']
            chunk_end = audio_chunk_info['end_time']
            audio_chunk_filepath = audio_chunk_info['filepath']
            
            logger.info(f"🔧 Processing Chunk {chunk_num}/{total_chunks}: {chunk_start:.1f}s - {chunk_end:.1f}s")
            
            # Create pending transcription chunk file
            chunk_filename = f"chunk_{chunk_num:03d}_{chunk_start:.0f}s_{chunk_end:.0f}s.json"
            chunk_filepath = os.path.join(temp_chunks_dir, chunk_filename)
            
            pending_chunk_data = {
                "chunk_number": chunk_num,
                "start_time": chunk_start,
                "end_time": chunk_end,
                "status": "pending",
                "created_at": time.time(),
                "text": "",
                "processing_started": None,
                "processing_completed": None,
                "audio_chunk_file": audio_chunk_filepath
            }
            
            with open(chunk_filepath, 'w', encoding='utf-8') as f:
                json.dump(pending_chunk_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📝 Created pending chunk file: {chunk_filename}")
            
            try:
                # Update status to processing
                pending_chunk_data["status"] = "processing"
                pending_chunk_data["processing_started"] = time.time()
                with open(chunk_filepath, 'w', encoding='utf-8') as f:
                    json.dump(pending_chunk_data, f, ensure_ascii=False, indent=2)
                
                # Load audio chunk from file and transcribe
                chunk_audio_data, chunk_sample_rate = librosa.load(audio_chunk_filepath, sr=16000, mono=True)
                chunk_text = self._transcribe_chunk(chunk_audio_data, chunk_num, chunk_start, chunk_end, model_name)
                
                # Only create segment if we have actual text
                if chunk_text and chunk_text.strip():
                     # Perform speaker diarization on this chunk
                     try:
                         logger.info(f"🔊 CHUNK {chunk_num}: Starting speaker diarization...")
                         speaker_start_time = time.time()
                         
                         # Import and initialize speaker diarization service
                         from src.core.orchestrator.speaker_transcription_service import SpeakerTranscriptionService
                         speaker_service = SpeakerTranscriptionService(self.config, self.app_config)
                         
                         # Perform speaker diarization on the audio chunk
                         speaker_result = speaker_service.speaker_diarization(
                             audio_file_path=audio_chunk_filepath, 
                             model_name=model_name,
                             save_output=False  # Don't save individual chunk outputs
                         )
                         
                         speaker_time = time.time() - speaker_start_time
                         logger.info(f"✅ CHUNK {chunk_num}: Speaker diarization completed in {speaker_time:.2f}s")
                         
                         # Add each speaker segment with proper timing
                         speaker_count = 0
                         for speaker_id, speaker_segments in speaker_result.speakers.items():
                             for seg in speaker_segments:
                                 # Adjust segment timing to be relative to the chunk
                                 adjusted_segment = TranscriptionSegment(
                                     start=chunk_start + seg.start,
                                     end=chunk_start + seg.end,
                                     text=seg.text,
                                     speaker=speaker_id
                                 )
                                 all_segments.append(adjusted_segment)
                                 speaker_count += 1
                         
                         logger.info(f"✅ CHUNK {chunk_num}: Created {speaker_count} speaker segments")
                         
                         # Update chunk file with completed status, text, and speaker info
                         pending_chunk_data["status"] = "completed"
                         pending_chunk_data["processing_completed"] = time.time()
                         pending_chunk_data["text"] = chunk_text
                         pending_chunk_data["speaker_count"] = speaker_count
                         pending_chunk_data["speaker_segments"] = [
                             {
                                 "speaker": seg.speaker,
                                 "start": seg.start - chunk_start,
                                 "end": seg.end - chunk_start,
                                 "text": seg.text
                             } for seg in all_segments[-speaker_count:]  # Get the segments we just added
                         ]
                         
                         with open(chunk_filepath, 'w', encoding='utf-8') as f:
                             json.dump(pending_chunk_data, f, ensure_ascii=False, indent=2)
                         
                         logger.info(f"✅ Chunk {chunk_num} completed with speaker diarization and saved to: {chunk_filename}")
                         
                     except Exception as e:
                         logger.warning(f"⚠️ CHUNK {chunk_num}: Speaker diarization failed: {e}")
                         logger.info(f"🔧 CHUNK {chunk_num}: Falling back to single speaker mode")
                         
                         # Fallback to single speaker if diarization fails
                         segment = TranscriptionSegment(
                             start=chunk_start,
                             end=chunk_end,
                             text=chunk_text,
                             speaker="0"
                         )
                         all_segments.append(segment)
                         
                         # Update chunk file with completed status and text (fallback mode)
                         pending_chunk_data["status"] = "completed"
                         pending_chunk_data["processing_completed"] = time.time()
                         pending_chunk_data["text"] = chunk_text
                         pending_chunk_data["speaker_count"] = 1
                         pending_chunk_data["diarization_failed"] = True
                         pending_chunk_data["error"] = str(e)
                         
                         with open(chunk_filepath, 'w', encoding='utf-8') as f:
                             json.dump(pending_chunk_data, f, ensure_ascii=False, indent=2)
                         
                         logger.info(f"✅ Chunk {chunk_num} completed in fallback mode and saved to: {chunk_filename}")
                else:
                    logger.warning(f"⚠️ Chunk {chunk_num}: No text produced, skipping segment")
                    # Update chunk file with error status
                    pending_chunk_data["status"] = "error"
                    pending_chunk_data["processing_completed"] = time.time()
                    pending_chunk_data["error"] = "No text produced"
                    with open(chunk_filepath, 'w', encoding='utf-8') as f:
                        json.dump(pending_chunk_data, f, ensure_ascii=False, indent=2)
                
                # Clean up audio chunk data from memory
                del chunk_audio_data
                
            except Exception as e:
                logger.error(f"❌ Error processing chunk {chunk_num}: {e}")
                # Update chunk file with error status
                pending_chunk_data["status"] = "error"
                pending_chunk_data["processing_completed"] = time.time()
                pending_chunk_data["error"] = str(e)
                with open(chunk_filepath, 'w', encoding='utf-8') as f:
                    json.dump(pending_chunk_data, f, ensure_ascii=False, indent=2)
                continue
        
        # Create final result
        total_time = time.time() - start_time
        total_text = " ".join([seg.text for seg in all_segments])
        
        # Group segments by speaker for TranscriptionResult
        speakers_data = {}
        for segment in all_segments:
            if segment.speaker not in speakers_data:
                speakers_data[segment.speaker] = []
            speakers_data[segment.speaker].append(segment)
        
        # Count unique speakers
        unique_speakers = len(speakers_data)
        
        result = TranscriptionResult(
            success=True,
            speakers=speakers_data,
            full_text=total_text,
            transcription_time=total_time,
            model_name=model_name,
            audio_file=audio_file_path,
            speaker_count=unique_speakers
        )
        
        logger.info(f"🎯 Audio chunk transcription completed: {total_time:.1f}s, {len(total_text)} chars, {len(all_segments)} segments")
        logger.info(f"🔧 Audio chunks saved in: {audio_chunks_dir}")
        
        return result
    
    def _process_existing_audio_chunks(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Process existing audio chunks instead of creating new ones from large file"""
        import os
        import glob
        
        # Check if audio chunks directory exists
        chunks_dir = "examples/audio/voice/audio_chunks/"
        if not os.path.exists(chunks_dir):
            logger.warning(f"⚠️ Audio chunks directory not found: {chunks_dir}")
            return self._transcribe_with_audio_chunks(audio_file_path, model_name, 120)
        
        # Find existing audio chunk files
        chunk_files = glob.glob(os.path.join(chunks_dir, "audio_chunk_*.wav"))
        chunk_files.sort()  # Sort by chunk number
        
        if not chunk_files:
            logger.warning(f"⚠️ No audio chunk files found in {chunks_dir}")
            return self._transcribe_with_audio_chunks(audio_file_path, model_name, 120)
        
        logger.info(f"🎯 Found {len(chunk_files)} existing audio chunks, processing them directly")
        logger.info(f"📁 Chunks directory: {chunks_dir}")
        
        # Process each existing chunk
        all_segments = []
        total_duration = 0.0
        start_time = time.time()
        
        for i, chunk_file in enumerate(chunk_files, 1):
            chunk_name = os.path.basename(chunk_file)
            logger.info(f"🔧 Processing existing chunk {i}/{len(chunk_files)}: {chunk_name}")
            
            try:
                # Load audio to get duration for chunk parameters
                import librosa
                audio, sr = librosa.load(chunk_file, sr=16000)
                chunk_duration = len(audio) / sr
                
                # Create chunk info for JSON file
                chunk_start = total_duration
                chunk_end = total_duration + chunk_duration
                
                # Create JSON file for this chunk
                chunk_filename = f"chunk_{i:03d}_{chunk_start:.0f}s_{chunk_end:.0f}s.json"
                chunk_filepath = os.path.join(self.temp_chunks_dir, chunk_filename)
                
                # Create initial pending chunk file
                chunk_data = {
                    "chunk_number": i,
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                    "status": "processing",
                    "created_at": time.time(),
                    "text": "",
                    "processing_started": time.time(),
                    "processing_completed": None,
                    "audio_chunk_file": chunk_name
                }
                
                with open(chunk_filepath, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"📝 Created pending chunk file: {chunk_filename}")
                
                # Transcribe this chunk
                chunk_text = self._transcribe_chunk(audio, i, chunk_start, chunk_end, model_name)
                
                if chunk_text and chunk_text.strip():
                    # Create a simple segment for this chunk (no speaker diarization per chunk)
                    segment = TranscriptionSegment(
                        start=chunk_start,
                        end=chunk_end,
                        text=chunk_text.strip(),
                        speaker="0",  # Default speaker, will be processed later
                        chunk_file=chunk_name,
                        chunk_number=i
                    )
                    all_segments.append(segment)
                    
                    # Update JSON file with completed status and text
                    chunk_data.update({
                        "status": "completed",
                        "text": chunk_text.strip(),
                        "processing_completed": time.time(),
                        "transcription_length": len(chunk_text),
                        "words_estimated": len(chunk_text.split()),
                        "speaker_count": 1,
                        "note": "Speaker diarization will be applied to full result"
                    })
                    
                    with open(chunk_filepath, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"✅ Chunk {i} completed: {chunk_duration:.1f}s, text length: {len(chunk_text)}")
                    
                    total_duration += chunk_duration
                else:
                    logger.warning(f"⚠️ Chunk {i} returned no text")
                    # Update JSON file with error status
                    chunk_data.update({
                        "status": "error",
                        "error_message": "No text returned from transcription"
                    })
                    
                    with open(chunk_filepath, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                logger.error(f"❌ Error processing chunk {i} ({chunk_name}): {e}")
                # Update JSON file with error status if it was created
                if 'chunk_filepath' in locals() and 'chunk_data' in locals():
                    chunk_data.update({
                        "status": "error",
                        "error_message": str(e)
                    })
                    
                    with open(chunk_filepath, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, indent=2, ensure_ascii=False)
                continue
        
        if not all_segments:
            logger.error("❌ No segments were processed successfully")
            # Return a failed result instead of None
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message="No segments were processed successfully"
            )
        
        # Group segments by speaker
        speakers_dict = {}
        for segment in all_segments:
            speaker = getattr(segment, 'speaker', f"speaker_{segment.chunk_number}")
            if speaker not in speakers_dict:
                speakers_dict[speaker] = []
            speakers_dict[speaker].append(segment)
        
        # Create final result
        final_result = TranscriptionResult(
            success=True,
            speakers=speakers_dict,
            full_text=" ".join([seg.text for seg in all_segments]),
            transcription_time=time.time() - start_time,
            model_name=model_name,
            audio_file=audio_file_path,
            speaker_count=len(speakers_dict)
        )
        
        logger.info(f"🎉 Successfully processed {len(chunk_files)} existing chunks")
        logger.info(f"📊 Total segments: {len(all_segments)}")
        logger.info(f"⏱️ Total duration: {total_duration:.1f}s")
        logger.info(f"🗣️ Speakers detected: {len(speakers_dict)}")
        
        return final_result
    
    def _cleanup_logs(self):
        """Clean up log files before starting new transcription"""
        if not self.cleanup_logs_before_run:
            return
            
        try:
            # Clear console output by printing separator
            print("\n" + "="*80)
            print("🧹 NEW TRANSCRIPTION SESSION STARTING")
            print("="*80 + "\n")
            
            # Clear common log files if they exist
            log_files = [
                "output/transcription.log",
                "output/error.log", 
                "output/debug.log",
                "output/progress.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    # Truncate log file instead of deleting
                    with open(log_file, 'w') as f:
                        f.write(f"# Log cleared at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"# New transcription session: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("="*80 + "\n\n")
                    logger.debug(f"🧹 Cleared log file: {log_file}")
            
            # Clear output directory of old files (optional)
            output_dir = "output"
            if os.path.exists(output_dir):
                # Keep only the last N transcription files based on config
                transcription_files = []
                for file in os.listdir(output_dir):
                    if file.endswith(('.txt', '.json', '.docx')) and 'transcription' in file.lower():
                        file_path = os.path.join(output_dir, file)
                        transcription_files.append((file_path, os.path.getmtime(file_path)))
                
                # Sort by modification time and remove old ones
                transcription_files.sort(key=lambda x: x[1], reverse=True)
                for file_path, _ in transcription_files[self.max_output_files:]:
                    try:
                        os.remove(file_path)
                        logger.debug(f"🧹 Removed old file: {file_path}")
                    except Exception as e:
                        logger.debug(f"⚠️ Could not remove old file {file_path}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Log cleanup error: {e}")
    
    def cleanup_logs_manually(self, clear_console=True, clear_files=True, clear_output=True):
        """
        Manually trigger log cleanup
        
        Args:
            clear_console: Whether to clear console output
            clear_files: Whether to clear log files
            clear_output: Whether to clean old output files
        """
        if clear_console:
            print("\n" + "="*80)
            print("🧹 MANUAL LOG CLEANUP")
            print("="*80 + "\n")
        
        if clear_files:
            self._cleanup_logs()
        
        if clear_output:
            self._cleanup_output_files()
    
    def _cleanup_output_files(self):
        """Clean up old output files"""
        try:
            output_dir = "output"
            if not os.path.exists(output_dir):
                return
                
            # Keep only the last N transcription files based on config
            transcription_files = []
            for file in os.listdir(output_dir):
                if file.endswith(('.txt', '.json', '.docx')) and 'transcription' in file.lower():
                    file_path = os.path.join(output_dir, file)
                    transcription_files.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time and remove old ones
            transcription_files.sort(key=lambda x: x[1], reverse=True)
            removed_count = 0
            for file_path, _ in transcription_files[self.max_output_files:]:
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    logger.debug(f"⚠️ Could not remove old file {file_path}: {e}")
            
            if removed_count > 0:
                logger.info(f"🧹 Cleaned up {removed_count} old output files")
                
        except Exception as e:
            logger.warning(f"⚠️ Output cleanup error: {e}")
    
    def get_cleanup_stats(self):
        """Get statistics about cleanup configuration and status"""
        stats = {
            "cleanup_enabled": self.cleanup_logs_before_run,
            "max_output_files": self.max_output_files,
            "temp_dir": self.temp_chunks_dir,
            "temp_dir_exists": os.path.exists(self.temp_chunks_dir)
        }
        
        # Count output files
        output_dir = "output"
        if os.path.exists(output_dir):
            transcription_files = []
            for file in os.listdir(output_dir):
                if file.endswith(('.txt', '.json', '.docx')) and 'transcription' in file.lower():
                    file_path = os.path.join(output_dir, file)
                    transcription_files.append((file_path, os.path.getmtime(file_path)))
            
            stats["current_output_files"] = len(transcription_files)
            stats["output_files_to_clean"] = max(0, len(transcription_files) - self.max_output_files)
        
        return stats
    
    def _cleanup_temp_files(self):
        """Clean up temporary files created during processing"""
        try:
            if os.path.exists(self.temp_chunks_dir):
                import shutil
                shutil.rmtree(self.temp_chunks_dir)
                logger.debug(f"🧹 Cleaned temp directory: {self.temp_chunks_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup error: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        try:
            self._cleanup_temp_files()
        except Exception as e:
            logger.warning(f"⚠️ Cleanup error: {e}")
        return False  # Re-raise any exceptions
