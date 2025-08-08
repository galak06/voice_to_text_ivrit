#!/usr/bin/env python3
"""
Performance Monitor
Tracks application performance metrics and resource usage
"""

import time
import psutil
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    open_files: int

class PerformanceMonitor:
    """Monitors application performance and resource usage"""
    
    def __init__(self, monitoring_interval: float = 5.0):
        """
        Initialize performance monitor
        
        Args:
            monitoring_interval: Interval between measurements in seconds
        """
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.start_time = time.time()
        self.last_measurement = 0
        self.process = psutil.Process()
        
        # Initialize baseline measurements
        self._baseline_io = psutil.disk_io_counters()
        self._baseline_network = psutil.net_io_counters()
        
        logger.info("Performance monitor initialized")
    
    def measure_performance(self) -> PerformanceMetrics:
        """Measure current performance metrics"""
        try:
            # Get current time
            current_time = datetime.now().isoformat()
            
            # CPU and memory usage
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            
            # Disk I/O
            current_io = psutil.disk_io_counters()
            if current_io and self._baseline_io:
                disk_io_read_mb = (current_io.read_bytes - self._baseline_io.read_bytes) / 1024 / 1024
                disk_io_write_mb = (current_io.write_bytes - self._baseline_io.write_bytes) / 1024 / 1024
            else:
                disk_io_read_mb = 0.0
                disk_io_write_mb = 0.0
            
            # Network I/O
            current_network = psutil.net_io_counters()
            if current_network and self._baseline_network:
                network_sent_mb = (current_network.bytes_sent - self._baseline_network.bytes_sent) / 1024 / 1024
                network_recv_mb = (current_network.bytes_recv - self._baseline_network.bytes_recv) / 1024 / 1024
            else:
                network_sent_mb = 0.0
                network_recv_mb = 0.0
            
            # Thread and file information
            active_threads = self.process.num_threads()
            open_files = len(self.process.open_files())
            
            # Create metrics object
            metrics = PerformanceMetrics(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_threads=active_threads,
                open_files=open_files
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 measurements to prevent memory bloat
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error measuring performance: {e}")
            # Return empty metrics on error
            return PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                active_threads=0,
                open_files=0
            )
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics as dictionary"""
        metrics = self.measure_performance()
        return asdict(metrics)
    
    def get_average_metrics(self, window_minutes: int = 5) -> Dict[str, float]:
        """Get average metrics over a time window"""
        if not self.metrics_history:
            return {}
        
        # Calculate time window
        window_seconds = window_minutes * 60
        cutoff_time = time.time() - window_seconds
        
        # Filter metrics within window
        recent_metrics = [
            m for m in self.metrics_history
            if time.mktime(datetime.fromisoformat(m.timestamp).timetuple()) > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages
        avg_metrics = {
            'cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            'memory_mb': sum(m.memory_mb for m in recent_metrics) / len(recent_metrics),
            'active_threads': sum(m.active_threads for m in recent_metrics) / len(recent_metrics),
            'open_files': sum(m.open_files for m in recent_metrics) / len(recent_metrics)
        }
        
        return avg_metrics
    
    def get_peak_metrics(self, window_minutes: int = 5) -> Dict[str, float]:
        """Get peak metrics over a time window"""
        if not self.metrics_history:
            return {}
        
        # Calculate time window
        window_seconds = window_minutes * 60
        cutoff_time = time.time() - window_seconds
        
        # Filter metrics within window
        recent_metrics = [
            m for m in self.metrics_history
            if time.mktime(datetime.fromisoformat(m.timestamp).timetuple()) > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate peaks
        peak_metrics = {
            'cpu_percent': max(m.cpu_percent for m in recent_metrics),
            'memory_percent': max(m.memory_percent for m in recent_metrics),
            'memory_mb': max(m.memory_mb for m in recent_metrics),
            'active_threads': max(m.active_threads for m in recent_metrics),
            'open_files': max(m.open_files for m in recent_metrics)
        }
        
        return peak_metrics
    
    def log_performance_summary(self):
        """Log a performance summary"""
        if not self.metrics_history:
            logger.info("No performance metrics available")
            return
        
        # Get current metrics
        current = self.get_current_metrics()
        
        # Get averages over last 5 minutes
        averages = self.get_average_metrics(5)
        
        # Get peaks over last 5 minutes
        peaks = self.get_peak_metrics(5)
        
        logger.info("📊 PERFORMANCE SUMMARY:")
        logger.info(f"   Current CPU: {current['cpu_percent']:.1f}% (Avg: {averages.get('cpu_percent', 0):.1f}%, Peak: {peaks.get('cpu_percent', 0):.1f}%)")
        logger.info(f"   Current Memory: {current['memory_mb']:.1f}MB ({current['memory_percent']:.1f}%)")
        logger.info(f"   Avg Memory: {averages.get('memory_mb', 0):.1f}MB ({averages.get('memory_percent', 0):.1f}%)")
        logger.info(f"   Peak Memory: {peaks.get('memory_mb', 0):.1f}MB ({peaks.get('memory_percent', 0):.1f}%)")
        logger.info(f"   Active Threads: {current['active_threads']} (Avg: {averages.get('active_threads', 0):.1f})")
        logger.info(f"   Open Files: {current['open_files']} (Avg: {averages.get('open_files', 0):.1f})")
        
        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        uptime_hours = uptime_seconds / 3600
        logger.info(f"   Uptime: {uptime_hours:.1f} hours")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        current = self.get_current_metrics()
        averages_5min = self.get_average_metrics(5)
        averages_1hour = self.get_average_metrics(60)
        peaks_1hour = self.get_peak_metrics(60)
        
        uptime_seconds = time.time() - self.start_time
        
        return {
            'current': current,
            'averages_5min': averages_5min,
            'averages_1hour': averages_1hour,
            'peaks_1hour': peaks_1hour,
            'uptime_seconds': uptime_seconds,
            'uptime_hours': uptime_seconds / 3600,
            'total_measurements': len(self.metrics_history),
            'monitoring_interval': self.monitoring_interval
        }
    
    def cleanup(self):
        """Clean up performance monitor resources"""
        try:
            # Clear history to free memory
            self.metrics_history.clear()
            logger.info("Performance monitor cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up performance monitor: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during cleanup
