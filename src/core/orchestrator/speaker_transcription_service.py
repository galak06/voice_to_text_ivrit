#!/usr/bin/env python3
"""
Speaker Transcription Service for ivrit-ai models
Handles speaker diarization with configurable parameters
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, List

from src.models.speaker_models import SpeakerConfig, TranscriptionResult, SpeakerDiarizationRequest
from src.core.factories.engine_factory import TranscriptionEngineFactory
from src.core.factories.file_validator_factory import FileValidatorFactory
from src.models import AppConfig
from src.core.logic.result_builder import ResultBuilder

logger = logging.getLogger(__name__)

class SpeakerTranscriptionService:
    """
    Service for transcribing audio with speaker diarization
    Uses Strategy Pattern for different transcription engines
    """
    
    def __init__(self, config: Optional[SpeakerConfig] = None, app_config: Optional[AppConfig] = None, output_manager: Optional['OutputManager'] = None):
        """
        Initialize the speaker transcription service
        
        Args:
            config: Speaker configuration (uses defaults if None)
            app_config: Application configuration (uses defaults if None)
            output_manager: Output manager instance (uses default if None)
        """
        from src.models import AppConfig
        
        self.config = config or SpeakerConfig()
        self.app_config = app_config or AppConfig()
        
        # Import OutputManager only when needed to avoid circular imports
        if output_manager is None:
            from src.output_data import OutputManager
            self.output_manager = OutputManager()
        else:
            self.output_manager = output_manager
        
        # Use the unified FileValidator for file validation
        self.file_validator = FileValidatorFactory.create_audio_validator(self.app_config)
    
    def speaker_diarization(
        self, 
        audio_file_path: str, 
        model_name: str = None,
        save_output: bool = True,
        run_session_id: str = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file with speaker diarization
        
        Args:
            audio_file_path: Path to the audio file
            model_name: Model to use for transcription
            save_output: Whether to save outputs in all formats
            
        Returns:
            TranscriptionResult with speaker-separated data
        """
        # Create request object for validation
        request = SpeakerDiarizationRequest(
            audio_file_path=audio_file_path,
            model_name=model_name,
            save_output=save_output,
            run_session_id=run_session_id,
            speaker_config=self.config
        )
        
        return self._process_diarization_request(request)
    
    def _process_diarization_request(self, request: SpeakerDiarizationRequest) -> TranscriptionResult:
        """Process a speaker diarization request"""
        start_time = time.time()
        logger.info(f"Starting diarization for: {request.audio_file_path}")
        
        # Validate audio file
        if not self._validate_audio_file(request.audio_file_path):
            return self._create_error_result(request, start_time, "Invalid audio file")
        
        # Determine model name
        model_name = self._determine_model_name(request)
        
        try:
            # Determine engine type based on file size
            engine_type = self._determine_engine_type(request.audio_file_path)
            
            # Perform transcription
            result = self._transcribe_with_engine(engine_type, request.audio_file_path, model_name)
            
            if result.success:
                logger.info(f"Transcription successful")
                
                # Save outputs if requested
                if request.save_output:
                    self._save_outputs(result, request.audio_file_path, model_name, request.run_session_id)
                
                return result
            
            # Transcription failed
            logger.error(f"Transcription failed")
            return self._create_error_result(request, start_time, "Transcription engine failed")
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return self._create_error_result(request, start_time, str(e))
    
    def _determine_model_name(self, request: SpeakerDiarizationRequest) -> str:
        """Determine the model name to use"""
        if request.model_name is not None:
            return request.model_name
        return self.app_config.transcription.default_model
    
    def _determine_engine_type(self, audio_file_path: str) -> str:
        """Determine engine type based on file size"""
        file_size = Path(audio_file_path).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Get constants from configuration
        constants = self.config.system.constants if self.config.system else None
        large_file_threshold = constants.large_file_threshold_mb if constants else 100
        
        if file_size_mb > large_file_threshold:
            logger.info(f"📁 Large file detected ({file_size_mb:.1f}MB), using custom-whisper with chunking")
            return "custom-whisper"
        else:
            logger.info(f"📁 Small file detected ({file_size_mb:.1f}MB), using stable-whisper")
            return "stable-whisper"
    
    def _create_error_result(self, request: SpeakerDiarizationRequest, start_time: float, 
                           error_message: str) -> TranscriptionResult:
        """Create error result with consistent format"""
        return TranscriptionResult(
            success=False,
            speakers={},
            full_text="",
            transcription_time=time.time() - start_time,
            model_name=request.model_name or "unknown",
            audio_file=request.audio_file_path,
            speaker_count=0,
            error_message=error_message
        )
    
    def _transcribe_with_engine(self, engine_type: str, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using a specific engine"""
        try:
            engine = TranscriptionEngineFactory.create_engine(engine_type, self.config)
            return engine.transcribe(audio_file_path, model_name)
        except Exception as e:
            logger.error(f"Error creating {engine_type} engine: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=f"Failed to create {engine_type} engine: {str(e)}"
            )
    
    def _validate_audio_file(self, audio_file_path: str) -> bool:
        """
        Validate audio file exists and is accessible using the unified FileValidator
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            True if file is valid, False otherwise
        """
        # Use the unified FileValidator for comprehensive validation
        validation_result = self.file_validator.validate_audio_file(audio_file_path)
        
        if not validation_result['valid']:
            logger.error(f"Audio file validation failed: {validation_result['error']}")
            return False
        
        # Log file information for debugging
        logger.info(f"Audio file: {audio_file_path} ({validation_result['file_size']:,} bytes)")
        return True
    
    def _save_outputs(
        self, 
        result: TranscriptionResult, 
        audio_file_path: str, 
        model_name: str,
        run_session_id: str = None
    ):
        """Save transcription outputs in all formats"""
        try:
            # Convert TranscriptionResult to the format expected by OutputManager
            # The OutputManager expects a dictionary with 'speakers' key
            transcription_data = {
                'speakers': {speaker: [seg.model_dump() for seg in segments] for speaker, segments in result.speakers.items()},
                'full_text': result.full_text,
                'model_name': result.model_name,
                'audio_file': result.audio_file,
                'transcription_time': result.transcription_time,
                'speaker_count': result.speaker_count
            }
            
            # Use the injected output manager
            saved_files = self.output_manager.save_transcription(
                transcription_data=transcription_data,
                audio_file=audio_file_path,
                model=model_name,
                engine="speaker-diarization",
                session_id=run_session_id
            )
            
            logger.info(f"All formats saved:")
            for format_type, file_path in saved_files.items():
                logger.info(f"  📄 {format_type.upper()}: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to save outputs: {e}")
            # Log more details about the error
            import traceback
            logger.error(f"Error details: {traceback.format_exc()}")
    
    def _format_conversation_text(self, speakers: Dict[str, List]) -> str:
        """Format speaker segments into a readable conversation format"""
        if not speakers:
            return "No transcription data available."
        
        # Collect all segments with timing information
        all_segments = []
        for speaker, segments in speakers.items():
            for segment in segments:
                all_segments.append({
                    'speaker': speaker,
                    'start': float(segment.start),
                    'end': float(segment.end),
                    'text': str(segment.text).strip()
                })
        
        # Sort by start time
        all_segments.sort(key=lambda x: x['start'])
        
        # Format conversation
        conversation_lines = []
        for i, segment in enumerate(all_segments):
            # Format timestamp
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            
            # Format speaker and text
            speaker_name = segment['speaker']
            text = segment['text']
            
            # Add conversation line
            conversation_lines.append(f"[{start_time} - {end_time}] {speaker_name}: {text}")
            
            # Add separator between segments if there's a gap
            if i < len(all_segments) - 1:
                next_segment = all_segments[i + 1]
                gap = next_segment['start'] - segment['end']
                if gap > 2.0:  # Add separator for gaps longer than 2 seconds
                    conversation_lines.append("")
        
        return "\n".join(conversation_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def display_results(self, result: TranscriptionResult):
        """Display transcription results in a formatted way"""
        if not result.success:
            logger.error(f"Transcription failed: {result.error_message}")
            return
        
        logger.info("Speaker-separated transcription completed successfully")
        logger.info(f"Transcription time: {result.transcription_time:.2f} seconds")
        logger.info(f"Detected speakers: {result.speaker_count}")
        logger.info(f"Model used: {result.model_name}")
        
        # Log speaker information
        for speaker, segments in result.speakers.items():
            logger.info(f"Speaker {speaker}: {len(segments)} segments")
        
        logger.info(f"Full transcription length: {len(result.full_text)} characters")
    
    def get_available_engines(self) -> list:
        """Get list of available transcription engines"""
        return TranscriptionEngineFactory.get_available_engines(self.config) 