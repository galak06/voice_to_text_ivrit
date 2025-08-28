#!/usr/bin/env python3
"""
Enhanced Progress Monitor for Transcription
Provides real-time monitoring of transcription progress with detailed statistics
"""

import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Thread, Lock
import re

logger = logging.getLogger(__name__)


@dataclass
class ChunkProgress:
    """Represents the progress of a single audio chunk"""
    chunk_number: int
    start_time: float
    end_time: float
    status: str  # 'processing', 'completed', 'failed'
    transcription: str
    word_count: int
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None


@dataclass
class TranscriptionProgress:
    """Overall transcription progress summary"""
    total_chunks: int
    completed_chunks: int
    failed_chunks: int
    current_chunk: int
    overall_progress: float
    elapsed_time: float
    estimated_remaining: float
    success_rate: float
    start_time: datetime
    current_chunk_start: Optional[datetime] = None
    chunks: Dict[int, ChunkProgress] = None
    
    def __post_init__(self):
        if self.chunks is None:
            self.chunks = {}


class ProgressMonitor:
    """Real-time transcription progress monitor"""
    
    def __init__(self, temp_chunks_dir: str = None):
        # Use definition.py for temp chunks directory
        if temp_chunks_dir is None:
            try:
                from definition import TEMP_DIR
                temp_chunks_dir = TEMP_DIR
            except ImportError:
                temp_chunks_dir = "output/temp_chunks"
        self.temp_chunks_dir = Path(temp_chunks_dir)
        self.temp_chunks_dir.mkdir(parents=True, exist_ok=True)
        self.monitoring = False
        self.monitor_thread: Optional[Thread] = None
        self.lock = Lock()
        self.current_progress: Optional[TranscriptionProgress] = None
        
    def start_monitoring(self, audio_file: str, estimated_duration: float = None):
        """Start monitoring transcription progress"""
        if self.monitoring:
            logger.warning("Progress monitoring is already active")
            return
            
        self.monitoring = True
        self.current_progress = TranscriptionProgress(
            total_chunks=0,
            completed_chunks=0,
            failed_chunks=0,
            current_chunk=0,
            overall_progress=0.0,
            elapsed_time=0.0,
            estimated_remaining=0.0,
            success_rate=0.0,
            start_time=datetime.now()
        )
        
        # Start monitoring thread
        self.monitor_thread = Thread(
            target=self._monitor_loop,
            args=(audio_file, estimated_duration),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("🚀 Progress monitoring started")
        
    def stop_monitoring(self):
        """Stop progress monitoring"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logger.info("🛑 Progress monitoring stopped")
        
    def _monitor_loop(self, audio_file: str, estimated_duration: float = None):
        """Main monitoring loop"""
        last_check = time.time()
        
        while self.monitoring:
            try:
                current_time = time.time()
                
                # Update progress from temp chunk files
                self._update_progress_from_chunks()
                
                # Update timing information
                if self.current_progress:
                    self.current_progress.elapsed_time = current_time - self.current_progress.start_time.timestamp()
                    
                    # Calculate estimated remaining time
                    if self.current_progress.completed_chunks > 0:
                        avg_chunk_time = self.current_progress.elapsed_time / self.current_progress.completed_chunks
                        remaining_chunks = self.current_progress.total_chunks - self.current_progress.completed_chunks
                        self.current_progress.estimated_remaining = avg_chunk_time * remaining_chunks
                    
                    # Calculate success rate
                    total_processed = self.current_progress.completed_chunks + self.current_progress.failed_chunks
                    if total_processed > 0:
                        self.current_progress.success_rate = (self.current_progress.completed_chunks / total_processed) * 100
                
                # Display progress update
                self._display_progress()
                
                # Check every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in progress monitoring: {e}")
                time.sleep(5)
                
    def _update_progress_from_chunks(self):
        """Update progress by reading temporary chunk files"""
        if not self.current_progress:
            return
            
        try:
            chunk_files = list(self.temp_chunks_dir.glob("chunk_*.json"))
            
            # Parse chunk files to update progress
            for chunk_file in chunk_files:
                try:
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                    
                    chunk_num = chunk_data.get('chunk_number')
                    if chunk_num is None:
                        continue
                        
                    # Create or update chunk progress
                    if chunk_num not in self.current_progress.chunks:
                        chunk_progress = ChunkProgress(
                            chunk_number=chunk_num,
                            start_time=chunk_data.get('start_time', 0),
                            end_time=chunk_data.get('end_time', 0),
                            status=chunk_data.get('status', 'unknown'),
                            transcription=chunk_data.get('text', ''),
                            word_count=chunk_data.get('word_count', 0),
                            timestamp=chunk_data.get('timestamp')
                        )
                        self.current_progress.chunks[chunk_num] = chunk_progress
                        
                        # Update total chunks count
                        if chunk_num > self.current_progress.total_chunks:
                            self.current_progress.total_chunks = chunk_num
                    else:
                        # Update existing chunk
                        chunk_progress = self.current_progress.chunks[chunk_num]
                        chunk_progress.status = chunk_data.get('status', chunk_progress.status)
                        chunk_progress.transcription = chunk_data.get('text', chunk_progress.transcription)
                        chunk_progress.word_count = chunk_data.get('word_count', chunk_progress.word_count)
                        
                        # Update timestamps
                        if chunk_data.get('timestamp'):
                            chunk_progress.timestamp = chunk_data.get('timestamp')
                            
            # Update progress counts
            completed = sum(1 for c in self.current_progress.chunks.values() if c.status == 'completed')
            failed = sum(1 for c in self.current_progress.chunks.values() if c.status == 'failed')
            
            self.current_progress.completed_chunks = completed
            self.current_progress.failed_chunks = failed
            
            # Calculate overall progress
            if self.current_progress.total_chunks > 0:
                self.current_progress.overall_progress = (completed / self.current_progress.total_chunks) * 100
                
        except Exception as e:
            logger.error(f"Error updating progress from chunks: {e}")
            
    def _display_progress(self):
        """Display current progress information"""
        if not self.current_progress:
            return
            
        progress = self.current_progress
        
        # Clear screen (simple approach)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🎯 TRANSCRIPTION PROGRESS MONITOR")
        print("=" * 80)
        
        # Overall progress
        print(f"📊 Overall Progress: {progress.overall_progress:.1f}%")
        print(f"🎯 Current Chunk: {progress.current_chunk}/{progress.total_chunks}")
        print(f"✅ Completed: {progress.completed_chunks}")
        print(f"❌ Failed: {progress.failed_chunks}")
        print(f"📈 Success Rate: {progress.success_rate:.1f}%")
        
        # Time information
        elapsed_str = str(timedelta(seconds=int(progress.elapsed_time)))
        remaining_str = str(timedelta(seconds=int(progress.estimated_remaining))) if progress.estimated_remaining > 0 else "Calculating..."
        
        print(f"⏱️  Elapsed Time: {elapsed_str}")
        print(f"⏳ Estimated Remaining: {remaining_str}")
        
        # Progress bar
        bar_length = 50
        filled_length = int(bar_length * progress.overall_progress / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\n[{bar}] {progress.overall_progress:.1f}%")
        
        # Recent chunks status
        print(f"\n📋 Recent Chunks Status:")
        recent_chunks = sorted(progress.chunks.keys(), reverse=True)[:10]
        
        for chunk_num in recent_chunks:
            chunk = progress.chunks[chunk_num]
            status_emoji = {
                'completed': '✅',
                'processing': '🔄',
                'failed': '❌',
                'unknown': '❓'
            }.get(chunk.status, '❓')
            
            print(f"   {status_emoji} Chunk {chunk_num:03d}: {chunk.status} "
                  f"({chunk.start_time:.0f}s - {chunk.end_time:.0f}s)")
            
        print("\n" + "=" * 80)
        print("Press Ctrl+C to stop monitoring")
        
    def get_progress_summary(self) -> Optional[Dict]:
        """Get a summary of current progress"""
        if not self.current_progress:
            return None
            
        progress = self.current_progress
        
        return {
            'overall_progress': progress.overall_progress,
            'total_chunks': progress.total_chunks,
            'completed_chunks': progress.completed_chunks,
            'failed_chunks': progress.failed_chunks,
            'success_rate': progress.success_rate,
            'elapsed_time': progress.elapsed_time,
            'estimated_remaining': progress.estimated_remaining,
            'start_time': progress.start_time.isoformat(),
            'current_chunk': progress.current_chunk
        }
        
    def export_progress_report(self, output_file: str = None) -> str:
        """Export detailed progress report to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"transcription_progress_{timestamp}.json"
            
        report = {
            'summary': self.get_progress_summary(),
            'chunks': {
                chunk_num: {
                    'chunk_number': chunk.chunk_number,
                    'start_time': chunk.start_time,
                    'end_time': chunk.end_time,
                    'status': chunk.status,
                    'word_count': chunk.word_count,
                    'transcription_preview': chunk.transcription[:100] + "..." if len(chunk.transcription) > 100 else chunk.transcription
                }
                for chunk_num, chunk in self.current_progress.chunks.items()
            } if self.current_progress else {},
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info(f"📊 Progress report exported to: {output_file}")
        return output_file


class LogBasedProgressMonitor:
    """Alternative progress monitor that reads from log files"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self.last_position = 0
        self.progress_patterns = {
            'transcription_start': r'🚀 STARTING CHUNKED TRANSCRIPTION: (\d+) chunks to process',
            'chunk_start': r'🎯 Processing chunk (\d+): ([\d.]+)s - ([\d.]+)s',
            'chunk_complete': r'✅ CHUNK (\d+) PROGRESS: Transcription completed in ([\d.]+)s',
            'overall_progress': r'📊 OVERALL PROGRESS: ([\d.]+)% \(([\d.]+)s / ([\d.]+)s\)',
            'transcription_complete': r'🏁 CHUNKED TRANSCRIPTION COMPLETE!',
            'error': r'❌.*?failed.*?chunk (\d+)',
            'warning': r'⚠️.*?warning'
        }
        
    def monitor_logs(self, callback=None):
        """Monitor log file for progress updates"""
        if not self.log_file or not os.path.exists(self.log_file):
            logger.error(f"Log file not found: {self.log_file}")
            return
            
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # Seek to last position
                f.seek(self.last_position)
                
                for line in f:
                    self._parse_progress_line(line.strip(), callback)
                    
                # Update position
                self.last_position = f.tell()
                
        except Exception as e:
            logger.error(f"Error monitoring log file: {e}")
            
    def _parse_progress_line(self, line: str, callback=None):
        """Parse a single log line for progress information"""
        if not line:
            return
            
        # Check for progress patterns
        for pattern_name, pattern in self.progress_patterns.items():
            match = re.search(pattern, line)
            if match:
                if callback:
                    callback(pattern_name, match.groups(), line)
                break
