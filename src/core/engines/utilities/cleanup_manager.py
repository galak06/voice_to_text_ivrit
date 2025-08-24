#!/usr/bin/env python3
"""
Cleanup Manager Utility
Handles cleanup operations for transcription engines
"""

import logging
import os
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CleanupManager:
    """Manages cleanup operations for transcription engines"""
    
    def __init__(self, config):
        """Initialize cleanup manager with configuration"""
        self.config = config
        self.cleanup_logs_before_run = getattr(config, 'cleanup_logs_before_run', True)
        self.max_output_files = getattr(config, 'max_output_files', 5)
        self.temp_chunks_dir = "output/temp_chunks"
    
    def execute_cleanup(self, clear_console: bool = True, clear_files: bool = True, clear_output: bool = True) -> None:
        """Execute cleanup operations based on parameters"""
        if clear_console:
            self._clear_console_output()
        
        if clear_files:
            self._cleanup_logs()
        
        if clear_output:
            self._cleanup_output_files()
    
    def _clear_console_output(self) -> None:
        """Clear console output by printing separator"""
        print("\n" + "="*80)
        print("🧹 MANUAL LOG CLEANUP")
        print("="*80 + "\n")
    
    def _cleanup_logs(self) -> None:
        """Clean up log files before starting new transcription"""
        if not self.cleanup_logs_before_run:
            return
            
        try:
            self._print_session_separator()
            self._clear_log_files()
            self._cleanup_previous_chunks()
        except Exception as e:
            logger.warning(f"⚠️ Log cleanup error: {e}")
    
    def _print_session_separator(self) -> None:
        """Print session separator to console"""
        print("\n" + "="*80)
        print("🧹 NEW TRANSCRIPTION SESSION STARTING")
        print("="*80 + "\n")
    
    def _clear_log_files(self) -> None:
        """Clear log files"""
        log_files = [
            "output/transcription.log",
            "output/error.log", 
            "output/debug.log",
            "output/progress.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                self._truncate_log_file(log_file)
    
    def _cleanup_previous_chunks(self) -> None:
        """Clean up previous transcription chunks at the start of new run"""
        try:
            if os.path.exists(self.temp_chunks_dir):
                import shutil
                shutil.rmtree(self.temp_chunks_dir)
                logger.info(f"🧹 Cleaned previous temp_chunks directory: {self.temp_chunks_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Could not clean previous chunks: {e}")
    
    def _truncate_log_file(self, log_file: str) -> None:
        """Truncate a single log file"""
        with open(log_file, 'w') as f:
            f.write(f"# Log cleared at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# New transcription session: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
        logger.debug(f"🧹 Cleared log file: {log_file}")
    
    def _cleanup_output_files(self) -> None:
        """Clean up old output files"""
        try:
            output_dir = "output"
            if not os.path.exists(output_dir):
                return
                
            transcription_files = self._get_transcription_files(output_dir)
            removed_count = self._remove_old_files(transcription_files)
            
            if removed_count > 0:
                logger.info(f"🧹 Cleaned up {removed_count} old output files")
                
        except Exception as e:
            logger.warning(f"⚠️ Output cleanup error: {e}")
    
    def _get_transcription_files(self, output_dir: str) -> list:
        """Get list of transcription files with timestamps"""
        transcription_files = []
        for file in os.listdir(output_dir):
            if file.endswith(('.txt', '.json', '.docx')) and 'transcription' in file.lower():
                file_path = os.path.join(output_dir, file)
                transcription_files.append((file_path, os.path.getmtime(file_path)))
        return transcription_files
    
    def _remove_old_files(self, transcription_files: list) -> int:
        """Remove old transcription files"""
        transcription_files.sort(key=lambda x: x[1], reverse=True)
        removed_count = 0
        
        for file_path, _ in transcription_files[self.max_output_files:]:
            try:
                os.remove(file_path)
                removed_count += 1
            except Exception as e:
                logger.debug(f"⚠️ Could not remove old file {file_path}: {e}")
        
        return removed_count
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files created during processing"""
        try:
            if os.path.exists(self.temp_chunks_dir):
                # Only clean up non-JSON temporary files, preserve JSON chunks
                import glob
                temp_files = glob.glob(os.path.join(self.temp_chunks_dir, "*.tmp"))
                temp_files.extend(glob.glob(os.path.join(self.temp_chunks_dir, "*.log")))
                
                for temp_file in temp_files:
                    try:
                        os.remove(temp_file)
                        logger.debug(f"🧹 Cleaned temp file: {temp_file}")
                    except Exception as e:
                        logger.debug(f"⚠️ Could not remove temp file {temp_file}: {e}")
                
                logger.debug(f"🧹 Cleaned temporary files in: {self.temp_chunks_dir}")
                # Note: JSON chunk files are preserved for user reference
        except Exception as e:
            logger.warning(f"⚠️ Cleanup error: {e}")
    
    def auto_cleanup_after_transcription(self) -> None:
        """Automatically clean up temp files after transcription completion"""
        try:
            # Clean audio chunk files if they exist (keep JSON chunks)
            audio_chunks_dir = "output/audio_chunks"
            if os.path.exists(audio_chunks_dir):
                import shutil
                shutil.rmtree(audio_chunks_dir)
                logger.debug(f"🧹 Cleaned audio chunks directory: {audio_chunks_dir}")
                
            # Note: JSON chunks in temp_chunks are preserved for user reference
            logger.info("🧹 Auto-cleanup completed after transcription (JSON chunks preserved)")
        except Exception as e:
            logger.warning(f"⚠️ Auto-cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about cleanup configuration and status"""
        stats = {
            "cleanup_enabled": self.cleanup_logs_before_run,
            "max_output_files": self.max_output_files,
            "temp_dir": self.temp_chunks_dir,
            "temp_dir_exists": os.path.exists(self.temp_chunks_dir)
        }
        
        output_stats = self._get_output_file_stats()
        stats.update(output_stats)
        
        return stats
    
    def _get_output_file_stats(self) -> dict:
        """Get output file statistics"""
        output_dir = "output"
        if not os.path.exists(output_dir):
            return {}
        
        transcription_files = self._get_transcription_files(output_dir)
        
        return {
            "current_output_files": len(transcription_files),
            "output_files_to_clean": max(0, len(transcription_files) - self.max_output_files)
        }
