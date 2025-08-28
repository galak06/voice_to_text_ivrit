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
    
    def __init__(self, config_manager):
        """Initialize cleanup manager with ConfigManager - no fallback to direct config"""
        if not config_manager:
            raise ValueError("ConfigManager is required - no fallback to direct config")
        
        self.config_manager = config_manager
        
        # Get configuration values from ConfigManager
        config = config_manager.config
        self.cleanup_logs_before_run = getattr(config, 'cleanup_logs_before_run', True)
        self.max_output_files = getattr(config, 'max_output_files', 5)
        
        # Get directory paths from ConfigManager
        dir_paths = config_manager.get_directory_paths()
        # JSON files go to chunk_results, not temp_chunks
        self.temp_chunks_dir = dir_paths.get('chunk_results_dir', 'output/chunk_results')
        self.chunk_results_dir = dir_paths.get('chunk_results_dir', 'output/chunk_results')
        self.audio_chunks_dir = dir_paths.get('audio_chunks_dir', 'output/audio_chunks')
    
    def execute_cleanup(self, clear_console: bool = True, clear_files: bool = True, clear_output: bool = True) -> None:
        """Execute cleanup operations based on parameters"""
        logger.info(f"🧹 execute_cleanup called with: console={clear_console}, files={clear_files}, output={clear_output}")
        
        if clear_console:
            self._clear_console_output()
        
        if clear_files:
            # Always clean up chunks regardless of config flag
            logger.info("🧹 Forcing chunk cleanup...")
            self._cleanup_previous_chunks()
            # Also do log cleanup if configured
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
                # Use definition.py for log file paths
        try:
            from definition import LOGS_DIR
            log_files = [
                os.path.join(LOGS_DIR, "transcription.log"),
                os.path.join(LOGS_DIR, "error.log"),
                os.path.join(LOGS_DIR, "debug.log"),
                os.path.join(LOGS_DIR, "progress.log")
            ]
        except ImportError:
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
            logger.info("🧹 Starting chunk cleanup process...")
            
            # Clean up temp_chunks directory
            if os.path.exists(self.temp_chunks_dir):
                logger.info(f"🧹 Found temp_chunks directory: {self.temp_chunks_dir}")
                import shutil
                shutil.rmtree(self.temp_chunks_dir)
                logger.info(f"🧹 Cleaned previous temp_chunks directory: {self.temp_chunks_dir}")
            else:
                logger.info(f"🧹 No temp_chunks directory found: {self.temp_chunks_dir}")
            
            # Use instance variable for chunk_results directory
            chunk_results_dir = self.chunk_results_dir
            logger.info(f"🧹 Using chunk_results_dir: {chunk_results_dir}")
            
            if os.path.exists(chunk_results_dir):
                logger.info(f"🧹 Found chunk_results directory: {chunk_results_dir}")
                # List files before deletion for debugging
                files = os.listdir(chunk_results_dir)
                logger.info(f"🧹 Found {len(files)} files to delete: {files[:5]}...")
                
                import shutil
                shutil.rmtree(chunk_results_dir)
                logger.info(f"🧹 Deleted chunk_results directory: {chunk_results_dir}")
                
                # Recreate empty directory
                os.makedirs(chunk_results_dir, exist_ok=True)
                logger.info(f"🧹 Recreated empty chunk_results directory: {chunk_results_dir}")
                
                # Verify deletion
                if os.path.exists(chunk_results_dir):
                    remaining_files = os.listdir(chunk_results_dir)
                    logger.info(f"🧹 Verification: directory exists with {len(remaining_files)} files")
                else:
                    logger.error(f"🧹 ERROR: Directory was not recreated: {chunk_results_dir}")
            else:
                logger.info(f"🧹 No chunk_results directory found: {chunk_results_dir}")
                
        except Exception as e:
            logger.error(f"❌ Could not clean previous chunks: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
    
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
            # Use definition.py for output directory
            try:
                from definition import OUTPUT_DIR
                output_dir = OUTPUT_DIR
            except ImportError:
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
            # Use instance variable for audio chunks directory
            audio_chunks_dir = self.audio_chunks_dir
            
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
