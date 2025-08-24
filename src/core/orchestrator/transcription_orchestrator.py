"""
Transcription Orchestrator
Coordinates the transcription process using various transcription services
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
import logging
from datetime import datetime

from .transcription_service import TranscriptionService
from .speaker_transcription_service import SpeakerTranscriptionService
from src.utils.config_manager import ConfigManager
from src.models.speaker_models import SpeakerConfig
from src.core.factories.engine_factory import create_engine
from src.core.factories.speaker_config_factory import SpeakerConfigFactory
from src.core.factories.speaker_enhancement_factory import create_speaker_enhancement_orchestrator

if TYPE_CHECKING:
    from src.output_data import OutputManager


logger = logging.getLogger(__name__)

class TranscriptionOrchestrator:
    """
    Orchestrates the transcription process
    
    This class follows the Single Responsibility Principle by coordinating
    transcription operations while delegating specific transcription tasks
    to specialized services.
    """
    
    def __init__(self, config_manager: ConfigManager, output_manager: 'OutputManager'):
        """
        Initialize the transcription orchestrator
        
        Args:
            config_manager: Configuration manager instance
            output_manager: Output manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.output_manager = output_manager
        # Initialize transcription services
        self.transcription_service = TranscriptionService(self.config_manager, self.output_manager)
        
        # Convert SpeakerConfig to the expected type
        speaker_config = None
        if isinstance(self.config, dict):
            if 'speaker' in self.config:
                # Check if speaker diarization is enabled
                speaker_diarization_enabled = self.config.get('speaker_diarization', {}).get('enabled', True)
                if speaker_diarization_enabled:
                    # Get constants from system configuration
                    system_config = self.config.get('system', {})
                    constants = system_config.get('constants', {})
                    default_silence_duration = constants.get('min_silence_duration_ms', 300)
                    
                    speaker_config = SpeakerConfig(
                        min_speakers=self.config['speaker'].get('min_speakers', 2),
                        max_speakers=self.config['speaker'].get('max_speakers', 4),
                        silence_threshold=self.config['speaker'].get('silence_threshold', 1.5),
                        vad_enabled=self.config['speaker'].get('vad_enabled', True),
                        word_timestamps=self.config['speaker'].get('word_timestamps', True),
                        language=self.config['speaker'].get('language', 'he'),
                        beam_size=self.config['speaker'].get('beam_size', 5),
                        vad_min_silence_duration_ms=self.config['speaker'].get('vad_min_silence_duration_ms', default_silence_duration)
                    )
        else:
            if hasattr(self.config, 'speaker') and self.config.speaker:
                # Check if speaker diarization is enabled
                speaker_diarization_enabled = getattr(self.config, 'speaker_diarization', {}).get('enabled', True)
                if speaker_diarization_enabled:
                    # Get constants from system configuration
                    constants = self.config.system.constants if hasattr(self.config, 'system') and self.config.system else None
                    default_silence_duration = constants.min_silence_duration_ms if constants else 300
                    
                    speaker_config = SpeakerConfig(
                        min_speakers=self.config.speaker.min_speakers,
                        max_speakers=self.config.speaker.max_speakers,
                        silence_threshold=getattr(self.config.speaker, 'silence_threshold', 1.5),
                        vad_enabled=getattr(self.config.speaker, 'vad_enabled', True),
                        word_timestamps=getattr(self.config.speaker, 'word_timestamps', True),
                        language=getattr(self.config.speaker, 'language', 'he'),
                        beam_size=getattr(self.config.speaker, 'beam_size', 5),
                        vad_min_silence_duration_ms=getattr(self.config.speaker, 'vad_min_silence_duration_ms', default_silence_duration)
                    )
        
        self.speaker_service = SpeakerTranscriptionService(speaker_config, self.config, self.output_manager)
        
        # Initialize speaker enhancement orchestrator with dependency injection
        self.speaker_enhancement_orchestrator = create_speaker_enhancement_orchestrator(self.speaker_service)
        
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
            
            # Use unified transcription method since all engines implement the same interface
            result = self._transcribe_with_engine(job_params)
            
            # Update statistics
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in transcription: {e}")
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
            Dictionary with prepared job parameters
        """
        # Extract basic parameters
        file_path = input_data.get('file_path', '')
        file_name = input_data.get('file_name', '')
        
        # Get engine and model from kwargs first, then input_data, then defaults
        engine = kwargs.get('engine') or input_data.get('engine', 'speaker-diarization')
        model = kwargs.get('model') or input_data.get('model', 'ivrit-ai/whisper-large-v3-ct2')
        
        # Validate engine-model combination
        validation_result = self.validate_engine_model_combination(engine, model)
        if not validation_result.get('valid', False):
            logger.warning(f"Invalid engine-model combination: {validation_result.get('error', 'Unknown error')}")
            logger.info(f"🎯 Proceeding with user-specified combination: engine={engine}, model={model}")
            # Note: Commenting out fallback to allow user-specified combinations
            # engine = 'speaker-diarization'
            # model = 'ivrit-ai/whisper-large-v3'
        
        # Prepare job parameters
        job_params = {
            'input': {
                'data': file_path,
                'file_name': file_name,
                'type': 'file'
            },
            'engine': engine,
            'model': model,
            'save_output': input_data.get('save_output', True),
            'session_id': input_data.get('session_id'),
            **kwargs
        }
        
        logger.info(f"Prepared job parameters: engine={engine}, model={model}")
        return job_params
    
    def _transcribe_with_engine(self, job_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform transcription using the specified engine
        
        Args:
            job_params: Job parameters containing engine and model information
            
        Returns:
            Dictionary containing transcription results
        """
        # Initialize variables for error handling
        audio_file = job_params['input']['data']
        engine_type = job_params['engine']
        model_name = job_params['model']
        save_output = job_params['save_output']
        
        try:
            
            logger.info(f"Using {engine_type} engine with model {model_name}")
            
            # Create engine using factory
            speaker_config = SpeakerConfigFactory.get_config('default')
            engine = create_engine(engine_type, speaker_config, self.config)
            
            # Check if engine is available
            if not engine.is_available():
                raise Exception(f"{engine_type} engine is not available. Please install required dependencies.")
            
            # Perform transcription using unified interface
            logger.info(f"🎯 About to call engine.transcribe() on {type(engine).__name__}")
            logger.info(f"🎯 Engine method type: {type(engine.transcribe)}")
            result = engine.transcribe(audio_file, model_name)
            logger.info(f"🎯 Transcription completed, result type: {type(result)}")
            
            # Apply speaker enhancement if using speaker-diarization engine AND it's enabled in config
            if (engine_type == 'speaker-diarization' and 
                result.success and 
                self._is_speaker_diarization_enabled()):
                
                logger.info("🎯 Applying speaker diarization enhancement")
                try:
                    enhanced_result = self.speaker_enhancement_orchestrator.enhance_transcription(
                        result, audio_file, strategy='chunked'
                    )
                    if enhanced_result.success:
                        logger.info(f"✅ Speaker enhancement successful: {len(enhanced_result.speakers)} speakers detected")
                        result = enhanced_result
                    else:
                        logger.warning("⚠️ Speaker enhancement failed, using original result")
                except Exception as e:
                    logger.error(f"❌ Error in speaker enhancement: {e}")
                    logger.warning("⚠️ Continuing with original transcription result")
            elif engine_type == 'speaker-diarization' and not self._is_speaker_diarization_enabled():
                logger.info("ℹ️ Speaker diarization engine selected but disabled in configuration")
            
            # Convert result to output format
            transcription_data = None
            if save_output and result.success:
                transcription_data = self._convert_result_to_output_format(result)
                self._save_transcription_output(transcription_data, audio_file, model_name, engine_type, job_params.get('session_id'))
            
            # Create unified response
            return self._create_unified_response(result, transcription_data, model_name, engine_type, save_output)
            
        except Exception as e:
            engine_type = job_params.get('engine', 'unknown')
            logger.error(f"Error in {engine_type} transcription: {e}")
            
            # Try to preserve any partial results
            partial_data = {}
            if 'audio_file' in locals():
                partial_data['audio_file'] = audio_file
            if 'engine_type' in locals():
                partial_data['engine_type'] = engine_type
            if 'model_name' in locals():
                partial_data['model_name'] = model_name
            
            return {
                'success': False,
                'error': str(e),
                'engine': engine_type,
                'method': engine_type,
                'timestamp': datetime.now().isoformat(),
                'partial_data': partial_data,
                'error_type': type(e).__name__
            }
    
    def _convert_result_to_output_format(self, result) -> Dict[str, Any]:
        """
        Convert transcription result to output format
        
        Args:
            result: TranscriptionResult from engine
            
        Returns:
            Dictionary in output format
        """
        speakers_data = {}
        for speaker, segments in result.speakers.items():
            speakers_data[speaker] = [
                {
                    'speaker': speaker,
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'words': getattr(segment, 'words', [])
                }
                for segment in segments
            ]
        
        transcription_data = {
            'speakers': speakers_data,
            'segments': [
                {
                    'speaker': speaker,
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'words': getattr(segment, 'words', [])
                }
                for speaker, segments in result.speakers.items()
                for segment in segments
            ],
            'model_name': getattr(result, 'model_used', 'unknown'),
            'audio_file': getattr(result, 'audio_file', 'unknown'),
            'transcription_time': getattr(result, 'processing_time', 0.0),
            'speaker_count': len(result.speakers),
            'full_text': result.full_text
        }
        
        self._log_conversion_details(result, transcription_data)
        return transcription_data
    
    def _log_conversion_details(self, result, transcription_data: Dict[str, Any]):
        """Log conversion details"""
        total_words = sum(len(seg['text'].split()) for seg in transcription_data['segments'])
        logger.info(f"🔄 CONVERTING TO OUTPUT FORMAT:")
        logger.info(f"   - Input segments: {sum(len(segments) for segments in result.speakers.values())}")
        logger.info(f"   - Output speakers: {list(transcription_data['speakers'].keys())}")
        logger.info(f"   - Output segments: {len(transcription_data['segments'])}")
        logger.info(f"   - Total text length: {len(result.full_text)} characters")
        logger.info(f"   - Total word count: {total_words} words")
        
        if transcription_data['segments']:
            first_seg = transcription_data['segments'][0]
            last_seg = transcription_data['segments'][-1]
            logger.info(f"   - First segment: {first_seg['start']:.1f}s - {first_seg['end']:.1f}s ({len(first_seg['text'])} chars)")
            logger.info(f"   - Last segment: {last_seg['start']:.1f}s - {last_seg['end']:.1f}s ({len(last_seg['text'])} chars)")
    
    def _save_transcription_output(self, transcription_data: Dict[str, Any], audio_file: str, 
                                 model_name: str, engine_type: str, session_id: Optional[str] = None):
        """Save transcription output"""
        try:
            saved_files = self.output_manager.save_transcription(
                transcription_data=transcription_data,
                audio_file=audio_file,
                model=model_name,
                engine=engine_type,
                session_id=session_id
            )
            logger.info(f"{engine_type} transcription completed and saved for {audio_file}")
        except Exception as e:
            logger.error(f"Failed to save {engine_type} output: {e}")
    
    def _create_unified_response(self, result, transcription_data: Optional[Dict[str, Any]], 
                               model_name: str, engine_type: str, save_output: bool) -> Dict[str, Any]:
        """Create unified response for transcription"""
        return {
            'success': result.success,
            'transcription': transcription_data if save_output and result.success else result.full_text,
            'speakers': result.speakers,
            'model': model_name,
            'engine': engine_type,
            'method': engine_type,
            'transcription_time': getattr(result, 'processing_time', 0.0),
            'timestamp': datetime.now().isoformat(),
            'error': getattr(result, 'error', None)
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
            self.processing_stats['total_processing_time'] = \
                self.processing_stats.get('total_processing_time', 0.0) + result.get('transcription_time', 0.0)
        else:
            self.processing_stats['failed_transcriptions'] = \
                self.processing_stats.get('failed_transcriptions', 0) + 1
        
        # Update engine-specific stats
        engine = result.get('engine', 'unknown')
        if engine not in self.processing_stats:
            self.processing_stats[engine] = {'success': 0, 'failed': 0}
        
        if result.get('success', False):
            self.processing_stats[engine]['success'] += 1
        else:
            self.processing_stats[engine]['failed'] += 1
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics
        
        Returns:
            Dictionary with processing statistics
        """
        return self.processing_stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {}
        logger.info("Processing statistics reset")
    
    def get_available_engines(self) -> Dict[str, str]:
        """
        Get available transcription engines
        
        Returns:
            Dictionary mapping engine types to descriptions
        """
        return {
            'speaker-diarization': 'Custom Whisper with speaker diarization',
            'custom-whisper': 'Custom Whisper implementation',
            'stable-whisper': 'Stable Whisper implementation',
            'optimized-whisper': 'CTranslate2 optimized Whisper',
            'ctranslate2': 'Alias for optimized-whisper'
        }
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """
        Get available models for each engine
        
        Returns:
            Dictionary mapping engine types to available models
        """
        return {
            'speaker-diarization': ['ivrit-ai/whisper-large-v3-ct2'],
            'custom-whisper': ['ivrit-ai/whisper-large-v3-ct2'],
            'stable-whisper': ['ivrit-ai/whisper-large-v3-ct2'],
            'optimized-whisper': ['ivrit-ai/whisper-large-v3-ct2'],
            'ctranslate2': ['ivrit-ai/whisper-large-v3-ct2']
        }
    
    def validate_engine_model_combination(self, engine: str, model: str) -> Dict[str, Any]:
        """
        Validate engine-model combination
        
        Args:
            engine: Engine type
            model: Model name
            
        Returns:
            Dictionary with validation result
        """
        try:
            # Check if engine is supported
            available_engines = self.get_available_engines()
            if engine not in available_engines:
                return {
                    'valid': False,
                    'error': f'Unsupported engine: {engine}. Available engines: {list(available_engines.keys())}'
                }
            
            # Check if model is supported for the engine
            available_models = self.get_available_models()
            if engine in available_models and model not in available_models[engine]:
                return {
                    'valid': False,
                    'error': f'Model {model} not supported for engine {engine}. Available models: {available_models[engine]}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up transcription orchestrator")
        # Reset statistics
        self.reset_stats()
        # Clear current job
        self.current_job = None
    
    def _is_speaker_diarization_enabled(self) -> bool:
        """
        Check if speaker diarization is enabled in configuration and environment
        
        Returns:
            True if enabled, False otherwise
        """
        try:
            # First check environment variable (highest priority)
            import os
            env_enabled = os.getenv('SPEAKER_DIARIZATION_ENABLED', 'true').lower()
            if env_enabled == 'false':
                logger.info("ℹ️ Speaker diarization disabled via environment variable")
                return False
            
            # Then check configuration object attributes
            if hasattr(self.config, 'speaker'):
                # Check if speaker config has the diarization enabled flag
                if hasattr(self.config.speaker, '_diarization_enabled'):
                    return self.config.speaker._diarization_enabled
                
                # Check speaker config object properties
                if hasattr(self.config.speaker, 'min_speakers') and hasattr(self.config.speaker, 'max_speakers'):
                    # If speaker config exists and has speaker settings, assume enabled
                    return True
            
            # Then check legacy configuration (dict format)
            if isinstance(self.config, dict):
                if 'speaker_diarization' in self.config:
                    return self.config['speaker_diarization'].get('enabled', True)
            elif hasattr(self.config, 'speaker_diarization'):
                return getattr(self.config.speaker_diarization, 'enabled', True)
            
            return True  # Default to enabled if not specified
        except Exception as e:
            logger.debug(f"Error checking speaker diarization enabled: {e}")
            return True  # Default to enabled on error 