"""
Transcription Orchestrator
Coordinates the transcription process using various transcription services
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.output_data import OutputManager
from src.core.transcription_service import TranscriptionService
from src.core.speaker_transcription_service import SpeakerTranscriptionService


logger = logging.getLogger(__name__)

class TranscriptionOrchestrator:
    """
    Orchestrates the transcription process
    
    This class follows the Single Responsibility Principle by coordinating
    transcription operations while delegating specific transcription tasks
    to specialized services.
    """
    
    def __init__(self, config: Any, output_manager: OutputManager):
        """
        Initialize the transcription orchestrator
        
        Args:
            config: Application configuration
            output_manager: Output manager instance
        """
        self.config = config
        self.output_manager = output_manager
        # Initialize transcription services
        self.transcription_service = TranscriptionService(output_manager)
        self.speaker_service = SpeakerTranscriptionService(config)
        
        # Current processing state
        self.current_job: Optional[Dict[str, Any]] = None
        self.processing_stats: Dict[str, Any] = {}
    
    def transcribe(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Perform transcription on input data
        
        Args:
            input_data: Input data containing file information
            **kwargs: Additional transcription parameters
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            logger.info(f"Starting transcription for: {input_data.get('file_name', 'unknown')}")
            
            # Prepare job parameters
            job_params = self._prepare_job_params(input_data, **kwargs)
            
            # Determine transcription method
            engine = job_params.get('engine', 'faster-whisper')
            
            if engine == 'speaker-diarization':
                result = self._transcribe_with_speaker_diarization(job_params)
            else:
                result = self._transcribe_standard(job_params)
            
            # Update processing stats
            self._update_stats(result)
            
            logger.info(f"Transcription completed for: {input_data.get('file_name', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_job_params(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Prepare job parameters for transcription
        
        Args:
            input_data: Input data
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing job parameters
        """
        # Default parameters
        default_params = {
            'model': 'base',
            'engine': 'speaker-diarization',
            'save_output': True,
            'streaming': False,
            'speaker_config_preset': 'conversation'
        }
        
        logger.info(f"Default params: {default_params}")
        
        # Override with config defaults
        if hasattr(self.config, 'transcription'):
            config_params = self.config.transcription.__dict__
            logger.info(f"Config params: {config_params}")
            default_params.update(config_params)
            logger.info(f"After config override: {default_params}")
        
        # Override with kwargs
        if kwargs:
            # Only override with non-None values
            non_none_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            if non_none_kwargs:
                logger.info(f"Kwargs: {non_none_kwargs}")
                default_params.update(non_none_kwargs)
                logger.info(f"After kwargs override: {default_params}")
        
        # Add input data
        job_params = {
            'input': {
                'type': 'file',  # We're processing files directly
                'data': input_data.get('file_path'),
                'file_name': input_data.get('file_name'),
                'file_size': input_data.get('file_size'),
                'file_format': input_data.get('file_format')
            },
            **default_params
        }
        
        logger.info(f"Final job parameters: {job_params}")
        return job_params
    
    def _transcribe_standard(self, job_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform standard transcription
        
        Args:
            job_params: Job parameters
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            logger.info("Using standard transcription service")
            
            # Create job for transcription service
            job = {
                'input': {
                    'type': 'file',
                    'data': job_params['input']['data'],
                    'model': job_params['model'],
                    'engine': job_params['engine'],
                    'streaming': job_params['streaming'],
                    'save_output': job_params['save_output']
                }
            }
            
            # Perform transcription and consume the generator
            transcription_generator = self.transcription_service.transcribe(job)
            transcription_result = None
            
            # Consume the generator to get the actual result
            for result in transcription_generator:
                if 'error' in result:
                    return {
                        'success': False,
                        'error': result['error'],
                        'method': 'standard',
                        'timestamp': datetime.now().isoformat()
                    }
                elif 'result' in result:
                    transcription_result = result['result']
                    break
                else:
                    # For streaming results, collect all segments
                    if transcription_result is None:
                        transcription_result = []
                    transcription_result.append(result)
            
            return {
                'success': True,
                'transcription': transcription_result,
                'model': job_params['model'],
                'engine': job_params['engine'],
                'method': 'standard',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in standard transcription: {e}")
            return {
                'success': False,
                'error': str(e),
                'method': 'standard',
                'timestamp': datetime.now().isoformat()
            }
    
    def _transcribe_with_speaker_diarization(self, job_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform transcription with speaker diarization
        
        Args:
            job_params: Job parameters
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            logger.info("Using speaker diarization transcription service")
            
            # Extract parameters
            audio_file = job_params['input']['data']
            model_name = job_params['model']
            save_output = job_params['save_output']
            speaker_config = job_params['speaker_config_preset']
            
            # Configure speaker service with the specified preset
            from src.core.speaker_config_factory import SpeakerConfigFactory
            speaker_config_obj = SpeakerConfigFactory.get_config(speaker_config)
            self.speaker_service.config = speaker_config_obj
            
            # Perform speaker diarization transcription
            result = self.speaker_service.speaker_diarization(
                audio_file_path=audio_file,
                model_name=model_name,
                save_output=save_output
            )
            
            return {
                'success': True,
                'transcription': result,
                'model': model_name,
                'engine': 'speaker-diarization',
                'method': 'speaker-diarization',
                'speaker_config': speaker_config,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in speaker diarization transcription: {e}")
            return {
                'success': False,
                'error': str(e),
                'method': 'speaker-diarization',
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_stats(self, result: Dict[str, Any]):
        """
        Update processing statistics
        
        Args:
            result: Transcription result
        """
        if result.get('success', False):
            self.processing_stats['successful_transcriptions'] = \
                self.processing_stats.get('successful_transcriptions', 0) + 1
        else:
            self.processing_stats['failed_transcriptions'] = \
                self.processing_stats.get('failed_transcriptions', 0) + 1
        
        self.processing_stats['total_transcriptions'] = \
            self.processing_stats.get('total_transcriptions', 0) + 1
        self.processing_stats['last_transcription'] = datetime.now().isoformat()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics
        
        Returns:
            Dictionary containing processing statistics
        """
        return self.processing_stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            'successful_transcriptions': 0,
            'failed_transcriptions': 0,
            'total_transcriptions': 0,
            'last_transcription': None
        }
        logger.info("Processing statistics reset")
    
    def get_available_engines(self) -> Dict[str, str]:
        """
        Get available transcription engines
        
        Returns:
            Dictionary mapping engine names to descriptions
        """
        return {
            'faster-whisper': 'Fast Whisper transcription engine',
            'stable-whisper': 'Stable Whisper transcription engine',
            'speaker-diarization': 'Speaker diarization with transcription'
        }
    
    def get_available_models(self) -> Dict[str, str]:
        """
        Get available transcription models
        
        Returns:
            Dictionary mapping model names to descriptions
        """
        return {
            'tiny': 'Tiny model (fastest, least accurate)',
            'base': 'Base model (balanced speed/accuracy)',
            'small': 'Small model (good accuracy)',
            'medium': 'Medium model (better accuracy)',
            'large': 'Large model (best accuracy, slowest)',
            'large-v2': 'Large V2 model (improved accuracy)',
            'large-v3': 'Large V3 model (latest and most accurate)'
        }
    
    def validate_engine_model_combination(self, engine: str, model: str) -> Dict[str, Any]:
        """
        Validate engine and model combination
        
        Args:
            engine: Transcription engine
            model: Model name
            
        Returns:
            Dictionary containing validation results
        """
        available_engines = self.get_available_engines()
        available_models = self.get_available_models()
        
        engine_valid = engine in available_engines
        model_valid = model in available_models
        
        return {
            'valid': engine_valid and model_valid,
            'engine_valid': engine_valid,
            'model_valid': model_valid,
            'available_engines': list(available_engines.keys()),
            'available_models': list(available_models.keys())
        }
    
    def cleanup(self):
        """Cleanup orchestrator resources"""
        try:
            logger.info("Cleaning up transcription orchestrator")
            
            # Reset stats
            self.reset_stats()
            
            # Clear current job
            self.current_job = None
            
            logger.info("Transcription orchestrator cleanup completed")
            
        except Exception as e:
           logger.error(f"Error during orchestrator cleanup: {e}") 