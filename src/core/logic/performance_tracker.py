"""
Performance Tracking Service
Handles performance monitoring and statistics tracking
"""

from typing import Dict, Any, List, Optional
import logging
import threading
from datetime import datetime
import time

from src.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks performance metrics and statistics
    
    This class follows the Single Responsibility Principle by focusing
    solely on performance monitoring and statistics tracking.
    """
    
    def __init__(self, config_manager: ConfigManager, max_history_size: int = 1000):
        """
        Initialize performance tracker with resource limits
        
        Args:
            config_manager: Configuration manager instance
            max_history_size: Maximum size of metrics history to prevent memory leaks
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.max_history_size = max_history_size
        
        # Get constants from configuration (robust to mocked config without attributes)
        try:
            system_cfg = getattr(self.config, 'system', None)
            self.constants = getattr(system_cfg, 'constants', None) if system_cfg else None
        except Exception:
            self.constants = None
        
        # Initialize tracking data
        self.processing_stats: Dict[str, Any] = {
            'total_files_processed': 0,
            'successful_transcriptions': 0,
            'failed_transcriptions': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'memory_usage': [],
            'cpu_usage': [],
            'start_time': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        # Performance monitoring
        self._performance_monitor = None
        self._initialize_performance_monitor()
        
        # Thread safety
        self._lock = threading.RLock()
    
    def _initialize_performance_monitor(self):
        """Initialize performance monitor if available"""
        try:
            from src.core.logic.performance_monitor import PerformanceMonitor
            self._performance_monitor = PerformanceMonitor()
        except ImportError:
            logger.warning("PerformanceMonitor not available, using basic tracking")
    
    def track_file_processing(self, processing_time: float, success: bool, 
                            file_path: str = None, **kwargs):
        """
        Track processing of a single file
        
        Args:
            processing_time: Time taken to process the file
            success: Whether processing was successful
            file_path: Path to the processed file
            **kwargs: Additional tracking data
        """
        self._update_basic_statistics(processing_time, success)
        self._track_advanced_metrics()
        self._log_performance_if_needed(processing_time, file_path)
    
    def _update_basic_statistics(self, processing_time: float, success: bool):
        """Update basic processing statistics"""
        self.processing_stats['total_files_processed'] += 1
        self.processing_stats['total_processing_time'] += processing_time
        total_files_processed = self.processing_stats['total_files_processed']
        self.processing_stats['average_processing_time'] = (
            self.processing_stats['total_processing_time'] / total_files_processed if total_files_processed > 0 else 0.0
        )
        self.processing_stats['last_activity'] = datetime.now().isoformat()
        
        if success:
            self.processing_stats['successful_transcriptions'] += 1
        else:
            self.processing_stats['failed_transcriptions'] += 1
    
    def _track_advanced_metrics(self):
        """Track advanced performance metrics"""
        if self._performance_monitor:
            self._track_performance_metrics()
    
    def _log_performance_if_needed(self, processing_time: float, file_path: str = None):
        """Log performance if processing took significant time"""
        if self._should_log_performance(processing_time):
            self._log_performance_summary(processing_time, file_path)
    
    def track_batch_processing(self, total_files: int, successful_files: int, 
                             total_time: float, **kwargs):
        """
        Track batch processing statistics
        
        Args:
            total_files: Total number of files in batch
            successful_files: Number of successfully processed files
            total_time: Total time for batch processing
            **kwargs: Additional tracking data
        """
        # Update batch-specific statistics
        self.processing_stats['total_files_processed'] += total_files
        self.processing_stats['successful_transcriptions'] += successful_files
        self.processing_stats['failed_transcriptions'] += (total_files - successful_files)
        self.processing_stats['total_processing_time'] += total_time
        total_files_processed = self.processing_stats['total_files_processed']
        self.processing_stats['average_processing_time'] = (
            self.processing_stats['total_processing_time'] / total_files_processed if total_files_processed > 0 else 0.0
        )
        self.processing_stats['last_activity'] = datetime.now().isoformat()
        
        # Track performance metrics
        if self._performance_monitor:
            self._track_performance_metrics()
        
        # Log batch performance summary
        self._log_batch_performance_summary(total_files, successful_files, total_time)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report
        
        Returns:
            Dictionary containing performance metrics and statistics
        """
        report = {
            'processing_stats': self.processing_stats.copy(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add performance monitor data if available
        if self._performance_monitor:
            try:
                monitor_report = self._performance_monitor.get_performance_report()
                report['performance_metrics'] = monitor_report
            except Exception as e:
                logger.warning(f"Failed to get performance monitor report: {e}")
                report['performance_metrics'] = {}
        
        return report
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics
        
        Returns:
            Dictionary containing current metrics
        """
        if self._performance_monitor:
            try:
                return self._performance_monitor.get_current_metrics()
            except Exception as e:
                logger.warning(f"Failed to get current metrics: {e}")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'processing_stats': self.processing_stats.copy()
        }
    
    def reset_statistics(self):
        """Reset all performance statistics"""
        self.processing_stats = {
            'total_files_processed': 0,
            'successful_transcriptions': 0,
            'failed_transcriptions': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'memory_usage': [],
            'cpu_usage': [],
            'start_time': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        if self._performance_monitor:
            try:
                self._performance_monitor.reset_metrics()
            except Exception as e:
                logger.warning(f"Failed to reset performance monitor: {e}")
        
        logger.info("Performance statistics reset")

    # Backwards-compatibility methods expected by application/tests
    def record_file_processing(self, processing_time: float, success: bool, file_path: Optional[str] = None):
        """Alias to track_file_processing for compatibility"""
        self.track_file_processing(processing_time=processing_time, success=success, file_path=file_path)

    def record_batch_processing(self, total_files: int = 0, successful_files: int = 0, total_time: float = 0.0, **kwargs):
        """Alias to track_batch_processing for compatibility; accepts extra kwargs and ignores them"""
        self.track_batch_processing(total_files=total_files, successful_files=successful_files, total_time=total_time)

    def get_summary(self) -> Dict[str, Any]:
        """Return a lightweight summary for status endpoints"""
        return self.get_statistics_summary()
    
    def cleanup(self):
        """Clean up performance tracking resources"""
        if self._performance_monitor:
            try:
                self._performance_monitor.cleanup()
            except Exception as e:
                logger.warning(f"Failed to cleanup performance monitor: {e}")
    
    def _track_performance_metrics(self):
        """Track current performance metrics with resource limits and thread safety"""
        if self._performance_monitor:
            try:
                with self._lock:  # Thread safety
                    current_metrics = self._performance_monitor.get_current_metrics()
                    
                    # Enforce memory limits before appending
                    if len(self.processing_stats['memory_usage']) >= self.max_history_size:
                        self.processing_stats['memory_usage'] = self.processing_stats['memory_usage'][-self.max_history_size:]
                    if len(self.processing_stats['cpu_usage']) >= self.max_history_size:
                        self.processing_stats['cpu_usage'] = self.processing_stats['cpu_usage'][-self.max_history_size:]
                    
                    self.processing_stats['memory_usage'].append(current_metrics.get('memory_mb', 0))
                    self.processing_stats['cpu_usage'].append(current_metrics.get('cpu_percent', 0))
                    
                    # Additional limit check for constants-based limits
                    max_history = (self.constants.max_processing_stats_history 
                                  if self.constants else self.max_history_size)
                    
                    if len(self.processing_stats['memory_usage']) > max_history:
                        self.processing_stats['memory_usage'] = self.processing_stats['memory_usage'][-max_history:]
                    if len(self.processing_stats['cpu_usage']) > max_history:
                        self.processing_stats['cpu_usage'] = self.processing_stats['cpu_usage'][-max_history:]
                        
            except Exception as e:
                logger.warning(f"Failed to track performance metrics: {e}")
    
    def _should_log_performance(self, processing_time: float) -> bool:
        """
        Determine if performance should be logged
        
        Args:
            processing_time: Time taken for processing
            
        Returns:
            True if performance should be logged
        """
        threshold = (self.constants.performance_log_threshold_seconds 
                    if self.constants else 30)
        return processing_time > threshold
    
    def _log_performance_summary(self, processing_time: float, file_path: str = None):
        """
        Log performance summary for a file
        
        Args:
            processing_time: Time taken for processing
            file_path: Path to the processed file
        """
        file_info = f" for {file_path}" if file_path else ""
        logger.info(f"📊 File processing completed in {processing_time:.1f}s{file_info}")
        
        if self._performance_monitor:
            try:
                self._performance_monitor.log_performance_summary()
            except Exception as e:
                logger.warning(f"Failed to log performance summary: {e}")
    
    def _log_batch_performance_summary(self, total_files: int, successful_files: int, 
                                     total_time: float):
        """
        Log batch performance summary
        
        Args:
            total_files: Total number of files
            successful_files: Number of successful files
            total_time: Total processing time
        """
        success_rate = (successful_files / total_files) * 100 if total_files > 0 else 0
        avg_time = total_time / total_files if total_files > 0 else 0
        
        logger.info(f"📊 BATCH PERFORMANCE SUMMARY:")
        logger.info(f"   - Total files: {total_files}")
        logger.info(f"   - Successful: {successful_files}")
        logger.info(f"   - Success rate: {success_rate:.1f}%")
        logger.info(f"   - Total time: {total_time:.1f}s")
        logger.info(f"   - Average time per file: {avg_time:.1f}s")
        
        if self._performance_monitor:
            try:
                self._performance_monitor.log_performance_summary()
            except Exception as e:
                logger.warning(f"Failed to log batch performance summary: {e}")
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current statistics
        
        Returns:
            Dictionary containing statistics summary
        """
        stats = self.processing_stats
        
        return {
            'total_files_processed': stats['total_files_processed'],
            'successful_transcriptions': stats['successful_transcriptions'],
            'failed_transcriptions': stats['failed_transcriptions'],
            'success_rate': (stats['successful_transcriptions'] / stats['total_files_processed'] * 100 
                           if stats['total_files_processed'] > 0 else 0),
            'average_processing_time': stats['average_processing_time'],
            'total_processing_time': stats['total_processing_time'],
            'uptime': self._calculate_uptime(),
            'last_activity': stats['last_activity'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_uptime(self) -> str:
        """
        Calculate application uptime
        
        Returns:
            Uptime as a formatted string
        """
        try:
            start_time = datetime.fromisoformat(self.processing_stats['start_time'])
            uptime = datetime.now() - start_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            else:
                return f"{minutes}m {seconds}s"
        except Exception:
            return "Unknown"
