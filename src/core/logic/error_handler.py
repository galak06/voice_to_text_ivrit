"""
Error Handling Service
Provides standardized error handling patterns across the application
"""

from typing import Dict, Any, Optional, Callable, Type, Union, List
import logging
from datetime import datetime
from functools import wraps
import traceback
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for categorization"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    VALIDATION = "validation"
    PROCESSING = "processing"
    TRANSCRIPTION = "transcription"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Structured error context information"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    context: str
    operation: Optional[str] = None
    file_path: Optional[str] = None
    error_type: str = ""
    error_message: str = ""
    additional_info: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class ErrorRecoveryStrategy:
    """Base class for error recovery strategies"""
    
    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        """Check if this strategy can handle the given error"""
        pass
    
    def attempt_recovery(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Attempt to recover from the error"""
        pass


class FileSystemRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for file system errors"""
    
    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        return context.category == ErrorCategory.FILE_SYSTEM
    
    def attempt_recovery(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Attempt file system error recovery"""
        if "Permission denied" in str(error):
            # Try to fix permissions
            try:
                if context.file_path:
                    Path(context.file_path).chmod(0o644)
                    return {'success': True, 'action': 'fixed_permissions'}
            except Exception as recovery_error:
                logger.warning(f"Failed to fix permissions: {recovery_error}")
        
        return {'success': False, 'action': 'no_recovery_possible'}


class NetworkRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for network errors"""
    
    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        return context.category == ErrorCategory.NETWORK
    
    def attempt_recovery(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Attempt network error recovery with exponential backoff"""
        import time
        import random
        
        # Simple exponential backoff
        backoff_time = random.uniform(1, 5)
        time.sleep(backoff_time)
        
        return {'success': True, 'action': 'retry_with_backoff', 'backoff_time': backoff_time}


class ErrorHandler:
    """
    Centralized error handling service with recovery strategies and thread safety
    
    This class follows the Single Responsibility Principle by handling
    all error-related operations consistently across the application.
    """
    
    def __init__(self, config_manager):
        """Initialize error handler with configuration"""
        self.config_manager = config_manager
        self.config = config_manager.config
        self._error_count = 0
        self._error_history: List[ErrorContext] = []
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self.recovery_strategies: List[ErrorRecoveryStrategy] = [
            FileSystemRecoveryStrategy(),
            NetworkRecoveryStrategy()
        ]
    
    @property
    def error_count(self) -> int:
        """Thread-safe access to error count"""
        with self._lock:
            return self._error_count
    
    @property
    def error_history(self) -> List[ErrorContext]:
        """Thread-safe access to error history"""
        with self._lock:
            return self._error_history.copy()
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on exception type hierarchy"""
        error_type = type(error)
        
        # File system errors
        if issubclass(error_type, (OSError, IOError, FileNotFoundError, PermissionError)):
            return ErrorCategory.FILE_SYSTEM
        
        # Network errors
        if issubclass(error_type, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK
        
        # Validation errors
        if issubclass(error_type, (ValueError, TypeError, AttributeError)):
            return ErrorCategory.VALIDATION
        
        # Configuration errors
        if issubclass(error_type, (KeyError, ImportError)):
            return ErrorCategory.CONFIGURATION
        
        # Resource errors
        if issubclass(error_type, (MemoryError, OverflowError)):
            return ErrorCategory.RESOURCE
        
        # Check error message for additional context
        error_str = str(error).lower()
        if any(keyword in error_str for keyword in ['transcription', 'audio', 'model', 'whisper']):
            return ErrorCategory.TRANSCRIPTION
        elif any(keyword in error_str for keyword in ['processing', 'pipeline']):
            return ErrorCategory.PROCESSING
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on error type and category"""
        error_type = type(error)
        
        # Critical errors
        if issubclass(error_type, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.FILE_SYSTEM, ErrorCategory.NETWORK]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.TRANSCRIPTION, ErrorCategory.VALIDATION]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        return ErrorSeverity.LOW
    
    def _attempt_recovery(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Attempt to recover from the error using available strategies"""
        for strategy in self.recovery_strategies:
            if strategy.can_handle(error, context):
                try:
                    recovery_result = strategy.attempt_recovery(error, context)
                    context.recovery_attempted = True
                    context.recovery_successful = recovery_result.get('success', False)
                    return recovery_result
                except Exception as recovery_error:
                    logger.warning(f"Recovery strategy failed: {recovery_error}")
        
        return {'success': False, 'action': 'no_recovery_strategy_available'}
    
    def handle_error(self, error: Exception, context: str, operation: str = None, 
                    file_path: str = None, **kwargs) -> Dict[str, Any]:
        """
        Handle an error with standardized logging and response format
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            operation: Specific operation being performed
            file_path: Path to file being processed (if applicable)
            **kwargs: Additional context information
            
        Returns:
            Standardized error response dictionary
        """
        with self._lock:
            self._error_count += 1
            error_id = f"ERR_{self._error_count:06d}"
        
        # Categorize and determine severity
        category = self._categorize_error(error)
        severity = self._determine_severity(error, category)
        
        # Create error context
        error_context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            context=context,
            operation=operation,
            file_path=file_path,
            error_type=type(error).__name__,
            error_message=str(error),
            additional_info=kwargs,
            stack_trace=traceback.format_exc() if self.config.system and self.config.system.debug else None
        )
        
        # Attempt recovery
        recovery_result = self._attempt_recovery(error, error_context)
        
        # Add to history (thread-safe)
        with self._lock:
            self._error_history.append(error_context)
        
        # Log error with appropriate level
        log_message = f"❌ {error_id} - {context}: {error}"
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Return standardized error response
        return {
            'success': False,
            'error_id': error_id,
            'error': str(error),
            'error_type': type(error).__name__,
            'category': category.value,
            'severity': severity.value,
            'context': context,
            'operation': operation,
            'file_path': file_path,
            'timestamp': error_context.timestamp.isoformat(),
            'recovery_attempted': error_context.recovery_attempted,
            'recovery_successful': error_context.recovery_successful,
            'recovery_action': recovery_result.get('action'),
            **kwargs
        }
    
    def handle_operation_error(self, operation: str, error: Exception, 
                             context: str = None, **kwargs) -> Dict[str, Any]:
        """
        Handle errors during specific operations
        
        Args:
            operation: Operation being performed
            error: The exception that occurred
            context: Additional context
            **kwargs: Additional information
            
        Returns:
            Standardized error response
        """
        return self.handle_error(
            error=error,
            context=context or "Operation execution",
            operation=operation,
            **kwargs
        )
    
    def handle_file_processing_error(self, error: Exception, file_path: str, 
                                   operation: str = None, **kwargs) -> Dict[str, Any]:
        """
        Handle errors during file processing
        
        Args:
            error: The exception that occurred
            file_path: Path to the file being processed
            operation: Specific operation being performed
            **kwargs: Additional information
            
        Returns:
            Standardized error response
        """
        return self.handle_error(
            error=error,
            context="File processing",
            operation=operation,
            file_path=file_path,
            **kwargs
        )
    
    def handle_transcription_error(self, error: Exception, audio_file: str, 
                                 engine: str = None, model: str = None, **kwargs) -> Dict[str, Any]:
        """
        Handle errors during transcription
        
        Args:
            error: The exception that occurred
            audio_file: Path to the audio file
            engine: Transcription engine being used
            model: Model being used
            **kwargs: Additional information
            
        Returns:
            Standardized error response
        """
        return self.handle_error(
            error=error,
            context="Transcription",
            operation=f"{engine or 'unknown'}-{model or 'unknown'}",
            file_path=audio_file,
            engine=engine,
            model=model,
            **kwargs
        )
    
    def safe_execute(self, func: Callable, *args, context: str = None, 
                    operation: str = None, **kwargs) -> Dict[str, Any]:
        """
        Safely execute a function with error handling
        
        Args:
            func: Function to execute
            *args: Function arguments
            context: Context for error handling
            operation: Operation name
            **kwargs: Additional context and function kwargs
            
        Returns:
            Dictionary with success status and result or error
        """
        try:
            result = func(*args, **kwargs)
            return {
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
        except (ValueError, TypeError) as e:
            return self.handle_operation_error(
                operation=operation or func.__name__,
                error=e,
                context=context or "Function execution"
            )
        except (OSError, IOError) as e:
            return self.handle_operation_error(
                operation=operation or func.__name__,
                error=e,
                context=context or "Function execution"
            )
        except Exception as e:
            return self.handle_operation_error(
                operation=operation or func.__name__,
                error=e,
                context=context or "Function execution"
            )
    
    def retry_operation(self, func: Callable, max_attempts: int = None, 
                       *args, **kwargs) -> Dict[str, Any]:
        """
        Execute a function with retry logic
        
        Args:
            func: Function to execute
            max_attempts: Maximum number of retry attempts
            *args: Function arguments
            **kwargs: Function kwargs and retry configuration
            
        Returns:
            Dictionary with success status and result or error
        """
        if max_attempts is None:
            max_attempts = self.config.system.retry_attempts if self.config.system else 3
        
        constants = self.config.system.constants if self.config.system else None
        max_backoff = constants.max_backoff_seconds if constants else 30
        backoff_base = constants.exponential_backoff_base if constants else 2
        
        for attempt in range(1, max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                return {
                    'success': True,
                    'result': result,
                    'attempts': attempt,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                if attempt == max_attempts:
                    return self.handle_operation_error(
                        operation=func.__name__,
                        error=e,
                        context=f"Retry operation (attempts: {attempt})"
                    )
                
                # Calculate backoff time
                backoff_time = min(backoff_base ** (attempt - 1), max_backoff)
                logger.warning(f"⚠️ Attempt {attempt}/{max_attempts} failed for {func.__name__}, "
                             f"retrying in {backoff_time}s: {e}")
                
                import time
                time.sleep(backoff_time)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        with self._lock:
            category_counts = {}
            severity_counts = {}
            
            for error in self._error_history:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            return {
                'total_errors': self._error_count,
                'error_history': [self._error_context_to_dict(error) for error in self._error_history[-10:]],  # Last 10 errors
                'category_breakdown': category_counts,
                'severity_breakdown': severity_counts,
                'timestamp': datetime.now().isoformat()
            }
    
    def _error_context_to_dict(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Convert ErrorContext to dictionary for serialization"""
        return {
            'error_id': error_context.error_id,
            'timestamp': error_context.timestamp.isoformat(),
            'category': error_context.category.value,
            'severity': error_context.severity.value,
            'context': error_context.context,
            'operation': error_context.operation,
            'file_path': error_context.file_path,
            'error_type': error_context.error_type,
            'error_message': error_context.error_message,
            'recovery_attempted': error_context.recovery_attempted,
            'recovery_successful': error_context.recovery_successful
        }
    
    def clear_error_history(self):
        """Clear error history"""
        with self._lock:
            self._error_history.clear()
            self._error_count = 0
    
    @contextmanager
    def error_context(self, context: str, operation: str = None, **kwargs):
        """
        Context manager for error handling
        
        Args:
            context: Context for error handling
            operation: Operation name
            **kwargs: Additional context
        """
        try:
            yield
        except Exception as e:
            self.handle_error(e, context, operation, **kwargs)
            raise


def error_handler_decorator(context: str = None, operation: str = None):
    """
    Decorator for automatic error handling
    
    Args:
        context: Context for error handling
        operation: Operation name
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get error handler from self if it's a method
            error_handler = None
            if args and hasattr(args[0], 'error_handler'):
                error_handler = args[0].error_handler
            
            if error_handler:
                return error_handler.safe_execute(
                    func, *args, context=context, operation=operation, **kwargs
                )
            else:
                # Fallback to basic error handling
                try:
                    result = func(*args, **kwargs)
                    return {
                        'success': True,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {e}")
                    return {
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'timestamp': datetime.now().isoformat()
                    }
        return wrapper
    return decorator
