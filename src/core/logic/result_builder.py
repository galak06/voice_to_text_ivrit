"""
Result Builder
Provides a fluent interface for creating standardized result dictionaries
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
from enum import Enum


class ResultType(Enum):
    """Result types for categorization"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ResultBuilder:
    """
    Fluent interface for building standardized result dictionaries
    
    This class follows the Builder pattern to create consistent result structures
    across the application, eliminating code duplication.
    """
    
    def __init__(self):
        """Initialize an empty result builder"""
        self._result: Dict[str, Any] = {}
        self._timestamp = datetime.now().isoformat()
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[str] = []
        self._performance_metrics: Dict[str, Any] = {}
    
    def success(self, success: bool = True) -> 'ResultBuilder':
        """
        Set the success status of the result
        
        Args:
            success: Whether the operation was successful
            
        Returns:
            Self for method chaining
        """
        self._result['success'] = success
        return self
    
    def error(self, error_message: str, error_type: Optional[str] = None, 
              error_category: Optional[str] = None, severity: Optional[str] = None) -> 'ResultBuilder':
        """
        Set an error message with enhanced error information
        
        Args:
            error_message: Description of the error
            error_type: Type of error (e.g., 'ValidationError', 'ProcessingError')
            error_category: Category of error (e.g., 'validation', 'processing')
            severity: Error severity (e.g., 'low', 'medium', 'high', 'critical')
            
        Returns:
            Self for method chaining
        """
        error_info = {
            'message': error_message,
            'timestamp': self._timestamp
        }
        
        if error_type:
            error_info['type'] = error_type
        if error_category:
            error_info['category'] = error_category
        if severity:
            error_info['severity'] = severity
        
        self._errors.append(error_info)
        self._result['error'] = error_message
        self._result['errors'] = self._errors
        return self
    
    def add_error(self, error_info: Dict[str, Any]) -> 'ResultBuilder':
        """
        Add a detailed error to the result
        
        Args:
            error_info: Dictionary containing error details
            
        Returns:
            Self for method chaining
        """
        self._errors.append(error_info)
        self._result['errors'] = self._errors
        return self
    
    def warning(self, warning_message: str) -> 'ResultBuilder':
        """
        Add a warning message
        
        Args:
            warning_message: Warning description
            
        Returns:
            Self for method chaining
        """
        self._warnings.append(warning_message)
        self._result['warnings'] = self._warnings
        return self
    
    def performance_metric(self, name: str, value: Any, unit: Optional[str] = None) -> 'ResultBuilder':
        """
        Add a performance metric
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement (optional)
            
        Returns:
            Self for method chaining
        """
        metric = {'value': value}
        if unit:
            metric['unit'] = unit
        self._performance_metrics[name] = metric
        self._result['performance_metrics'] = self._performance_metrics
        return self
    
    def processing_time(self, seconds: float) -> 'ResultBuilder':
        """
        Set processing time in seconds
        
        Args:
            seconds: Processing time in seconds
            
        Returns:
            Self for method chaining
        """
        return self.performance_metric('processing_time_seconds', seconds, 'seconds')
    
    def file_path(self, file_path: str) -> 'ResultBuilder':
        """
        Set the file path
        
        Args:
            file_path: Path to the file being processed
            
        Returns:
            Self for method chaining
        """
        self._result['file_path'] = file_path
        return self
    
    def file_name(self, file_name: str) -> 'ResultBuilder':
        """
        Set the file name
        
        Args:
            file_name: Name of the file
            
        Returns:
            Self for method chaining
        """
        self._result['file_name'] = file_name
        return self
    
    def file_size(self, file_size: int) -> 'ResultBuilder':
        """
        Set the file size in bytes
        
        Args:
            file_size: Size of the file in bytes
            
        Returns:
            Self for method chaining
        """
        self._result['file_size'] = file_size
        return self
    
    def file_format(self, file_format: str) -> 'ResultBuilder':
        """
        Set the file format/extension
        
        Args:
            file_format: File format (e.g., '.mp3', 'json')
            
        Returns:
            Self for method chaining
        """
        self._result['file_format'] = file_format
        return self
    
    def last_modified(self, last_modified: str) -> 'ResultBuilder':
        """
        Set the last modified timestamp
        
        Args:
            last_modified: ISO format timestamp
            
        Returns:
            Self for method chaining
        """
        self._result['last_modified'] = last_modified
        return self
    
    def data(self, data: Dict[str, Any]) -> 'ResultBuilder':
        """
        Set the result data
        
        Args:
            data: Dictionary containing result data
            
        Returns:
            Self for method chaining
        """
        self._result['data'] = data
        return self
    
    def metadata(self, metadata: Dict[str, Any]) -> 'ResultBuilder':
        """
        Set the metadata
        
        Args:
            metadata: Dictionary containing metadata
            
        Returns:
            Self for method chaining
        """
        self._result['metadata'] = metadata
        return self
    
    def validation(self, validation: Dict[str, Any]) -> 'ResultBuilder':
        """
        Set the validation result
        
        Args:
            validation: Dictionary containing validation results
            
        Returns:
            Self for method chaining
        """
        self._result['validation'] = validation
        return self
    
    def output_files(self, output_files: Dict[str, Any]) -> 'ResultBuilder':
        """
        Set the output files
        
        Args:
            output_files: Dictionary containing output file information
            
        Returns:
            Self for method chaining
        """
        self._result['output_files'] = output_files
        return self
    
    def formats_generated(self, formats: List[str]) -> 'ResultBuilder':
        """
        Set the generated formats
        
        Args:
            formats: List of generated format types
            
        Returns:
            Self for method chaining
        """
        self._result['formats_generated'] = formats
        return self
    
    def transcription_result(self, transcription_result: Dict[str, Any]) -> 'ResultBuilder':
        """
        Set the transcription result
        
        Args:
            transcription_result: Dictionary containing transcription results
            
        Returns:
            Self for method chaining
        """
        self._result['transcription_result'] = transcription_result
        return self
    
    def session_id(self, session_id: str) -> 'ResultBuilder':
        """
        Set the session ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Self for method chaining
        """
        self._result['session_id'] = session_id
        return self
    
    def timestamp(self, timestamp: Optional[str] = None) -> 'ResultBuilder':
        """
        Set the timestamp
        
        Args:
            timestamp: ISO format timestamp (uses current time if None)
            
        Returns:
            Self for method chaining
        """
        self._result['timestamp'] = timestamp or self._timestamp
        return self
    
    def total_files(self, total_files: int) -> 'ResultBuilder':
        """
        Set the total number of files
        
        Args:
            total_files: Total number of files processed
            
        Returns:
            Self for method chaining
        """
        self._result['total_files'] = total_files
        return self
    
    def successful_files(self, successful_files: int) -> 'ResultBuilder':
        """
        Set the number of successful files
        
        Args:
            successful_files: Number of successfully processed files
            
        Returns:
            Self for method chaining
        """
        self._result['successful_files'] = successful_files
        return self
    
    def failed_files(self, failed_files: int) -> 'ResultBuilder':
        """
        Set the number of failed files
        
        Args:
            failed_files: Number of failed files
            
        Returns:
            Self for method chaining
        """
        self._result['failed_files'] = failed_files
        return self
    
    def success_rate(self, success_rate: float) -> 'ResultBuilder':
        """
        Set the success rate percentage
        
        Args:
            success_rate: Success rate as a percentage (0.0 to 100.0)
            
        Returns:
            Self for method chaining
        """
        self._result['success_rate'] = success_rate
        return self
    
    def results(self, results: List[Dict[str, Any]]) -> 'ResultBuilder':
        """
        Set the list of individual results
        
        Args:
            results: List of individual processing results
            
        Returns:
            Self for method chaining
        """
        self._result['results'] = results
        return self
    
    def failed_files_details(self, failed_details: List[Dict[str, Any]]) -> 'ResultBuilder':
        """
        Set the details of failed files
        
        Args:
            failed_details: List of dictionaries containing failure details
            
        Returns:
            Self for method chaining
        """
        self._result['failed_files_details'] = failed_details
        return self
    
    def recovery_info(self, recovery_attempted: bool, recovery_successful: bool = False, 
                     recovery_action: Optional[str] = None) -> 'ResultBuilder':
        """
        Set recovery information
        
        Args:
            recovery_attempted: Whether recovery was attempted
            recovery_successful: Whether recovery was successful
            recovery_action: Description of recovery action taken
            
        Returns:
            Self for method chaining
        """
        recovery_info = {
            'recovery_attempted': recovery_attempted,
            'recovery_successful': recovery_successful
        }
        if recovery_action:
            recovery_info['recovery_action'] = recovery_action
        
        self._result['recovery_info'] = recovery_info
        return self
    
    def operation_type(self, operation_type: str) -> 'ResultBuilder':
        """
        Set the operation type
        
        Args:
            operation_type: Type of operation performed
            
        Returns:
            Self for method chaining
        """
        self._result['operation_type'] = operation_type
        return self
    
    def engine_info(self, engine: str, model: Optional[str] = None) -> 'ResultBuilder':
        """
        Set engine and model information
        
        Args:
            engine: Transcription engine used
            model: Model used (optional)
            
        Returns:
            Self for method chaining
        """
        engine_info = {'engine': engine}
        if model:
            engine_info['model'] = model
        self._result['engine_info'] = engine_info
        return self
    
    def add_custom_field(self, key: str, value: Any) -> 'ResultBuilder':
        """
        Add a custom field to the result
        
        Args:
            key: Field name
            value: Field value
            
        Returns:
            Self for method chaining
        """
        self._result[key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        Build and return the final result dictionary
        
        Returns:
            Complete result dictionary
        """
        # Ensure timestamp is always present
        if 'timestamp' not in self._result:
            self._result['timestamp'] = self._timestamp
        
        # Ensure errors and warnings are included
        if self._errors:
            self._result['errors'] = self._errors
        if self._warnings:
            self._result['warnings'] = self._warnings
        if self._performance_metrics:
            self._result['performance_metrics'] = self._performance_metrics
        
        return self._result.copy()
    
    @classmethod
    def create_validation_success(cls, path: Path) -> Dict[str, Any]:
        """
        Create a validation success result
        
        Args:
            path: Path object of the validated file
            
        Returns:
            Validation success result dictionary
        """
        file_size = path.stat().st_size
        return (cls()
                .success(True)
                .file_path(str(path))
                .file_name(path.name)
                .file_size(file_size)
                .file_format(path.suffix.lower())
                .last_modified(datetime.fromtimestamp(path.stat().st_mtime).isoformat())
                .build())
    
    @classmethod
    def create_validation_error(cls, error_message: str, error_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a validation error result
        
        Args:
            error_message: Description of the validation error
            error_type: Type of validation error
            
        Returns:
            Validation error result dictionary
        """
        return (cls()
                .success(False)
                .error(error_message, error_type, 'validation', 'medium')
                .build())
    
    @classmethod
    def create_batch_result(cls, success: bool, error: Optional[str] = None, 
                          total_files: int = 0, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a standardized batch result
        
        Args:
            success: Whether the batch was successful
            error: Error message if applicable
            total_files: Total number of files
            session_id: Session identifier
            
        Returns:
            Standardized batch result dictionary
        """
        builder = (cls()
                  .success(success)
                  .total_files(total_files)
                  .successful_files(0)
                  .failed_files(total_files)
                  .success_rate(0.0)
                  .results([])
                  .failed_files_details([]))
        
        if error:
            builder.error(error, 'BatchProcessingError', 'processing', 'high')
        
        if session_id:
            builder.session_id(session_id)
        
        return builder.build()
    
    @classmethod
    def create_success_result(cls, output_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a success result for output processing
        
        Args:
            output_results: Dictionary containing output results
            
        Returns:
            Success result dictionary
        """
        return (cls()
                .success(True)
                .output_files(output_results)
                .formats_generated(list(output_results.keys()))
                .build())
    
    @classmethod
    def create_failure_result(cls, error_message: str, 
                            transcription_result: Optional[Dict[str, Any]] = None,
                            error_type: str = None, error_category: str = None) -> Dict[str, Any]:
        """
        Create a failure result
        
        Args:
            error_message: Description of the failure
            transcription_result: Optional transcription result data
            error_type: Type of error
            error_category: Category of error
            
        Returns:
            Failure result dictionary
        """
        builder = cls().success(False).error(error_message, error_type, error_category)
        
        if transcription_result:
            builder.transcription_result(transcription_result)
        
        return builder.build()
    
    @classmethod
    def create_already_saved_result(cls) -> Dict[str, Any]:
        """
        Create a result for already saved output
        
        Returns:
            Already saved result dictionary
        """
        return (cls()
                .success(True)
                .add_custom_field('message', 'Transcription service already saved output, skipping duplicate save')
                .build())
    
    @classmethod
    def create_pipeline_result(cls, success: bool, context: Dict[str, Any], 
                             data: Dict[str, Any] = None, errors: List[Dict[str, Any]] = None,
                             warnings: List[str] = None, performance_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a standardized pipeline result
        
        Args:
            success: Whether the pipeline was successful
            context: Processing context information
            data: Processing data
            errors: List of errors
            warnings: List of warnings
            performance_metrics: Performance metrics
            
        Returns:
            Standardized pipeline result dictionary
        """
        builder = cls().success(success)
        
        # Add context information
        if context.get('session_id'):
            builder.session_id(context['session_id'])
        if context.get('file_path'):
            builder.file_path(context['file_path'])
        if context.get('operation_type'):
            builder.operation_type(context['operation_type'])
        
        # Add data
        if data:
            builder.data(data)
        
        # Add errors
        if errors:
            for error in errors:
                builder.add_error(error)
        
        # Add warnings
        if warnings:
            for warning in warnings:
                builder.warning(warning)
        
        # Add performance metrics
        if performance_metrics:
            for metric_name, metric_value in performance_metrics.items():
                if isinstance(metric_value, dict):
                    builder.performance_metric(metric_name, metric_value.get('value'), metric_value.get('unit'))
                else:
                    builder.performance_metric(metric_name, metric_value)
        
        return builder.build()
    
    @classmethod
    def create_transcription_result(cls, transcription: str, segments: List[Dict[str, Any]] = None,
                                  metadata: Dict[str, Any] = None, engine: str = None, 
                                  model: str = None, processing_time: float = None) -> Dict[str, Any]:
        """
        Create a standardized transcription result
        
        Args:
            transcription: Transcribed text
            segments: Transcription segments
            metadata: Audio metadata
            engine: Transcription engine
            model: Model used
            processing_time: Processing time in seconds
            
        Returns:
            Standardized transcription result dictionary
        """
        builder = cls().success(True)
        
        # Add transcription data
        transcription_data = {'transcription': transcription}
        if segments:
            transcription_data['segments'] = segments
        if metadata:
            transcription_data['metadata'] = metadata
        
        builder.data(transcription_data)
        
        # Add engine information
        if engine:
            builder.engine_info(engine, model)
        
        # Add performance metrics
        if processing_time:
            builder.processing_time(processing_time)
        
        return builder.build()
