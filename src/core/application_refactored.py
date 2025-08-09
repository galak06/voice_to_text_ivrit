#!/usr/bin/env python3
"""
Refactored Main Application Class
Follows SOLID principles with improved separation of concerns
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from datetime import datetime
import time

from src.core.processors.input_processor import InputProcessor
from src.core.processors.output_processor import OutputProcessor
from src.core.orchestrator.transcription_orchestrator import TranscriptionOrchestrator
from src.utils.config_manager import ConfigManager
from src.output_data import OutputManager
from src.logging import LoggingService
from src.clients.audio_transcription.audio_transcription_client import AudioTranscriptionClient
from src.utils.ui_manager import ApplicationUI
from src.core.logic.performance_monitor import PerformanceMonitor
from src.models.base_models import SessionInfo, ProcessingResult, ErrorInfo, PerformanceMetrics

logger = logging.getLogger(__name__)


class FileProcessingResult:
    """Result of processing a single file"""
    
    def __init__(self, file_path: str, success: bool, processing_time: float, 
                 error: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        self.file_path = file_path
        self.success = success
        self.processing_time = processing_time
        self.error = error
        self.data = data or {}
        self.timestamp = datetime.now()


class BatchProcessingResult:
    """Result of batch processing"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.results: List[FileProcessingResult] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
    
    @property
    def total_files(self) -> int:
        return len(self.results)
    
    @property
    def successful_files(self) -> int:
        return sum(1 for r in self.results if r.success)
    
    @property
    def failed_files(self) -> int:
        return sum(1 for r in self.results if not r.success)
    
    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.successful_files / self.total_files) * 100
    
    @property
    def total_processing_time(self) -> float:
        return sum(r.processing_time for r in self.results)
    
    @property
    def average_processing_time(self) -> float:
        if self.total_files == 0:
            return 0.0
        return self.total_processing_time / self.total_files
    
    def mark_completed(self):
        self.end_time = datetime.now()


class TranscriptionApplication:
    """
    Refactored main application class for voice-to-text transcription
    
    This class follows SOLID principles:
    - Single Responsibility: Orchestrates the transcription process
    - Open/Closed: Extensible through dependency injection
    - Liskov Substitution: Uses protocols for dependencies
    - Interface Segregation: Small, focused interfaces
    - Dependency Inversion: Depends on abstractions, not concretions
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, 
                 config_path: Optional[str] = None, 
                 ui_manager: Optional[ApplicationUI] = None):
        """Initialize the transcription application with dependency injection"""
        self._initialize_configuration(config_manager, config_path)
        self._initialize_session()
        self._initialize_components()
        self._initialize_ui_and_logging(ui_manager)
        self._initialize_performance_monitoring()
    
    def _initialize_configuration(self, config_manager: Optional[ConfigManager], 
                                config_path: Optional[str]) -> None:
        """Initialize configuration with proper error handling"""
        try:
            if config_manager is not None:
                self.config_manager = config_manager
            elif config_path:
                config_path_obj = Path(config_path)
                config_dir = str(config_path_obj.parent) if config_path_obj.is_file() else config_path
                self.config_manager = ConfigManager(config_dir)
            else:
                self.config_manager = ConfigManager()
            
            self.config = self.config_manager.config
            self._ensure_config_initialized()
            
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {e}")
            raise
    
    def _ensure_config_initialized(self) -> None:
        """Ensure all configuration sections are properly initialized"""
        from src.models import (
            TranscriptionConfig, SpeakerConfig, BatchConfig, 
            DockerConfig, RunPodConfig, OutputConfig, 
            SystemConfig, InputConfig
        )
        
        # Initialize any None configuration sections with defaults
        config_sections = {
            'transcription': TranscriptionConfig,
            'speaker': SpeakerConfig,
            'batch': BatchConfig,
            'docker': DockerConfig,
            'runpod': RunPodConfig,
            'output': OutputConfig,
            'system': SystemConfig,
            'input': InputConfig
        }
        
        for section_name, config_class in config_sections.items():
            if getattr(self.config, section_name) is None:
                setattr(self.config, section_name, config_class())
    
    def _initialize_session(self) -> None:
        """Initialize session information"""
        self.session_info = SessionInfo(
            session_id=self._generate_session_id(),
            start_time=datetime.now()
        )
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for this application run"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"
    
    def _initialize_components(self) -> None:
        """Initialize core components with dependency injection"""
        # Create DataUtils instance for dependency injection
        from src.output_data.utils.data_utils import DataUtils
        data_utils = DataUtils()
        
        self.output_manager = OutputManager(
            output_base_path=self.config.output.output_dir,
            data_utils=data_utils
        )
        
        # Initialize specialized processors
        self.input_processor = InputProcessor(self.config_manager, self.output_manager)
        self.output_processor = OutputProcessor(self.config_manager, self.output_manager)
        self.transcription_orchestrator = TranscriptionOrchestrator(
            self.config_manager, 
            self.output_manager
        )
    
    def _initialize_ui_and_logging(self, ui_manager: Optional[ApplicationUI]) -> None:
        """Initialize UI manager and logging service"""
        self.ui_manager = ui_manager or ApplicationUI(self.config_manager)
        self.logging_service = LoggingService(self.config_manager)
        self.logging_service.log_application_start()
    
    def _initialize_performance_monitoring(self) -> None:
        """Initialize performance monitoring"""
        self.performance_monitor = PerformanceMonitor()
        self._audio_client = None  # Lazy initialization
    
    def process_single_file(self, audio_file_path: str, **kwargs) -> ProcessingResult:
        """
        Process a single audio file through the complete pipeline
        
        Args:
            audio_file_path: Path to the audio file
            **kwargs: Additional parameters (model, engine, etc.)
            
        Returns:
            ProcessingResult containing the processing outcome
        """
        start_time = time.time()
        
        try:
            logger.info(f"🎤 Processing single file: {audio_file_path}")
            
            # Validate input
            if not self._validate_input_file(audio_file_path):
                return self._create_error_result("INVALID_INPUT", f"Invalid input file: {audio_file_path}")
            
            # Process through pipeline
            result = self._execute_processing_pipeline(audio_file_path, **kwargs)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update session statistics
            self._update_session_stats(processing_time, result.success)
            
            return ProcessingResult(
                success=result.success,
                status="completed" if result.success else "failed",
                data=result.data,
                error=result.error,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing file {audio_file_path}: {e}")
            self.logging_service.log_error(e, f"process_single_file: {audio_file_path}")
            
            return self._create_error_result("PROCESSING_ERROR", str(e), processing_time)
    
    def _validate_input_file(self, audio_file_path: str) -> bool:
        """Validate input file exists and is accessible"""
        try:
            path = Path(audio_file_path)
            return path.exists() and path.is_file()
        except Exception:
            return False
    
    def _execute_processing_pipeline(self, audio_file_path: str, **kwargs) -> ProcessingResult:
        """Execute the complete processing pipeline"""
        try:
            # Input processing
            input_result = self.input_processor.process_input(audio_file_path)
            if not input_result['success']:
                return self._create_error_result("INPUT_PROCESSING_ERROR", input_result.get('error', 'Unknown error'))
            
            # Transcription orchestration
            transcription_result = self.transcription_orchestrator.transcribe(
                input_result['data'], 
                session_id=self.session_info.session_id,
                **kwargs
            )
            
            # Output processing
            output_result = self.output_processor.process_output(
                transcription_result,
                input_result['metadata']
            )
            
            return ProcessingResult(
                success=True,
                status="completed",
                data={
                    'input': input_result,
                    'transcription': transcription_result,
                    'output': output_result
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            return self._create_error_result("PIPELINE_ERROR", str(e))
    
    def _create_error_result(self, error_code: str, error_message: str, 
                           processing_time: float = 0.0) -> ProcessingResult:
        """Create a standardized error result"""
        return ProcessingResult(
            success=False,
            status="failed",
            error=ErrorInfo(
                code=error_code,
                message=error_message,
                timestamp=datetime.now()
            ),
            processing_time=processing_time,
            timestamp=datetime.now()
        )
    
    def _update_session_stats(self, processing_time: float, success: bool) -> None:
        """Update session statistics"""
        self.session_info.total_files += 1
        if success:
            self.session_info.successful_files += 1
        else:
            self.session_info.failed_files += 1
    
    def process_batch(self, input_directory: Optional[str] = None, **kwargs) -> BatchProcessingResult:
        """
        Process multiple audio files in batch mode with enhanced error recovery
        
        Args:
            input_directory: Directory containing audio files
            **kwargs: Additional parameters (model, engine, etc.)
            
        Returns:
            BatchProcessingResult containing batch processing results
        """
        batch_result = BatchProcessingResult(self.session_info.session_id)
        
        try:
            # Discover audio files
            audio_files = self._discover_audio_files(input_directory)
            if not audio_files:
                logger.warning("No audio files found for batch processing")
                return batch_result
            
            logger.info(f"🎤 Processing batch of {len(audio_files)} files")
            self.logging_service.log_processing_start(len(audio_files), batch_mode=True)
            
            # Process files with retry logic
            batch_result.results = self._process_files_with_retry(audio_files, **kwargs)
            
            # Mark batch as completed
            batch_result.mark_completed()
            
            # Log completion statistics
            self._log_batch_completion(batch_result)
            
            return batch_result
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            self.logging_service.log_error(e, "process_batch")
            return batch_result
    
    def _discover_audio_files(self, input_directory: Optional[str]) -> List[str]:
        """Discover audio files in the input directory"""
        if input_directory:
            return self.input_processor.discover_files(input_directory)
        elif self.config.input and self.config.input.directory:
            return self.input_processor.discover_files(self.config.input.directory)
        else:
            return []
    
    def _process_files_with_retry(self, audio_files: List[str], **kwargs) -> List[FileProcessingResult]:
        """Process files with retry logic"""
        results = []
        retry_queue = []
        
        # First pass: process all files
        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"📊 Processing file {i}/{len(audio_files)}: {audio_file}")
            
            result = self.process_single_file(audio_file, **kwargs)
            file_result = FileProcessingResult(
                file_path=audio_file,
                success=result.success,
                processing_time=result.processing_time,
                error=result.error.message if result.error else None,
                data=result.data
            )
            results.append(file_result)
            
            if not result.success and self._should_retry():
                retry_queue.append((audio_file, kwargs))
        
        # Second pass: retry failed files
        if retry_queue:
            self._retry_failed_files(retry_queue, results)
        
        return results
    
    def _should_retry(self) -> bool:
        """Determine if retry should be attempted"""
        return (self.config.system and 
                self.config.system.retry_attempts > 0)
    
    def _retry_failed_files(self, retry_queue: List[tuple], 
                           results: List[FileProcessingResult]) -> None:
        """Retry failed files with exponential backoff"""
        logger.info(f"🔄 Retrying {len(retry_queue)} failed files...")
        
        for audio_file, kwargs in retry_queue:
            for attempt in range(1, self.config.system.retry_attempts + 1):
                logger.info(f"🔄 Retry attempt {attempt}/{self.config.system.retry_attempts} for {audio_file}")
                
                # Add exponential backoff
                if attempt > 1:
                    backoff_time = min(2 ** (attempt - 1), 30)
                    logger.info(f"⏳ Waiting {backoff_time} seconds before retry...")
                    time.sleep(backoff_time)
                
                result = self.process_single_file(audio_file, **kwargs)
                
                if result.success:
                    # Update the original result
                    for file_result in results:
                        if file_result.file_path == audio_file:
                            file_result.success = True
                            file_result.error = None
                            file_result.data = result.data
                            break
                    logger.info(f"✅ Retry successful for {audio_file}")
                    break
                else:
                    logger.warning(f"❌ Retry failed for {audio_file}: {result.error.message}")
    
    def _log_batch_completion(self, batch_result: BatchProcessingResult) -> None:
        """Log batch completion statistics"""
        logger.info(f"📊 BATCH PROCESSING COMPLETE:")
        logger.info(f"   - Total files: {batch_result.total_files}")
        logger.info(f"   - Successful: {batch_result.successful_files}")
        logger.info(f"   - Failed: {batch_result.failed_files}")
        logger.info(f"   - Success rate: {batch_result.success_rate:.1f}%")
        logger.info(f"   - Total processing time: {batch_result.total_processing_time:.1f}s")
        logger.info(f"   - Average processing time: {batch_result.average_processing_time:.1f}s")
        
        # Log failed files
        failed_files = [r for r in batch_result.results if not r.success]
        if failed_files:
            logger.warning(f"❌ Failed files:")
            for failed_file in failed_files:
                logger.warning(f"   - {failed_file.file_path}: {failed_file.error}")
        
        # Log processing completion
        self.logging_service.log_processing_complete(
            batch_result.successful_files, 
            batch_result.total_files, 
            batch_mode=True
        )
    
    @property
    def audio_client(self) -> Optional[AudioTranscriptionClient]:
        """Lazy-load AudioTranscriptionClient when needed"""
        if self._audio_client is None:
            try:
                data_utils = self.output_manager.data_utils if self.output_manager else None
                self._audio_client = AudioTranscriptionClient(
                    config=self.config,
                    data_utils=data_utils
                )
            except ImportError as e:
                logger.warning(f"RunPod not available: {e}")
                return None
        return self._audio_client
    
    def get_status(self) -> Dict[str, Any]:
        """Get current application status with performance metrics"""
        performance_report = self.performance_monitor.get_performance_report()
        
        return {
            'session_info': self.session_info.to_dict(),
            'config_loaded': self.config is not None,
            'components_ready': {
                'output_manager': self.output_manager is not None,
                'input_processor': self.input_processor is not None,
                'output_processor': self.output_processor is not None,
                'transcription_orchestrator': self.transcription_orchestrator is not None,
                'audio_client': self.audio_client is not None,
            },
            'performance_metrics': performance_report,
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            logger.info("🧹 Cleaning up application resources")
            
            if hasattr(self, 'performance_monitor'):
                self.performance_monitor.cleanup()
            
            self.session_info.mark_completed()
            self.logging_service.log_application_shutdown()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            self.logging_service.log_error(e, "cleanup")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
