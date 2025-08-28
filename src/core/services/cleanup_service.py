#!/usr/bin/env python3
"""
Cleanup Service for transcription system
Follows SOLID principles with dependency injection
"""

import logging
import os
import shutil
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CleanupService:
    """Service responsible for cleaning up transcription artifacts and temporary files"""
    
    def __init__(self, config_manager):
        """Initialize with ConfigManager dependency injection"""
        self.config_manager = config_manager
        self.output_directories = self._get_output_directories()
    
    def _get_output_directories(self) -> Dict[str, str]:
        """Get output directories from ConfigManager"""
        try:
            # Use ConfigManager's get_directory_paths method
            dir_paths = self.config_manager.get_directory_paths()
            
            # Extract directory paths with proper fallbacks
            chunk_results_dir = dir_paths.get('chunk_results_dir', 'output/chunk_results')
            audio_chunks_dir = dir_paths.get('audio_chunks_dir', 'output/audio_chunks')
            chunk_temp_dir = dir_paths.get('chunk_temp_dir', 'output/temp_chunks')
            
            # Get log directory from config with fallback
            log_directory = self._get_config_value('log_directory', 'output/logs')
            if not log_directory:
                log_directory = 'output/logs'
            
            return {
                'chunk_results': chunk_results_dir,
                'audio_chunks': audio_chunks_dir,
                'temp_chunks': chunk_temp_dir,
                'logs': log_directory
            }
        except Exception as e:
            logger.error(f"❌ Error getting output directories: {e}")
            raise RuntimeError(f"Failed to get output directories: {e}")
    
    def _get_config_value(self, key: str, default_value=None):
        """Get configuration value from ConfigManager using proper injection"""
        try:
            # Check if config is a dictionary
            if isinstance(self.config_manager.config, dict):
                # Check in output section first
                if 'output' in self.config_manager.config and key in self.config_manager.config['output']:
                    return self.config_manager.config['output'][key]
                
                # Check in logging section
                if 'logging' in self.config_manager.config and key in self.config_manager.config['logging']:
                    return self.config_manager.config['logging'][key]
                
                # Check in root config
                if key in self.config_manager.config:
                    return self.config_manager.config[key]
            
            # Check if config is an object with attributes
            elif hasattr(self.config_manager.config, '__getattr__') or hasattr(self.config_manager.config, '__getattribute__'):
                # Check in output section first
                if hasattr(self.config_manager.config, 'output') and hasattr(self.config_manager.config.output, key):
                    return getattr(self.config_manager.config.output, key)
                
                # Check in logging section
                if hasattr(self.config_manager.config, 'logging') and hasattr(self.config_manager.config.logging, key):
                    return getattr(self.config_manager.config.logging, key)
                
                # Check in root config
                if hasattr(self.config_manager.config, key):
                    return getattr(self.config_manager.config, key)
            
            # Return default
            return default_value
            
        except Exception as e:
            logger.debug(f"Error getting config value for {key}: {e}")
            return default_value
    
    def cleanup_before_transcription(self, clear_console: bool = False, clear_files: bool = True, clear_output: bool = False) -> Dict[str, Any]:
        """
        Clean up before starting new transcription
        
        Args:
            clear_console: Whether to clear console output
            clear_files: Whether to clear chunk files and temporary data
            clear_output: Whether to clear final transcription output
            
        Returns:
            Dictionary with cleanup results
        """
        cleanup_results = {
            'chunks_cleared': 0,
            'temp_files_cleared': 0,
            'json_files_cleared': 0,
            'errors': []
        }
        
        try:
            logger.info("🧹 Starting pre-transcription cleanup...")
            
            if clear_files:
                cleanup_results.update(self._cleanup_chunk_files())
                cleanup_results.update(self._cleanup_temp_files())
                cleanup_results.update(self._cleanup_json_progress_files())
            
            if clear_output:
                cleanup_results.update(self._cleanup_output_files())
            
            if clear_console:
                self._clear_console()
            
            logger.info("✅ Pre-transcription cleanup completed successfully")
            logger.info(f"📊 Cleanup summary: {cleanup_results}")
            
        except Exception as e:
            error_msg = f"Cleanup failed: {e}"
            logger.error(f"❌ {error_msg}")
            cleanup_results['errors'].append(error_msg)
        
        return cleanup_results
    
    def cleanup_after_transcription(self, retain_chunks: bool = True, retain_temp: bool = False) -> Dict[str, Any]:
        """
        Clean up after transcription completion
        
        Args:
            retain_chunks: Whether to keep audio chunk files
            retain_temp: Whether to keep temporary files
            
        Returns:
            Dictionary with cleanup results
        """
        cleanup_results = {
            'chunks_cleared': 0,
            'temp_files_cleared': 0,
            'json_files_cleared': 0,
            'errors': []
        }
        
        try:
            logger.info("🧹 Starting post-transcription cleanup...")
            
            if not retain_temp:
                cleanup_results.update(self._cleanup_temp_files())
            
            if not retain_chunks:
                cleanup_results.update(self._cleanup_chunk_files())
                cleanup_results.update(self._cleanup_json_progress_files())
            
            logger.info("✅ Post-transcription cleanup completed successfully")
            logger.info(f"📊 Cleanup summary: {cleanup_results}")
            
        except Exception as e:
            error_msg = f"Post-cleanup failed: {e}"
            logger.error(f"❌ {error_msg}")
            cleanup_results['errors'].append(error_msg)
        
        return cleanup_results
    
    def _cleanup_chunk_files(self) -> Dict[str, Any]:
        """Clean up audio chunk files"""
        results = {'chunks_cleared': 0, 'errors': []}
        
        try:
            audio_chunks_dir = self.output_directories.get('audio_chunks')
            if not audio_chunks_dir or not os.path.exists(audio_chunks_dir):
                logger.debug("📁 Audio chunks directory does not exist, skipping cleanup")
                return results
            
            # Count existing chunks
            existing_chunks = [f for f in os.listdir(audio_chunks_dir) if f.endswith('.wav')]
            logger.info(f"🔍 Found {len(existing_chunks)} existing audio chunks to clean up")
            
            # Remove chunk files
            for chunk_file in existing_chunks:
                try:
                    file_path = os.path.join(audio_chunks_dir, chunk_file)
                    os.remove(file_path)
                    results['chunks_cleared'] += 1
                    logger.debug(f"🗑️ Removed audio chunk: {chunk_file}")
                except Exception as e:
                    error_msg = f"Failed to remove {chunk_file}: {e}"
                    logger.warning(f"⚠️ {error_msg}")
                    results['errors'].append(error_msg)
            
            logger.info(f"✅ Audio chunks cleanup completed: {results['chunks_cleared']} files removed")
            
        except Exception as e:
            error_msg = f"Audio chunks cleanup failed: {e}"
            logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    def _cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files"""
        results = {'temp_files_cleared': 0, 'errors': []}
        
        try:
            temp_chunks_dir = self.output_directories.get('temp_chunks')
            if not temp_chunks_dir or not os.path.exists(temp_chunks_dir):
                logger.debug("📁 Temp chunks directory does not exist, skipping cleanup")
                return results
            
            # Count existing temp files
            existing_temp_files = []
            for root, dirs, files in os.walk(temp_chunks_dir):
                for file in files:
                    existing_temp_files.append(os.path.join(root, file))
            
            logger.info(f"🔍 Found {len(existing_temp_files)} existing temp files to clean up")
            
            # Remove temp directory and contents
            try:
                shutil.rmtree(temp_chunks_dir)
                results['temp_files_cleared'] = len(existing_temp_files)
                logger.info(f"🗑️ Removed temp directory: {temp_chunks_dir}")
            except Exception as e:
                error_msg = f"Failed to remove temp directory: {e}"
                logger.warning(f"⚠️ {error_msg}")
                results['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"Temp files cleanup failed: {e}"
            logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    def _cleanup_json_progress_files(self) -> Dict[str, Any]:
        """Clean up JSON progress files"""
        results = {'json_files_cleared': 0, 'errors': []}
        
        try:
            chunk_results_dir = self.output_directories.get('chunk_results')
            if not chunk_results_dir or not os.path.exists(chunk_results_dir):
                logger.debug("📁 Chunk results directory does not exist, skipping cleanup")
                return results
            
            # Count existing JSON files
            existing_json_files = [f for f in os.listdir(chunk_results_dir) if f.endswith('.json')]
            logger.info(f"🔍 Found {len(existing_json_files)} existing JSON progress files to clean up")
            
            # Remove JSON files
            for json_file in existing_json_files:
                try:
                    file_path = os.path.join(chunk_results_dir, json_file)
                    os.remove(file_path)
                    results['json_files_cleared'] += 1
                    logger.debug(f"🗑️ Removed JSON progress file: {json_file}")
                except Exception as e:
                    error_msg = f"Failed to remove {json_file}: {e}"
                    logger.warning(f"⚠️ {error_msg}")
                    results['errors'].append(error_msg)
            
            logger.info(f"✅ JSON progress files cleanup completed: {results['json_files_cleared']} files removed")
            
        except Exception as e:
            error_msg = f"JSON progress files cleanup failed: {e}"
            logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    def _cleanup_output_files(self) -> Dict[str, Any]:
        """Clean up final transcription output files"""
        results = {'output_files_cleared': 0, 'errors': []}
        
        try:
            # Get output directory from ConfigManager
            output_dir = self._get_config_value('output_dir', 'output/transcriptions')
            
            # Ensure output_dir is a valid string path
            if not output_dir or not isinstance(output_dir, str):
                logger.debug("📁 Invalid output directory path, skipping cleanup")
                return results
            
            if not os.path.exists(output_dir):
                logger.debug("📁 Output directory does not exist, skipping cleanup")
                return results
            
            # Find transcription output files
            output_files = []
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith(('.json', '.docx', '.txt')):
                        output_files.append(os.path.join(root, file))
            
            logger.info(f"🔍 Found {len(output_files)} existing output files to clean up")
            
            # Remove output files
            for output_file in output_files:
                try:
                    os.remove(output_file)
                    results['output_files_cleared'] += 1
                    logger.debug(f"🗑️ Removed output file: {output_file}")
                except Exception as e:
                    error_msg = f"Failed to remove {output_file}: {e}"
                    logger.warning(f"⚠️ {error_msg}")
                    results['errors'].append(error_msg)
            
            logger.info(f"✅ Output files cleanup completed: {results['output_files_cleared']} files removed")
            
        except Exception as e:
            error_msg = f"Output files cleanup failed: {e}"
            logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    def _clear_console(self) -> None:
        """Clear console output"""
        try:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            logger.info("🖥️ Console cleared")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clear console: {e}")
    
    def get_cleanup_status(self) -> Dict[str, Any]:
        """Get current cleanup status and file counts"""
        status = {
            'audio_chunks_count': 0,
            'json_progress_count': 0,
            'temp_files_count': 0,
            'output_files_count': 0
        }
        
        try:
            # Count audio chunks
            audio_chunks_dir = self.output_directories.get('audio_chunks')
            if audio_chunks_dir and os.path.exists(audio_chunks_dir):
                status['audio_chunks_count'] = len([f for f in os.listdir(audio_chunks_dir) if f.endswith('.wav')])
            
            # Count JSON progress files
            chunk_results_dir = self.output_directories.get('chunk_results')
            if chunk_results_dir and os.path.exists(chunk_results_dir):
                status['json_progress_count'] = len([f for f in os.listdir(chunk_results_dir) if f.endswith('.json')])
            
            # Count temp files
            temp_chunks_dir = self.output_directories.get('temp_chunks')
            if temp_chunks_dir and os.path.exists(temp_chunks_dir):
                temp_count = 0
                for root, dirs, files in os.walk(temp_chunks_dir):
                    temp_count += len(files)
                status['temp_files_count'] = temp_count
            
            # Count output files
            output_dir = self._get_config_value('output_dir', 'output/transcriptions')
            if output_dir and isinstance(output_dir, str) and os.path.exists(output_dir):
                output_count = 0
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(('.json', '.docx', '.txt')):
                            output_count += 1
                status['output_files_count'] = output_count
                
        except Exception as e:
            logger.error(f"❌ Error getting cleanup status: {e}")
        
        return status
    
    def get_cleanup_config(self) -> Dict[str, Any]:
        """Get cleanup configuration from ConfigManager"""
        config = {
            'retain_chunks_after_processing': True,
            'retain_temp_files': False,
            'cleanup_frequency': 5,
            'chunk_retention_hours': 24
        }
        
        try:
            # Get chunking config from main chunking section
            if hasattr(self.config_manager.config, 'chunking'):
                chunk_config = self.config_manager.config.chunking
                if hasattr(chunk_config, 'save_audio_chunks'):
                    config['retain_chunks_after_processing'] = chunk_config.save_audio_chunks
                if hasattr(chunk_config, 'save_chunk_metadata'):
                    config['retain_chunks_after_processing'] = chunk_config.save_chunk_metadata
            
            # Get performance config
            if hasattr(self.config_manager.config, 'performance') and hasattr(self.config_manager.config.performance, 'memory_management'):
                perf_config = self.config_manager.config.performance.memory_management
                if hasattr(perf_config, 'cleanup_frequency'):
                    config['cleanup_frequency'] = perf_config.cleanup_frequency
            
            logger.debug(f"🔧 Cleanup configuration loaded: {config}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load cleanup configuration, using defaults: {e}")
        
        return config
