#!/usr/bin/env python3
"""
Direct Transcription Strategy
Handles transcription of small files without chunking
"""

import logging
import time
from typing import TYPE_CHECKING, Optional, Dict, Any

from src.core.engines.strategies.base_strategy import BaseTranscriptionStrategy
from src.models.transcription_results import TranscriptionResult, TranscriptionSegment

if TYPE_CHECKING:
    from src.core.engines.base_interface import TranscriptionEngine

logger = logging.getLogger(__name__)


class DirectTranscriptionStrategy(BaseTranscriptionStrategy):
    """Strategy for direct transcription of small files"""
    
    def __init__(self, config_manager):
        """Initialize the strategy with ConfigManager dependency injection"""
        super().__init__(config_manager)
    
    def execute(self, audio_file_path: str, model_name: str, engine: 'TranscriptionEngine', chunk_info: Optional[Dict[str, Any]] = None) -> TranscriptionResult:
        """Execute direct transcription strategy"""
        logger.info(f"🎯 Using DirectTranscriptionStrategy for: {audio_file_path}")
        
        try:
            audio_data, sample_rate = self._load_audio(audio_file_path)
            
            # Direct strategy processes single files - no need for overlapping JSON structure
            # Overlapping JSON is only needed for chunked transcription strategies
            
            # If chunk_info is provided, use it for proper chunk numbering
            if chunk_info:
                chunk_number = chunk_info.get('chunk_number', 1)
                chunk_start = chunk_info.get('start', 0)
                chunk_end = chunk_info.get('end', len(audio_data) / sample_rate)
                chunk_result = self._transcribe_audio_with_chunk_info(audio_data, sample_rate, engine, model_name, 
                                                                   chunk_number, chunk_start, chunk_end)
            else:
                # Fallback to default behavior
                chunk_result = self._transcribe_audio(audio_data, sample_rate, engine, model_name)
            
            # Now _transcribe_chunk returns TranscriptionResult, so we can use it directly
            if chunk_result and chunk_result.success:
                logger.info("✅ Voice-to-text transcription completed successfully")
                
                # First: Complete the voice-to-text transcription
                # Save the basic transcription result first
                self._save_basic_transcription_result(audio_file_path, chunk_result, chunk_info)
                
                # Then: Apply speaker recognition enhancement (separate process)
                logger.info("🎤 Starting speaker recognition process...")
                enhanced_result = self._enhance_with_speaker_recognition(chunk_result, audio_file_path, chunk_info)
                if enhanced_result:
                    logger.info("✅ Speaker recognition applied successfully")
                    # Update the JSON with speaker recognition data
                    self._update_json_with_speaker_recognition(audio_file_path, enhanced_result)
                    return enhanced_result
                else:
                    logger.info("ℹ️ Speaker recognition not available, using basic result")
                    return chunk_result
            else:
                raise ValueError("No transcription result produced or transcription failed")
                
        except Exception as e:
            logger.error(f"❌ Error in direct transcription: {e}")
            raise
    
    def _load_audio(self, audio_file_path: str):
        """Load audio file"""
        import librosa
        return librosa.load(audio_file_path, sr=16000, mono=True)
    
    def _transcribe_audio(self, audio_data, sample_rate, engine, model_name: str) -> 'TranscriptionResult':
        """Transcribe audio data - now returns TranscriptionResult"""
        start_time = time.time()
        return engine._transcribe_chunk(audio_data, 1, 0, len(audio_data) / sample_rate, model_name)
    
    def _transcribe_audio_with_chunk_info(self, audio_data, sample_rate, engine, model_name: str, 
                                        chunk_number: int, chunk_start: float, chunk_end: float) -> 'TranscriptionResult':
        """Transcribe audio data with proper chunk information"""
        start_time = time.time()
        return engine._transcribe_chunk(audio_data, chunk_number, chunk_start, chunk_end, model_name)
    
    def _create_result(self, audio_data, sample_rate, chunk_text: str, model_name: str, audio_file_path: str) -> TranscriptionResult:
        """Create transcription result"""
        # Check if speaker logic is enabled
        if self._is_speaker_diarization_enabled():
            segment = TranscriptionSegment(start=0, end=len(audio_data) / sample_rate, text=chunk_text, speaker="0")
            return TranscriptionResult(
                success=True, text=chunk_text, speakers={"0": [segment]}, full_text=chunk_text,
                transcription_time=0.0, model_name=model_name, audio_file=audio_file_path, speaker_count=1
            )
        else:
            # Create result without speaker information when speaker logic is disabled
            segment = TranscriptionSegment(start=0, end=len(audio_data) / sample_rate, text=chunk_text)
            return TranscriptionResult(
                success=True, text=chunk_text, segments=[segment], full_text=chunk_text,
                transcription_time=0.0, model_name=model_name, audio_file=audio_file_path, speaker_count=0
            )
    
    def _create_metadata(self, model_name: str, engine: str, audio_file: str, processing_time: float):
        """Create metadata for TranscriptionResult"""
        from src.models.transcription_results import TranscriptionMetadata
        return TranscriptionMetadata(
            model_name=model_name,
            engine=engine,
            language="he",
            processing_time=processing_time,
            audio_duration=None,
            sample_rate=None,
            channels=None,
            file_size=None
        )
    
    def _enhance_with_speaker_recognition(self, transcription_result: 'TranscriptionResult', audio_file_path: str, chunk_info: Optional[Dict[str, Any]] = None) -> Optional['TranscriptionResult']:
        """Enhance transcription result with speaker recognition if enabled"""
        logger.info("🎤 _enhance_with_speaker_recognition called - starting speaker recognition process")
        try:
            # Check if speaker diarization is enabled
            if not self._is_speaker_diarization_enabled():
                logger.info("ℹ️ Speaker diarization disabled in configuration - skipping enhancement")
                # Return None to signal no enhancement was performed
                return None
            
            # Initialize speaker service if not already done
            if not hasattr(self, '_speaker_service'):
                self._initialize_speaker_service()
            
            if not self._speaker_service:
                logger.info("ℹ️ Speaker service not available")
                return None
            
            logger.info("🎤 Applying speaker recognition to transcription result")
            
            # Use speaker service to analyze the audio file with transcription text
            transcription_text = transcription_result.text if hasattr(transcription_result, 'text') and transcription_result.text else ""
            if not transcription_text and hasattr(transcription_result, 'transcription_data') and transcription_result.transcription_data:
                transcription_text = transcription_result.transcription_data.text if hasattr(transcription_result.transcription_data, 'text') else ""
            
            logger.info(f"🎤 Calling speaker service with transcription text length: {len(transcription_text)}")
            speaker_result = self._speaker_service.speaker_diarization(audio_file_path, transcription_text)
            
            if not speaker_result or not speaker_result.success:
                logger.warning("⚠️ Speaker recognition failed, using basic result")
                return None
            
            # Merge speaker information with transcription result
            enhanced_result = self._merge_speaker_and_transcription(transcription_result, speaker_result, chunk_info)
            
            logger.info(f"✅ Speaker recognition completed: {enhanced_result.speaker_count} speakers detected")
            
            # Enhanced JSON will be updated by the calling method
            # No need to save here since we're using the new flow
            
            return enhanced_result
            
        except Exception as e:
            logger.warning(f"⚠️ Speaker recognition enhancement failed: {e}")
            return None
    
    def _is_speaker_diarization_enabled(self) -> bool:
        """Check if speaker diarization is enabled based on config"""
        try:
            # Check for 'speaker' field first (this is what the config actually has)
            if hasattr(self.config_manager.config, 'speaker') and self.config_manager.config.speaker:
                speaker_config = self.config_manager.config.speaker
                # Check for disable_completely flag first
                if hasattr(speaker_config, 'disable_completely') and speaker_config.disable_completely:
                    logger.info("🎤 Speaker diarization completely disabled in configuration")
                    return False
                # Then check for enabled flag
                if hasattr(speaker_config, 'enabled'):
                    enabled = speaker_config.enabled
                    logger.info(f"🎤 Speaker diarization enabled: {enabled}")
                    return enabled
                logger.info("🎤 Speaker diarization enabled (default)")
                return True  # Default to enabled if no explicit flag
            # Fallback to 'speaker_diarization' field (legacy)
            elif hasattr(self.config_manager.config, 'speaker_diarization'):
                speaker_config = self.config_manager.config.speaker_diarization
                # Check for disable_completely flag first
                if hasattr(speaker_config, 'disable_completely') and speaker_config.disable_completely:
                    logger.info("🎤 Speaker diarization completely disabled in configuration (legacy)")
                    return False
                # Then check for enabled flag
                if hasattr(speaker_config, 'enabled'):
                    enabled = speaker_config.enabled
                    logger.info(f"🎤 Speaker diarization enabled (legacy): {enabled}")
                    return enabled
                logger.info("🎤 Speaker diarization enabled (legacy, default)")
                return True  # Default to enabled if no explicit flag
            logger.info("🎤 Speaker diarization enabled (global default)")
            return True  # Default to enabled
        except Exception as e:
            logger.warning(f"⚠️ Error checking speaker diarization config: {e}")
            return True  # Default to enabled
    
    def _initialize_speaker_service(self):
        """Initialize speaker service - fail fast if initialization fails"""
        try:
            if not self._is_speaker_diarization_enabled():
                logger.info("ℹ️ Speaker diarization disabled in configuration")
                return
            
            logger.info("🎤 Initializing speaker service...")
            
            # Create OutputManager for speaker service
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
            from src.core.factories.speaker_service_factory import SpeakerServiceFactory
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
    
    def _merge_speaker_and_transcription(self, transcription_result: 'TranscriptionResult', speaker_result: 'TranscriptionResult', chunk_info: Optional[Dict[str, Any]] = None) -> 'TranscriptionResult':
        """Merge speaker recognition results with transcription results"""
        try:
            # Extract text from transcription result
            text = getattr(transcription_result, 'text', '') or getattr(transcription_result, 'full_text', '')
            
            # Get speaker information from speaker result
            speakers = getattr(speaker_result, 'speakers', {})
            speaker_count = getattr(speaker_result, 'speaker_count', 0)
            
            # If no speakers detected, create a default speaker
            if not speakers or speaker_count == 0:
                from src.models.transcription_results import TranscriptionSegment
                default_segment = TranscriptionSegment(
                    text=text,
                    start=0.0,
                    end=1.0,
                    speaker="Speaker_1"
                )
                speakers = {"Speaker_1": [default_segment]}
                speaker_count = 1
            
            # Create merged result using the new model structure
            merged_result = TranscriptionResult(
                success=True,
                text=text,
                segments=transcription_result.segments if hasattr(transcription_result, 'segments') else [],
                speakers=speakers,
                speaker_count=speaker_count,
                metadata=transcription_result.metadata if hasattr(transcription_result, 'metadata') else None,
                word_timestamps=getattr(transcription_result, 'word_timestamps', None),
                language_detection=getattr(transcription_result, 'language_detection', None),
                confidence_scores=getattr(transcription_result, 'confidence_scores', None),
                raw_output=getattr(transcription_result, 'raw_output', None)
            )
            
            # Set audio file for backward compatibility
            if hasattr(transcription_result, 'audio_file'):
                merged_result.set_audio_file(transcription_result.audio_file)
            
            logger.info(f"✅ Successfully merged speaker recognition: {speaker_count} speakers")
            return merged_result
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to merge speaker recognition: {e}")
            # Return original transcription result if merging fails
            return transcription_result
    
    # Old method removed - replaced with separate _save_basic_transcription_result and _update_json_with_speaker_recognition
    
    def _save_basic_transcription_result(self, audio_file_path: str, transcription_result: 'TranscriptionResult', chunk_info: Optional[Dict[str, Any]] = None) -> None:
        """Save basic transcription result (voice-to-text only) to a simple JSON file"""
        try:
            import os
            import json
            import time
            from pathlib import Path
            
            # Create output directory for chunk results
            output_dir = "output/chunk_results"
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract filename from audio path and create a chunk-style JSON filename
            audio_filename = Path(audio_file_path).stem
            
            # Convert audio_chunk_001_0s_30s.wav to chunk_001_0s_30s.json
            if audio_filename.startswith('audio_chunk_'):
                json_filename = f"chunk_{audio_filename[12:]}.json"  # Remove 'audio_' prefix
            else:
                json_filename = f"{audio_filename}.json"
                
            json_path = os.path.join(output_dir, json_filename)
            
            # Extract text content
            text = getattr(transcription_result, 'text', '') or getattr(transcription_result, 'full_text', '')
            segments = getattr(transcription_result, 'segments', [])
            
            # Create simple JSON data for single file transcription
            json_data = {
                'file_name': audio_filename,
                'status': 'transcription_completed',
                'text': text,
                'processing_completed': time.time(),
                'enhancement_applied': False,
                'enhancement_strategy': 'voice_to_text_only',
                'transcription_length': len(text),
                'words_estimated': len(text.split()) if text else 0,
                'progress': {
                    'stage': 'transcription_completed',
                    'message': f'Voice-to-text transcription completed successfully',
                    'timestamp': time.time()
                },
                
                # Basic transcription data (no speaker recognition)
                'transcription_data': {
                    'text': text,
                    'segments': [
                        {
                            'start': getattr(seg, 'start', 0.0),
                            'end': getattr(seg, 'end', 0.0),
                            'text': getattr(seg, 'text', ''),
                            'duration': getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                        }
                        for seg in segments
                    ] if segments else [],
                    'language': 'he',
                    'confidence': 0.95
                }
            }
            
            # Add segments field for compatibility (without speaker information)
            json_data['segments'] = [
                {
                    'start': getattr(seg, 'start', 0.0),
                    'end': getattr(seg, 'end', 0.0),
                    'text': getattr(seg, 'text', ''),
                    'duration': getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                }
                for seg in segments
            ] if segments else []
            
            # Save JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Saved basic transcription result (voice-to-text): {json_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving basic transcription result: {e}")
    
    def _update_json_with_speaker_recognition(self, audio_file_path: str, enhanced_result: 'TranscriptionResult') -> None:
        """Update existing JSON with speaker recognition data (separate from transcription)"""
        try:
            import os
            import json
            import time
            from pathlib import Path
            
            # Find the existing JSON file for this audio file
            output_dir = "output/chunk_results"
            audio_filename = Path(audio_file_path).stem
            
            # Convert audio_chunk_001_0s_30s.wav to chunk_001_0s_30s.json
            if audio_filename.startswith('audio_chunk_'):
                json_filename = f"chunk_{audio_filename[12:]}.json"  # Remove 'audio_' prefix
            else:
                json_filename = f"{audio_filename}.json"
                
            json_path = os.path.join(output_dir, json_filename)
            
            if not os.path.exists(json_path):
                logger.warning(f"⚠️ Expected JSON file not found: {json_filename}")
                return
            
            # Read existing JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract speaker information
            speakers = getattr(enhanced_result, 'speakers', {})
            speaker_count = getattr(enhanced_result, 'speaker_count', 0)
            segments = getattr(enhanced_result, 'segments', [])
            
            # Respect configuration: if speaker diarization is disabled, do not add speaker data
            if not self._is_speaker_diarization_enabled():
                logger.info("ℹ️ Speaker diarization disabled - not updating JSON with speaker data")
                # Ensure enhancement flags remain voice_to_text_only
                json_data.update({
                    'status': 'transcription_completed',
                    'enhancement_applied': False,
                    'enhancement_strategy': 'voice_to_text_only',
                })
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                return

            # Update existing JSON with speaker recognition data (separate process)
            json_data.update({
                'status': 'completed',
                'enhancement_applied': True,
                'enhancement_strategy': 'fast_speaker_service',
                'progress': {
                    'stage': 'completed',
                    'message': f'Speaker recognition completed successfully with {speaker_count} speakers detected',
                    'timestamp': time.time()
                },
                
                # 🎯 Speaker Recognition Data (added after transcription)
                'speaker_recognition': {
                    'total_speakers': speaker_count,
                    'speaker_names': list(speakers.keys()) if speakers else [],
                    'speaker_details': {}
                },
                
                # 🎯 Enhanced Segments with Speaker Info (updated after transcription)
                'segments': [
                    {
                        'start': getattr(seg, 'start', 0.0),
                        'end': getattr(seg, 'end', 0.0),
                        'text': getattr(seg, 'text', ''),
                        'speaker': getattr(seg, 'speaker', 'unknown'),
                        'duration': getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                    }
                    for seg in segments
                ] if segments else [],
                
                # 🎯 Processing Type and Language
                'processing_type': 'enhanced_with_fast_speaker_service',
                'language': 'he',
                'confidence': 0.95
            })
            
            # Add speaker details
            if speakers:
                for speaker_id, speaker_segments in speakers.items():
                    if speaker_segments:
                        total_duration = sum(
                            getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0) 
                            for seg in speaker_segments
                        )
                        json_data['speaker_recognition']['speaker_details'][speaker_id] = {
                            'segment_count': len(speaker_segments),
                            'total_duration': total_duration,
                            'segments': [
                                {
                                    'start': getattr(seg, 'start', 0.0),
                                    'end': getattr(seg, 'end', 0.0),
                                    'text': getattr(seg, 'text', ''),
                                    'duration': getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                                }
                                for seg in speaker_segments
                            ]
                        }
            
            # Save updated JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"🎤 Updated JSON with speaker recognition data: {json_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error updating JSON with speaker recognition: {e}")
    

    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return "DirectTranscriptionStrategy"
