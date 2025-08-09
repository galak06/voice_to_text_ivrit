#!/usr/bin/env python3
"""
Core transcription service
Handles the main transcription logic and orchestration
"""

from typing import Dict, Any, Generator, Optional, List, TYPE_CHECKING
from src.core.factories.engine_factory import TranscriptionEngineFactory
from src.core.logic.job_validator import JobValidator
from src.core.processors.audio_file_processor import AudioFileProcessor
from src.utils.config_manager import ConfigManager
import logging

if TYPE_CHECKING:
    from src.output_data import OutputManager

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Core transcription service that orchestrates the transcription process"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, output_manager: Optional['OutputManager'] = None, max_payload_size: int = 200 * 1024 * 1024):
        """
        Initialize transcription service
        
        Args:
            config_manager: Configuration manager for service settings
            output_manager: Output manager instance (injected for consistency)
            max_payload_size: Maximum payload size in bytes
        """
        self.config_manager = config_manager
        
        # Use config payload size if available
        if config_manager and config_manager.config.system:
            max_payload_size = getattr(config_manager.config.system, 'max_payload_size', max_payload_size)
        
        self.validator = JobValidator(self.config_manager.config)
        self.engine_factory = TranscriptionEngineFactory()
        self.output_manager = output_manager
        if self.output_manager is None:
            from src.output_data import OutputManager
            self.output_manager = OutputManager()
        
        from src.core.processors.audio_file_processor import AudioFileProcessor
        self.audio_processor = AudioFileProcessor(self.config_manager, self.output_manager)
    
    def transcribe(self, job: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Main transcription function following Single Responsibility Principle.
        Orchestrates the transcription process by delegating to specialized functions.
        
        Args:
            job: The job dictionary containing input parameters
            
        Yields:
            Transcription segments or error messages
        """
        # Validate input parameters
        validation_error = self.validator.validate_job_input(job)
        if validation_error:
            yield {"error": validation_error}
            return
        
        # Extract and validate parameters
        job_params = self._extract_job_parameters(job)
        if not job_params:
            yield {"error": "Invalid job parameters"}
            return
        
        # Prepare audio file
        temp_dir, audio_file = self.audio_processor.prepare_audio_file(job)
        if temp_dir is None:
            yield {"error": audio_file}  # audio_file contains error message
            return
        
        # Ensure audio_file is not None before proceeding
        if audio_file is None:
            yield {"error": "Failed to prepare audio file"}
            return
        
        # Perform transcription
        try:
            result = self._execute_transcription(job_params, audio_file)
            
            if job_params['is_streaming']:
                for entry in result:
                    yield entry
            else:
                # Save output if requested
                if job_params['save_output'] and result:
                    self._save_transcription_output(result, audio_file, job_params, job.get('session_id'))
                
                yield {'result': result}
        finally:
            # Clean up temporary files
            if temp_dir:
                try:
                    self.audio_processor.cleanup_temp_files(temp_dir)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary files: {cleanup_error}")
    
    def transcribe_core(self, engine: str, model_name: str, audio_file: str) -> Generator[Dict[str, Any], None, None]:
        """
        Core transcription function using Strategy Pattern for engine selection.
        Follows Open/Closed Principle - open for extension, closed for modification.
        
        Args:
            engine: The transcription engine to use
            model_name: The model name to use
            audio_file: Path to the audio file
            
        Yields:
            Transcription segments
        """
        # Use Strategy Pattern to get the appropriate engine
        from src.core.factories.speaker_config_factory import SpeakerConfigFactory
        speaker_config = SpeakerConfigFactory.get_config('default')
        
        if engine == 'stable-whisper':
            from src.core.engines import StableWhisperEngine
            transcription_engine = StableWhisperEngine(speaker_config, self.config_manager.config)
        elif engine == 'custom-whisper':
            from src.core.engines import CustomWhisperEngine
            transcription_engine = CustomWhisperEngine(speaker_config, self.config_manager.config)
        elif engine == 'ctranslate2-whisper':
            from src.core.engines import OptimizedWhisperEngine
            transcription_engine = OptimizedWhisperEngine(speaker_config, self.config_manager.config)
        else:
            raise ValueError(f"Unsupported engine: {engine}")
        
        # Perform transcription using the selected engine
        result = transcription_engine.transcribe(audio_file, model_name)
        
        if not result.success:
            yield {"error": f"Transcription failed: {result.error_message}"}
            return
        
        # Convert result to segments format
        segs_list = []
        for speaker, segments in result.speakers.items():
            for segment in segments:
                segs_list.append(segment)
            
            # Process segments
            for i, s in enumerate(segs_list):
                words = []
                for w in s.words:
                    words.append({
                        'start': w.start,
                        'end': w.end,
                        'word': w.word,
                        'probability': w.probability
                    })
                
                seg = {
                    'id': s.id,
                    'seek': s.seek,
                    'start': s.start,
                    'end': s.end,
                    'text': s.text,
                    'avg_logprob': s.avg_logprob,
                    'compression_ratio': s.compression_ratio,
                    'no_speech_prob': s.no_speech_prob,
                    'words': words
                }
                
                yield seg 
    
    def _extract_job_parameters(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate job parameters
        
        Args:
            job: The job dictionary
            
        Returns:
            Dictionary with extracted parameters or None if invalid
        """
        try:
            input_data = job.get('input', {})
            return {
                'engine': input_data.get('engine', 'speaker-diarization'),
                'model_name': input_data.get('model', 'large-v2'),
                'is_streaming': input_data.get('streaming', False),
                'save_output': input_data.get('save_output', True)
            }
        except Exception as e:
            logger.error(f"Error extracting job parameters: {e}")
            return None
    
    def _execute_transcription(self, job_params: Dict[str, Any], audio_file: str) -> List[Dict[str, Any]]:
        """
        Execute the transcription process
        
        Args:
            job_params: Extracted job parameters
            audio_file: Path to the audio file
            
        Returns:
            List of transcription results
        """
        stream_gen = self.transcribe_core(job_params['engine'], job_params['model_name'], audio_file)
        return [entry for entry in stream_gen]
    
    def _save_transcription_output(self, result: List[Dict[str, Any]], audio_file: str, 
                                 job_params: Dict[str, Any], session_id: str = None):
        """
        Save transcription output in all formats
        
        Args:
            result: Transcription results
            audio_file: Path to the audio file
            job_params: Job parameters
            session_id: Optional session ID
        """
        try:
            saved_files = self.output_manager.save_transcription(
                transcription_data=result,
                audio_file=audio_file,
                model=job_params['model_name'],
                engine=job_params['engine'],
                session_id=session_id
            )
            logger.info(f"Transcription completed and saved for {audio_file}")
        except Exception as e:
            logger.error(f"Failed to save output: {e}") 