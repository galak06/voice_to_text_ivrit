"""
Audio File Processor
Concrete implementation of ProcessingPipeline for audio file transcription
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from src.core.processors.processing_pipeline import (
    ProcessingPipeline, 
    ProcessingContext, 
    ProcessingResult
)
# Import moved to method level to avoid circular import
from src.utils.config_manager import ConfigManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.output_data import OutputManager


class AudioFileProcessor(ProcessingPipeline):
    """
    Concrete implementation for audio file transcription processing
    
    This class extends the ProcessingPipeline template method pattern
    to provide specific audio file transcription functionality.
    """
    
    def __init__(self, config_manager: ConfigManager, output_manager: 'OutputManager'):
        """Initialize the audio file processor"""
        super().__init__(config_manager, output_manager)
        # Lazy initialization to avoid circular import
        self._transcription_orchestrator = None
    
    @property
    def transcription_orchestrator(self):
        """Lazy load transcription orchestrator to avoid circular import"""
        if self._transcription_orchestrator is None:
            from src.core.orchestrator.transcription_orchestrator import TranscriptionOrchestrator
            self._transcription_orchestrator = TranscriptionOrchestrator(
                self.config_manager, 
                self.output_manager
            )
        return self._transcription_orchestrator
    
    def _execute_core_processing(self, context: ProcessingContext) -> Dict[str, Any]:
        """Execute core audio transcription processing"""
        try:
            # Get transcription parameters
            model = context.parameters.get('model')
            engine = context.parameters.get('engine')
            speaker_preset = context.parameters.get('speaker_preset')
            
            # Execute transcription
            from pathlib import Path
            file_path = Path(context.file_path) if isinstance(context.file_path, str) else context.file_path
            
            input_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'engine': engine,
                'model': model,
                'save_output': True,
                'session_id': getattr(context, 'session_id', None)
            }
            
            # Add speaker preset as additional parameter
            kwargs = {}
            if speaker_preset:
                kwargs['speaker_preset'] = speaker_preset
            
            transcription_result = self.transcription_orchestrator.transcribe(input_data, **kwargs)
            
            if not transcription_result['success']:
                return transcription_result
            
            # Extract transcription data
            transcription_data = transcription_result.get('data', {})
            
            self._log_processing_step("Core processing", context, True, 
                                    f"Transcription completed with {engine} engine")
            
            return {
                'success': True,
                'transcription': transcription_data.get('transcription', ''),
                'segments': transcription_data.get('segments', []),
                'metadata': transcription_data.get('metadata', {}),
                'processing_info': {
                    'model': model,
                    'engine': engine,
                    'speaker_preset': speaker_preset,
                    'processing_time': transcription_result.get('processing_time', 0)
                }
            }
            
        except Exception as e:
            return self.error_handler.handle_transcription_error(
                e, context.file_path, 
                engine=context.parameters.get('engine'),
                model=context.parameters.get('model')
            )
    
    def _validate_input(self, context: ProcessingContext) -> Dict[str, Any]:
        """Validate audio file input"""
        try:
            if not context.file_path:
                return {'success': False, 'error': 'No file path provided'}
            
            file_path = Path(context.file_path)
            if not file_path.exists():
                # Standardize missing file message for tests
                return {'success': False, 'error': 'File not found'}
            
            if not file_path.is_file():
                return {'success': False, 'error': f'Path is not a file: {context.file_path}'}
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                return {'success': False, 'error': 'File is empty'}
            
            # Validate file format
            supported_formats = self.config.input.supported_formats if self.config.input else ['.wav', '.mp3', '.m4a']
            if file_path.suffix.lower() not in supported_formats:
                return {'success': False, 'error': f'Unsupported file format: {file_path.suffix}'}
            
            self._log_processing_step("Input validation", context, True, f"File size: {file_size} bytes")
            return {'success': True, 'file_size': file_size}
            
        except Exception as e:
            return self.error_handler.handle_file_processing_error(e, context.file_path, "validation")
    
    def _preprocess(self, context: ProcessingContext) -> Dict[str, Any]:
        """Pre-process audio file"""
        try:
            # Extract metadata
            metadata = self._extract_audio_metadata(context.file_path)
            
            # Prepare processing parameters
            processing_params = self._prepare_processing_parameters(context)
            
            self._log_processing_step("Preprocessing", context, True, f"Duration: {metadata.get('duration', 'unknown')}")
            return {
                'success': True,
                'metadata': metadata,
                'processing_params': processing_params
            }
            
        except Exception as e:
            return self.error_handler.handle_file_processing_error(e, context.file_path, "preprocessing")
    
    def _postprocess(self, context: ProcessingContext, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process audio processing results"""
        try:
            # Validate results
            if not data:
                return {'success': False, 'error': 'No processing data available'}
            
            # Format results
            formatted_data = self._format_results(data)
            
            # Save results if requested
            if context.parameters.get('save_output', True):
                save_result = self._save_results(context, formatted_data)
                if not save_result['success']:
                    return save_result
            
            self._log_processing_step("Postprocessing", context, True, "Results formatted and saved")
            return {'success': True, 'data': formatted_data}
            
        except Exception as e:
            return self.error_handler.handle_file_processing_error(e, context.file_path, "postprocessing")
    
    def _extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract audio file metadata"""
        try:
            # Basic metadata extraction
            file_path_obj = Path(file_path)
            stat = file_path_obj.stat()
            
            return {
                'file_name': file_path_obj.name,
                'file_size': stat.st_size,
                'file_extension': file_path_obj.suffix.lower(),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'duration': None  # Would need audio library to get actual duration
            }
        except Exception as e:
            return {'error': f'Failed to extract metadata: {e}'}
    
    def _prepare_processing_parameters(self, context: ProcessingContext) -> Dict[str, Any]:
        """Prepare processing parameters from context"""
        return {
            'model': context.parameters.get('model', self.config.transcription.default_model),
            'engine': context.parameters.get('engine', self.config.transcription.default_engine),
            'speaker_preset': context.parameters.get('speaker_preset', 'default'),
            'save_output': context.parameters.get('save_output', True)
        }
    
    def _format_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format processing results"""
        return {
            'transcription': data.get('transcription', ''),
            'segments': data.get('segments', []),
            'metadata': data.get('metadata', {}),
            'processing_info': data.get('processing_info', {}),
            'timestamp': datetime.now().isoformat()
        }
    
    def _save_results(self, context: ProcessingContext, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save processing results"""
        try:
            # Save transcription results
            file_name = Path(context.file_path).stem
            save_result = self.output_manager.save_transcription(data, file_name)
            
            if save_result['success']:
                self._log_processing_step("Save results", context, True, f"Saved to {save_result.get('file_path', 'unknown')}")
                return {'success': True, 'file_path': save_result.get('file_path')}
            else:
                return save_result
                
        except Exception as e:
            return self.error_handler.handle_file_processing_error(e, context.file_path, "save_results")
    
    def process_audio_file(self, file_path: str, session_id: str, **kwargs) -> ProcessingResult:
        """
        Convenience method for processing a single audio file
        
        Args:
            file_path: Path to the audio file
            session_id: Session identifier
            **kwargs: Additional processing parameters
            
        Returns:
            ProcessingResult with transcription data
        """
        context = ProcessingContext(
            session_id=session_id,
            file_path=file_path,
            operation_type="audio_transcription",
            parameters=kwargs
        )
        
        return self.process(context) 