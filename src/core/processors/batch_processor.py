"""
Batch Processing Service
Handles batch processing of audio files with retry logic and error recovery
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging
from datetime import datetime
import time
import concurrent.futures
import threading

from src.core.logic.error_handler import ErrorHandler
from src.utils.config_manager import ConfigManager
from src.core.logic.result_builder import ResultBuilder

if TYPE_CHECKING:
    from src.output_data import OutputManager

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Handles batch processing of audio files
    
    This class follows the Single Responsibility Principle by focusing
    solely on batch processing operations and error recovery.
    """
    
    def __init__(self, config_manager: ConfigManager, output_manager: 'OutputManager', 
                 error_handler: ErrorHandler, session_id: str, max_workers: int = None):
        """
        Initialize batch processor with concurrent processing support
        
        Args:
            config_manager: Configuration manager instance
            output_manager: Output manager instance
            error_handler: Error handler instance
            session_id: Current session ID
            max_workers: Maximum number of concurrent workers (defaults to config value)
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.output_manager = output_manager
        self.error_handler = error_handler
        self.session_id = session_id
        
        # Get constants from configuration
        self.constants = self.config.system.constants if self.config.system else None
        
        # Configure concurrent processing
        self.max_workers = max_workers or getattr(self.config.batch, 'max_workers', 4)
        self._lock = threading.RLock()  # Thread-safe lock for shared state
    
    def process_batch(self, audio_files: List[str], process_single_file_func: callable, 
                     **kwargs) -> Dict[str, Any]:
        """
        Process a batch of audio files with enhanced error recovery
        
        Args:
            audio_files: List of audio file paths to process
            process_single_file_func: Function to process individual files
            **kwargs: Additional parameters for file processing
            
        Returns:
            Dictionary containing batch processing results
        """
        if not audio_files:
            return ResultBuilder.create_batch_result(
                success=False,
                error="No audio files provided",
                total_files=0,
                session_id=self.session_id
            )
        
        logger.info(f"🎤 Processing batch of {len(audio_files)} files")
        
        # Process files with retry logic
        results = self._process_files_with_retry(audio_files, process_single_file_func, **kwargs)
        
        # Compile batch statistics
        batch_result = self._compile_batch_results(results, audio_files)
        
        # Log completion statistics
        self._log_batch_completion(batch_result)
        
        return batch_result
    
    def _process_files_with_retry(self, audio_files: List[str], 
                                 process_single_file_func: callable, **kwargs) -> List[Dict[str, Any]]:
        """
        Process files with retry logic and error recovery
        
        Args:
            audio_files: List of audio file paths
            process_single_file_func: Function to process individual files
            **kwargs: Additional parameters
            
        Returns:
            List of processing results
        """
        results = []
        
        # First pass: process all files
        results = self._process_files_initial_pass(audio_files, process_single_file_func, **kwargs)
        
        # Second pass: retry failed files
        retry_queue = self._build_retry_queue(results, audio_files, **kwargs)
        if retry_queue:
            self._retry_failed_files(retry_queue, results, process_single_file_func)
        
        return results
    
    def _process_files_initial_pass(self, audio_files: List[str], 
                                   process_single_file_func: callable, **kwargs) -> List[Dict[str, Any]]:
        """Process all files in initial pass with concurrent execution"""
        # Use concurrent processing for better performance
        if len(audio_files) > 1 and self.max_workers > 1:
            return self._process_files_concurrent(audio_files, process_single_file_func, **kwargs)
        else:
            # Fallback to sequential processing for small batches or single worker
            return self._process_files_sequential(audio_files, process_single_file_func, **kwargs)
    
    def _process_files_concurrent(self, audio_files: List[str], 
                                 process_single_file_func: callable, **kwargs) -> List[Dict[str, Any]]:
        """Process files concurrently using ThreadPoolExecutor"""
        logger.info(f"🚀 Starting concurrent processing with {self.max_workers} workers")
        
        results = [None] * len(audio_files)  # Pre-allocate results list
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._process_single_file_with_logging, 
                              audio_file, i+1, len(audio_files), 
                              process_single_file_func, **kwargs): i
                for i, audio_file in enumerate(audio_files)
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                    logger.info(f"✅ Concurrent task {index+1}/{len(audio_files)} completed")
                except (ValueError, TypeError) as e:
                    logger.error(f"❌ Validation error in concurrent task {index+1}/{len(audio_files)}: {e}")
                    results[index] = {
                        'success': False,
                        'error': str(e),
                        'error_type': 'validation',
                        'file': audio_files[index]
                    }
                except (OSError, IOError) as e:
                    logger.error(f"❌ File system error in concurrent task {index+1}/{len(audio_files)}: {e}")
                    results[index] = {
                        'success': False,
                        'error': str(e),
                        'error_type': 'file_system',
                        'file': audio_files[index]
                    }
                except Exception as e:
                    logger.error(f"❌ Unexpected error in concurrent task {index+1}/{len(audio_files)}: {e}")
                    results[index] = {
                        'success': False,
                        'error': str(e),
                        'error_type': 'unexpected',
                        'file': audio_files[index]
                    }
        
        return results
    
    def _process_files_sequential(self, audio_files: List[str], 
                                 process_single_file_func: callable, **kwargs) -> List[Dict[str, Any]]:
        """Process files sequentially (fallback method)"""
        logger.info(f"📝 Starting sequential processing of {len(audio_files)} files")
        
        results = []
        for i, audio_file in enumerate(audio_files, 1):
            result = self._process_single_file_with_logging(
                audio_file, i, len(audio_files), process_single_file_func, **kwargs
            )
            results.append(result)
        return results
    
    def _build_retry_queue(self, results: List[Dict[str, Any]], audio_files: List[str], 
                          **kwargs) -> List[Dict[str, Any]]:
        """Build queue of files that need retrying"""
        retry_queue = []
        for i, result in enumerate(results):
            if not result['success'] and self._should_retry():
                retry_queue.append({
                    'file': audio_files[i],
                    'kwargs': kwargs,
                    'attempts': 0,
                    'max_attempts': self.config.system.retry_attempts
                })
        return retry_queue
    
    def _process_single_file_with_logging(self, audio_file: str, file_index: int, 
                                         total_files: int, process_single_file_func: callable, 
                                         **kwargs) -> Dict[str, Any]:
        """
        Process a single file with logging and error handling
        
        Args:
            audio_file: Path to audio file
            file_index: Current file index
            total_files: Total number of files
            process_single_file_func: Function to process the file
            **kwargs: Additional parameters
            
        Returns:
            Processing result
        """
        try:
            logger.info(f"📊 Processing file {file_index}/{total_files}: {audio_file}")
            
            result = process_single_file_func(audio_file, **kwargs)
            
            if result['success']:
                logger.info(f"✅ File {file_index}/{total_files} completed successfully")
            else:
                logger.warning(f"❌ File {file_index}/{total_files} failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except (ValueError, TypeError) as e:
            error_result = self.error_handler.handle_file_processing_error(
                error=e,
                file_path=audio_file,
                operation="batch_processing"
            )
            logger.error(f"❌ Validation error processing {audio_file}: {e}")
            return error_result
        except (OSError, IOError) as e:
            error_result = self.error_handler.handle_file_processing_error(
                error=e,
                file_path=audio_file,
                operation="batch_processing"
            )
            logger.error(f"❌ File system error processing {audio_file}: {e}")
            return error_result
        except Exception as e:
            error_result = self.error_handler.handle_file_processing_error(
                error=e,
                file_path=audio_file,
                operation="batch_processing"
            )
            logger.error(f"❌ Unexpected error processing {audio_file}: {e}")
            return error_result
    
    def _retry_failed_files(self, retry_queue: List[Dict[str, Any]], 
                           results: List[Dict[str, Any]], 
                           process_single_file_func: callable):
        """
        Retry failed files with exponential backoff
        
        Args:
            retry_queue: Queue of files to retry
            results: Current results list
            process_single_file_func: Function to process files
        """
        logger.info(f"🔄 Retrying {len(retry_queue)} failed files...")
        
        for retry_item in retry_queue:
            retry_item['attempts'] += 1
            audio_file = retry_item['file']
            
            logger.info(f"🔄 Retry attempt {retry_item['attempts']}/{retry_item['max_attempts']} for {audio_file}")
            
            # Apply exponential backoff
            if retry_item['attempts'] > 1:
                backoff_time = self._calculate_backoff_time(retry_item['attempts'])
                logger.info(f"⏳ Waiting {backoff_time} seconds before retry...")
                time.sleep(backoff_time)
            
            # Retry processing
            result = self.error_handler.retry_operation(
                func=process_single_file_func,
                max_attempts=1,  # We're already in retry mode
                audio_file=audio_file,
                **retry_item['kwargs']
            )
            
            if result['success']:
                logger.info(f"✅ Retry successful for {audio_file}")
                # Update the original result in results list
                self._update_result_in_list(results, audio_file, result['result'])
            else:
                logger.warning(f"❌ Retry failed for {audio_file}: {result.get('error', 'Unknown error')}")
    
    def _compile_batch_results(self, results: List[Dict[str, Any]], 
                              audio_files: List[str]) -> Dict[str, Any]:
        """
        Compile batch processing results with statistics
        
        Args:
            results: List of processing results
            audio_files: Original list of audio files
            
        Returns:
            Compiled batch result
        """
        successful_files = sum(1 for r in results if r.get('success', False))
        failed_files = len(audio_files) - successful_files
        success_rate = (successful_files / len(audio_files)) * 100 if audio_files else 0
        
        return {
            'success': successful_files > 0,  # Consider batch successful if at least one file succeeded
            'total_files': len(audio_files),
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': success_rate,
            'results': results,
            'failed_files_details': self._extract_failed_files_details(results),
            'retry_attempts': self.config.system.retry_attempts if self.config.system else 0,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_failed_files_details(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract details of failed files
        
        Args:
            results: List of processing results
            
        Returns:
            List of failed file details
        """
        failed_files = []
        for result in results:
            if not result.get('success', False):
                failed_files.append({
                    'file': result.get('file_path') or result.get('file'),
                    'error': result.get('error', 'Unknown error'),
                    'attempt': result.get('attempts', 1)
                })
        return failed_files
    
    def _log_batch_completion(self, batch_result: Dict[str, Any]):
        """
        Log batch completion statistics
        
        Args:
            batch_result: Batch processing result
        """
        logger.info(f"📊 BATCH PROCESSING COMPLETE:")
        logger.info(f"   - Total files: {batch_result['total_files']}")
        logger.info(f"   - Successful: {batch_result['successful_files']}")
        logger.info(f"   - Failed: {batch_result['failed_files']}")
        logger.info(f"   - Success rate: {batch_result['success_rate']:.1f}%")
        
        if batch_result['failed_files_details']:
            logger.warning(f"❌ Failed files:")
            for failed_file in batch_result['failed_files_details']:
                logger.warning(f"   - {failed_file['file']}: {failed_file['error']} (attempts: {failed_file['attempt']})")
    
    def _should_retry(self) -> bool:
        """Check if retry is enabled in configuration"""
        return (self.config.system and 
                self.config.system.retry_attempts and 
                self.config.system.retry_attempts > 0)
    
    def _calculate_backoff_time(self, attempt: int) -> int:
        """
        Calculate backoff time for retry attempts
        
        Args:
            attempt: Current attempt number
            
        Returns:
            Backoff time in seconds
        """
        if not self.constants:
            return min(2 ** (attempt - 1), 30)
        
        max_backoff = self.constants.max_backoff_seconds
        backoff_base = self.constants.exponential_backoff_base
        
        return min(backoff_base ** (attempt - 1), max_backoff)
    
    def _update_result_in_list(self, results: List[Dict[str, Any]], 
                              audio_file: str, new_result: Dict[str, Any]):
        """
        Update a result in the results list
        
        Args:
            results: List of results to update
            audio_file: File path to match
            new_result: New result to replace with
        """
        for i, result in enumerate(results):
            if (result.get('file_path') == audio_file or 
                result.get('file') == audio_file):
                results[i] = new_result
                break
    
    def _create_batch_result(self, success: bool, error: str = None, 
                           total_files: int = 0, **kwargs) -> Dict[str, Any]:
        """
        Create a standardized batch result
        
        Args:
            success: Whether the batch was successful
            error: Error message if applicable
            total_files: Total number of files
            **kwargs: Additional result data
            
        Returns:
            Standardized batch result
        """
        return ResultBuilder.create_batch_result(
            success=success,
            error=error,
            total_files=total_files,
            session_id=self.session_id
        )
