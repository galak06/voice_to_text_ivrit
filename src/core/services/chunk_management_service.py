#!/usr/bin/env python3
"""
Chunk management service for audio processing
Follows SOLID principles with dependency injection
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ChunkManager(ABC):
    """Abstract base class for chunk managers"""
    
    def __init__(self, config_manager, chunking_strategy):
        """Initialize with ConfigManager and ChunkingStrategy dependencies"""
        self.config_manager = config_manager
        self.chunking_strategy = chunking_strategy
        self.output_directories = self._setup_output_directories()
    
    def _setup_output_directories(self) -> Dict[str, str]:
        """Setup output directories from configuration"""
        try:
            output_dir = self._get_config_value('output_dir', 'output/transcriptions')
            chunk_results_dir = self._get_config_value('chunk_results_dir', 'output/chunk_results')
            audio_chunks_dir = self._get_config_value('audio_chunks_dir', 'output/audio_chunks')
            
            # Create directories if they don't exist
            for directory in [output_dir, chunk_results_dir, audio_chunks_dir]:
                Path(directory).mkdir(parents=True, exist_ok=True)
            
            return {
                'output': output_dir,
                'chunk_results': chunk_results_dir,
                'audio_chunks': audio_chunks_dir
            }
            
        except Exception as e:
            logger.error(f"❌ Error setting up output directories: {e}")
            raise RuntimeError(f"Failed to setup output directories: {e}")
    
    def _get_config_value(self, key: str, default_value):
        """Get configuration value from ConfigManager"""
        try:
            if hasattr(self.config_manager.config, 'output') and hasattr(self.config_manager.config.output, key):
                return getattr(self.config_manager.config.output, key)
            
            if hasattr(self.config_manager.config, key):
                return getattr(self.config_manager.config, key)
            
            return default_value
            
        except Exception as e:
            logger.debug(f"Error getting config value for {key}: {e}")
            return default_value
    
    @abstractmethod
    def create_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create audio chunks according to the strategy"""
        pass
    
    @abstractmethod
    def save_audio_chunks(self, chunks: List[Dict[str, Any]], audio_data, sample_rate: int) -> None:
        """Save audio chunks to files"""
        pass


class OverlappingChunkManager(ChunkManager):
    """Manager for overlapping audio chunks"""
    
    def create_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create overlapping chunks using the strategy"""
        try:
            logger.info("🎯 Creating overlapping chunks using strategy")
            chunks = self.chunking_strategy.create_chunks(audio_file_path, duration)
            
            if not chunks:
                logger.warning("⚠️ No chunks created by strategy")
                return []
            
            # Create initial JSON progress files for each chunk
            for chunk_info in chunks:
                self._create_initial_chunk_json(chunk_info)
            
            logger.info(f"✅ Created {len(chunks)} overlapping chunks with JSON progress files")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error creating overlapping chunks: {e}")
            raise RuntimeError(f"Failed to create overlapping chunks: {e}")
    
    def save_audio_chunks(self, chunks: List[Dict[str, Any]], audio_data, sample_rate: int) -> None:
        """Save overlapping audio chunks to WAV files"""
        try:
            logger.info("🎯 Saving overlapping audio chunks")
            
            for chunk_info in chunks:
                start_time = chunk_info['start']
                end_time = chunk_info['end']
                chunk_num = chunk_info['chunk_number'] - 1  # Convert to 0-based index
                
                # Extract audio segment
                start_sample = int(start_time * sample_rate)
                end_sample = int(end_time * sample_rate)
                
                if len(audio_data.shape) > 1:  # Stereo
                    chunk_audio = audio_data[start_sample:end_sample, :]
                else:  # Mono
                    chunk_audio = audio_data[start_sample:end_sample]
                
                # Save audio chunk
                self._save_audio_chunk(chunk_audio, sample_rate, chunk_num, start_time, end_time)
            
            logger.info(f"✅ Saved {len(chunks)} overlapping audio chunks")
            
        except Exception as e:
            logger.error(f"❌ Error saving overlapping audio chunks: {e}")
            raise RuntimeError(f"Failed to save overlapping audio chunks: {e}")
    
    def _create_initial_chunk_json(self, chunk_info: Dict[str, Any]) -> None:
        """Create initial JSON progress file for a chunk"""
        try:
            chunk_num = chunk_info['chunk_number']
            start_time = chunk_info['start']
            end_time = chunk_info['end']
            
            # Create filename
            json_filename = f"chunk_{chunk_num:03d}_{int(start_time)}s_{int(end_time)}s.json"
            json_path = f"{self.output_directories['chunk_results']}/{json_filename}"
            
            # Create initial JSON data
            json_data = {
                'chunk_number': chunk_num,
                'start_time': start_time,
                'end_time': end_time,
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
                'progress': {
                    'stage': 'created',
                    'message': f'{chunk_info.get("chunking_strategy", "overlapping").replace("_", " ").title()} chunk created, waiting for processing',
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
            
            # Create the overlapping chunking strategy (always)
            self.chunking_strategy = ChunkingStrategyFactory.create_strategy(self.config_manager)
            
            # Create the overlapping chunk manager (always)
            self.chunk_manager = OverlappingChunkManager(self.config_manager, self.chunking_strategy)
            
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
