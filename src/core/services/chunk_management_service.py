#!/usr/bin/env python3
"""
Chunk management service for handling chunk creation and audio operations
Follows SOLID principles with dependency injection
"""

import logging
import os
import time
import json
import numpy as np
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ChunkManager(ABC):
    """Abstract base class for chunk managers"""
    
    @abstractmethod
    def create_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create audio chunks according to the strategy"""
        pass
    
    @abstractmethod
    def save_audio_chunks(self, chunks: List[Dict[str, Any]], audio_data, sample_rate: int) -> None:
        """Save audio chunks as WAV files"""
        pass
    
    @abstractmethod
    def create_chunk_directories(self) -> None:
        """Create necessary directories for chunking"""
        pass


class OverlappingChunkManager(ChunkManager):
    """Manager for overlapping chunking strategy"""
    
    def __init__(self, config_manager, chunking_strategy):
        """Initialize with ConfigManager and chunking strategy dependency injection"""
        self.config_manager = config_manager
        self.chunking_strategy = chunking_strategy
        self.output_directories = self._get_output_directories()
    
    def _get_output_directories(self) -> Dict[str, str]:
        """Get output directories from ConfigManager"""
        try:
            dir_paths = self.config_manager.get_directory_paths()
            return {
                'chunk_results': dir_paths.get('chunk_results_dir'),
                'audio_chunks': dir_paths.get('audio_chunks_dir')
            }
        except Exception as e:
            logger.error(f"❌ Error getting output directories: {e}")
            raise RuntimeError(f"Failed to get output directories: {e}")
    
    def create_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create overlapping audio chunks using the injected strategy"""
        try:
            # Use the injected chunking strategy to create chunks
            chunks = self.chunking_strategy.create_chunks(audio_file_path, duration)
            
            # Create all necessary chunk directories
            self.create_chunk_directories()
            
            # Create initial JSON progress files for all chunks
            self._create_initial_chunk_jsons(chunks)
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error creating overlapping chunks: {e}")
            raise RuntimeError(f"Overlapping chunking failed: {e}. The system requires overlapping chunking to work properly.")
    
    def save_audio_chunks(self, chunks: List[Dict[str, Any]], audio_data, sample_rate: int) -> None:
        """Save audio chunks as WAV files"""
        try:
            # Check if we should save audio chunks based on configuration
            save_audio_chunks = self._get_config_value('save_audio_chunks', True)
            logger.info(f"🎵 Audio chunk saving: {'enabled' if save_audio_chunks else 'disabled'}")
            
            if not save_audio_chunks:
                logger.info("📁 Audio chunk saving disabled, only metadata created")
                return
            
            # Save audio chunks and create metadata
            logger.info("💾 Creating audio chunks and metadata...")
            for i, chunk_info in enumerate(chunks):
                start_sample = int(chunk_info['start'] * sample_rate)
                end_sample = int(chunk_info['end'] * sample_rate)
                
                # Handle both mono and stereo audio data
                if len(audio_data.shape) > 1:
                    # Stereo audio: audio_data shape is (samples, channels)
                    audio_chunk = audio_data[start_sample:end_sample, :]
                    logger.debug(f"   🎧 Extracting stereo chunk: {start_sample}:{end_sample}, shape: {audio_chunk.shape}")
                    # Ensure we have valid audio data
                    if audio_chunk.size == 0:
                        logger.warning(f"⚠️ Empty stereo chunk extracted: {start_sample}:{end_sample}")
                        audio_chunk = np.zeros((end_sample - start_sample, audio_data.shape[1]), dtype=audio_data.dtype)
                else:
                    # Mono audio: audio_data shape is (samples,)
                    audio_chunk = audio_data[start_sample:end_sample]
                    logger.debug(f"   🎧 Extracting mono chunk: {start_sample}:{end_sample}, shape: {audio_chunk.shape}")
                    # Ensure we have valid audio data
                    if audio_chunk.size == 0:
                        logger.warning(f"⚠️ Empty mono chunk extracted: {start_sample}:{end_sample}")
                        audio_chunk = np.zeros(end_sample - start_sample, dtype=audio_data.dtype)
                
                # Pass the 0-based chunk index, not the 1-based chunk_number
                chunk_index = chunk_info['chunk_number'] - 1
                self._save_audio_chunk(audio_chunk, sample_rate, chunk_index, chunk_info['start'], chunk_info['end'])
                
                logger.info(f"💾 Created audio chunk {i+1}/{len(chunks)}: {chunk_info['filename']}.wav")
                logger.info(f"   📍 Time: {chunk_info['start']:.1f}s - {chunk_info['end']:.1f}s (duration: {chunk_info['duration']:.1f}s)")
                logger.info(f"   🎵 Samples: {len(audio_chunk):,} at {sample_rate}Hz")
            
        except Exception as e:
            logger.error(f"❌ Error saving audio chunks: {e}")
            raise RuntimeError(f"Failed to save audio chunks: {e}")
    
    def create_chunk_directories(self) -> None:
        """Create necessary directories for chunking"""
        try:
            # Create directories from configuration
            for dir_type, dir_path in self.output_directories.items():
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"📁 Created directory: {dir_type} -> {dir_path}")
            
            logger.info(f"📁 Created {len(self.output_directories)} chunk directories")
        except Exception as e:
            logger.warning(f"⚠️ Error creating chunk directories: {e}")
    
    def _create_initial_chunk_jsons(self, chunks: List[Dict[str, Any]]) -> None:
        """Create initial JSON progress files for all chunks"""
        try:
            for chunk_info in chunks:
                self._create_initial_chunk_json(chunk_info)
            
            logger.info(f"📝 Created {len(chunks)} initial JSON progress files")
            
        except Exception as e:
            logger.error(f"❌ Error creating initial chunk JSONs: {e}")
    
    def _create_initial_chunk_json(self, chunk_info: Dict[str, Any]) -> None:
        """Create initial JSON progress file for a chunk"""
        try:
            json_filename = f"{chunk_info['filename']}.json"
            json_path = os.path.join(self.output_directories['chunk_results'], json_filename)
            
            # Create initial JSON progress data
            json_data = {
                'chunk_number': chunk_info['chunk_number'],
                'start_time': chunk_info['start'],
                'end_time': chunk_info['end'],
                'status': 'created',
                'created_at': time.time(),
                'text': '',
                'processing_started': None,
                'processing_completed': None,
                'audio_chunk_metadata': chunk_info,
                'error_message': None,
                'enhancement_applied': False,
                'enhancement_strategy': self._get_config_value('default_enhancement_strategy', 'basic'),
                'transcription_length': 0,
                'words_estimated': 0,
                'chunk_metadata': chunk_info,
                'chunking_strategy': chunk_info.get('chunking_strategy', 'overlapping'),
                'overlap_start': chunk_info.get('overlap_start', 0),
                'overlap_end': chunk_info.get('overlap_end', 0),
                'stride_length': chunk_info.get('stride_length', 5),
                'progress': {
                    'stage': 'created',
                    'message': 'Overlapping chunk created, waiting for processing',
                    'timestamp': time.time()
                }
            }
            
            # Save initial JSON progress
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📝 Created initial JSON progress: {json_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error creating initial chunk JSON: {e}")
    
    def _save_audio_chunk(self, audio_chunk, sample_rate: int, chunk_num: int, chunk_start: float, chunk_end: float):
        """Save audio chunk as WAV file"""
        try:
            import soundfile as sf
            
            filename = f"audio_chunk_{chunk_num + 1:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav"
            filepath = f"{self.output_directories['audio_chunks']}/{filename}"
            
            # Save as WAV file
            sf.write(filepath, audio_chunk, sample_rate)
            logger.debug(f"💾 Saved audio chunk: {filename}")
            
        except ImportError:
            logger.warning("⚠️ soundfile not available, skipping audio chunk save")
        except Exception as e:
            logger.warning(f"⚠️ Error saving audio chunk {chunk_num + 1}: {e}")
    
    def _get_config_value(self, key: str, default_value):
        """Get configuration value from ConfigManager"""
        try:
            if hasattr(self.config_manager.config, 'chunking') and hasattr(self.config_manager.config.chunking, key):
                return getattr(self.config_manager.config.chunking, key)
            
            if hasattr(self.config_manager.config, 'processing') and hasattr(self.config_manager.config.processing, key):
                return getattr(self.config_manager.config.processing, key)
            
            if hasattr(self.config_manager.config, key):
                return getattr(self.config_manager.config, key)
            
            return default_value
            
        except Exception as e:
            logger.debug(f"Error getting config value for {key}: {e}")
            return default_value


class FixedDurationChunkManager(ChunkManager):
    """Manager for fixed duration chunking strategy"""
    
    def __init__(self, config_manager, chunking_strategy):
        """Initialize with ConfigManager and chunking strategy dependency injection"""
        self.config_manager = config_manager
        self.chunking_strategy = chunking_strategy
        self.output_directories = self._get_output_directories()
    
    def _get_output_directories(self) -> Dict[str, str]:
        """Get output directories from ConfigManager"""
        try:
            dir_paths = self.config_manager.get_directory_paths()
            return {
                'chunk_results': dir_paths.get('chunk_results_dir'),
                'audio_chunks': dir_paths.get('audio_chunks_dir')
            }
        except Exception as e:
            logger.error(f"❌ Error getting output directories: {e}")
            raise RuntimeError(f"Failed to get output directories: {e}")
    
    def create_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create fixed duration audio chunks using the injected strategy"""
        try:
            # Use the injected chunking strategy to create chunks
            chunks = self.chunking_strategy.create_chunks(audio_file_path, duration)
            
            # Create all necessary chunk directories
            self.create_chunk_directories()
            
            # Create initial JSON progress files for all chunks
            self._create_initial_chunk_jsons(chunks)
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error creating fixed duration chunks: {e}")
            return []
    
    def save_audio_chunks(self, chunks: List[Dict[str, Any]], audio_data, sample_rate: int) -> None:
        """Save audio chunks as WAV files"""
        try:
            # Check if we should save audio chunks based on configuration
            save_audio_chunks = self._get_config_value('save_audio_chunks', True)
            logger.info(f"🎵 Audio chunk saving: {'enabled' if save_audio_chunks else 'disabled'}")
            
            if not save_audio_chunks:
                logger.info("📁 Audio chunk saving disabled, only metadata created")
                return
            
            # Save audio chunks
            for i, chunk_info in enumerate(chunks):
                start_sample = int(chunk_info['start'] * sample_rate)
                end_sample = int(chunk_info['end'] * sample_rate)
                
                # Handle both mono and stereo audio data
                if len(audio_data.shape) > 1:
                    # Stereo audio: audio_data shape is (samples, channels)
                    audio_chunk = audio_data[start_sample:end_sample, :]
                    logger.debug(f"   🎧 Extracting stereo chunk: {start_sample}:{end_sample}, shape: {audio_chunk.shape}")
                    # Ensure we have valid audio data
                    if audio_chunk.size == 0:
                        logger.warning(f"⚠️ Empty stereo chunk extracted: {start_sample}:{end_sample}")
                        audio_chunk = np.zeros((end_sample - start_sample, audio_data.shape[1]), dtype=audio_data.dtype)
                else:
                    # Mono audio: audio_data shape is (samples,)
                    audio_chunk = audio_data[start_sample:end_sample]
                    logger.debug(f"   🎧 Extracting mono chunk: {start_sample}:{end_sample}, shape: {audio_chunk.shape}")
                    # Ensure we have valid audio data
                    if audio_chunk.size == 0:
                        logger.warning(f"⚠️ Empty mono chunk extracted: {start_sample}:{end_sample}")
                        audio_chunk = np.zeros(end_sample - start_sample, dtype=audio_data.dtype)
                
                chunk_index = chunk_info['chunk_number'] - 1
                self._save_audio_chunk(audio_chunk, sample_rate, chunk_index, chunk_info['start'], chunk_info['end'])
                
                logger.info(f"💾 Created audio chunk: {chunk_info['filename']}.wav ({chunk_info['start']:.1f}s - {chunk_info['end']:.1f}s)")
            
        except Exception as e:
            logger.error(f"❌ Error saving audio chunks: {e}")
            raise RuntimeError(f"Failed to save audio chunks: {e}")
    
    def create_chunk_directories(self) -> None:
        """Create necessary directories for chunking"""
        try:
            # Create directories from configuration
            for dir_type, dir_path in self.output_directories.items():
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"📁 Created directory: {dir_type} -> {dir_path}")
            
            logger.info(f"📁 Created {len(self.output_directories)} chunk directories")
        except Exception as e:
            logger.warning(f"⚠️ Error creating chunk directories: {e}")
    
    def _create_initial_chunk_jsons(self, chunks: List[Dict[str, Any]]) -> None:
        """Create initial JSON progress files for all chunks"""
        try:
            for chunk_info in chunks:
                self._create_initial_chunk_json(chunk_info)
            
            logger.info(f"📝 Created {len(chunks)} initial JSON progress files")
            
        except Exception as e:
            logger.error(f"❌ Error creating initial chunk JSONs: {e}")
    
    def _create_initial_chunk_json(self, chunk_info: Dict[str, Any]) -> None:
        """Create initial JSON progress file for a chunk"""
        try:
            json_filename = f"{chunk_info['filename']}.json"
            json_path = os.path.join(self.output_directories['chunk_results'], json_filename)
            
            # Create initial JSON progress data
            json_data = {
                'chunk_number': chunk_info['chunk_number'],
                'start_time': chunk_info['start'],
                'end_time': chunk_info['end'],
                'status': 'created',
                'created_at': time.time(),
                'text': '',
                'processing_started': None,
                'processing_completed': None,
                'audio_chunk_metadata': chunk_info,
                'error_message': None,
                'enhancement_applied': False,
                'enhancement_strategy': self._get_config_value('default_enhancement_strategy', 'basic'),
                'transcription_length': 0,
                'words_estimated': 0,
                'chunk_metadata': chunk_info,
                'chunking_strategy': chunk_info.get('chunking_strategy', 'fixed_duration'),
                'progress': {
                    'stage': 'created',
                    'message': 'Fixed duration chunk created, waiting for processing',
                    'timestamp': time.time()
                }
            }
            
            # Save initial JSON progress
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📝 Created initial JSON progress: {json_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error creating initial chunk JSON: {e}")
    
    def _save_audio_chunk(self, audio_chunk, sample_rate: int, chunk_num: int, chunk_start: float, chunk_end: float):
        """Save audio chunk as WAV file"""
        try:
            import soundfile as sf
            
            filename = f"audio_chunk_{chunk_num + 1:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav"
            filepath = f"{self.output_directories['audio_chunks']}/{filename}"
            
            # Save as WAV file
            sf.write(filepath, audio_chunk, sample_rate)
            logger.debug(f"💾 Saved audio chunk: {filename}")
            
        except ImportError:
            logger.warning("⚠️ soundfile not available, skipping audio chunk save")
        except Exception as e:
            logger.warning(f"⚠️ Error saving audio chunk {chunk_num + 1}: {e}")
    
    def _get_config_value(self, key: str, default_value):
        """Get configuration value from ConfigManager"""
        try:
            if hasattr(self.config_manager.config, 'chunking') and hasattr(self.config_manager.config.chunking, key):
                return getattr(self.config_manager.config.chunking, key)
            
            if hasattr(self.config_manager.config, 'processing') and hasattr(self.config_manager.config.processing, key):
                return getattr(self.config_manager.config.processing, key)
            
            if hasattr(self.config_manager.config, key):
                return getattr(self.config_manager.config, key)
            
            return default_value
            
        except Exception as e:
            logger.debug(f"Error getting config value for {key}: {e}")
            return default_value


class ChunkManagementService:
    """Service for managing chunk creation and management operations"""
    
    def __init__(self, config_manager):
        """Initialize with ConfigManager dependency injection"""
        self.config_manager = config_manager
        self.chunking_strategy = None
        self.chunk_manager = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize chunking strategy and manager based on configuration"""
        try:
            from src.core.engines.strategies.chunking_strategy import ChunkingStrategyFactory, OverlappingChunkingStrategy
            
            # Create the appropriate chunking strategy
            self.chunking_strategy = ChunkingStrategyFactory.create_strategy(self.config_manager)
            
            # Create the appropriate chunk manager
            if isinstance(self.chunking_strategy, OverlappingChunkingStrategy):
                self.chunk_manager = OverlappingChunkManager(self.config_manager, self.chunking_strategy)
            else:
                self.chunk_manager = FixedDurationChunkManager(self.config_manager, self.chunking_strategy)
            
            logger.info(f"✅ Initialized chunk management service with {self.chunking_strategy.get_strategy_name()}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing chunk management service: {e}")
            raise RuntimeError(f"Failed to initialize chunk management service: {e}")
    
    def create_and_save_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create chunks and save audio files"""
        try:
            # Ensure chunk manager is initialized
            if not self.chunk_manager:
                raise RuntimeError("Chunk manager not initialized")
            
            # Create chunks using the strategy
            chunks = self.chunk_manager.create_chunks(audio_file_path, duration)
            
            if not chunks:
                logger.warning("⚠️ No chunks created")
                return []
            
            # Load audio data for saving chunks
            audio_data, sample_rate = self._load_audio_data(audio_file_path)
            
            # Ensure sample_rate is an integer for soundfile compatibility
            sample_rate = int(sample_rate)
            
            # Save audio chunks
            self.chunk_manager.save_audio_chunks(chunks, audio_data, sample_rate)
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error creating and saving chunks: {e}")
            raise RuntimeError(f"Failed to create and save chunks: {e}")
    
    def _load_audio_data(self, audio_file_path: str):
        """Load audio data for chunking"""
        try:
            # Try soundfile first (more reliable for WAV files)
            try:
                import soundfile as sf
                audio_data, sample_rate = sf.read(audio_file_path)
                logger.info(f"✅ Audio loaded with soundfile: {len(audio_data):,} samples at {sample_rate}Hz")
                if len(audio_data.shape) > 1:
                    logger.info(f"   🎧 Audio channels: {audio_data.shape[1]} (stereo preserved)")
                else:
                    logger.info(f"   🎧 Audio channels: 1 (mono)")
                return audio_data, sample_rate
            except ImportError:
                logger.debug("⚠️ Soundfile not available, trying librosa")
                pass
            
            # Fallback to librosa
            import librosa
            # Preserve stereo to avoid audio corruption during chunking
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None, mono=False)
            logger.info(f"✅ Audio loaded with librosa: {len(audio_data):,} samples at {sample_rate}Hz")
            if len(audio_data.shape) > 1:
                logger.info(f"   🎧 Audio channels: {audio_data.shape[1]} (stereo preserved)")
            else:
                logger.info(f"   🎧 Audio channels: 1 (mono)")
            return audio_data, sample_rate
            
        except ImportError:
            logger.error("❌ Neither soundfile nor librosa available")
            raise ImportError("Soundfile or librosa is required for audio processing")
        except Exception as e:
            logger.error(f"❌ Error loading audio data: {e}")
            raise
