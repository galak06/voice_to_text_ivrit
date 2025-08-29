#!/usr/bin/env python3
"""
Chunking strategies for audio files
Follows SOLID principles with dependency injection
"""

import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""
    
    @abstractmethod
    def create_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create audio chunks according to the strategy"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        pass


class OverlappingChunkingStrategy(ChunkingStrategy):
    """Strategy for creating overlapping audio chunks"""
    
    def __init__(self, config_manager):
        """Initialize with ConfigManager dependency injection"""
        self.config_manager = config_manager
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate overlapping chunking configuration"""
        try:
            chunk_length = self._get_config_value('chunk_length', 30)
            stride_length = self._get_config_value('stride_length', 5)
            min_chunk_duration = self._get_config_value('min_chunk_duration', 5)
            
            if chunk_length <= 0:
                raise ValueError("chunk_length must be positive")
            if stride_length <= 0:
                raise ValueError("stride_length must be positive")
            if min_chunk_duration <= 0:
                raise ValueError("min_chunk_duration must be positive")
            if stride_length >= chunk_length:
                raise ValueError("stride_length must be less than chunk_length")
            
            logger.info("✅ Overlapping chunking configuration validation passed")
            
        except Exception as e:
            logger.error(f"❌ Overlapping chunking configuration validation failed: {e}")
            raise RuntimeError(f"Overlapping chunking configuration validation failed: {e}")
    
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
    
    def create_chunks(self, audio_file_path: str, duration: float) -> List[Dict[str, Any]]:
        """Create overlapping audio chunks"""
        try:
            # Get overlapping chunking configuration
            chunk_length = self._get_config_value('chunk_length', 30)
            stride_length = self._get_config_value('stride_length', 5)
            min_chunk_duration = self._get_config_value('min_chunk_duration', 5)
            
            logger.info("🎯 OVERLAPPING CHUNKS CONFIGURATION")
            logger.info(f"   📏 Chunk length: {chunk_length}s")
            logger.info(f"   🔄 Stride length (overlap): {stride_length}s")
            logger.info(f"   📏 Min chunk duration: {min_chunk_duration}s")
            logger.info(f"   🎵 Audio duration: {duration:.1f}s")
            
            # Calculate chunks with overlap
            chunks = []
            chunk_num = 0
            current_start = 0.0
            
            while current_start < duration:
                current_end = min(current_start + chunk_length, duration)
                chunk_duration = current_end - current_start
                
                # Skip chunks that are too short (except for the last one)
                if chunk_duration < min_chunk_duration and current_end < duration:
                    current_start += stride_length
                    continue
                
                # Create chunk metadata
                chunk_info = self._create_chunk_info(
                    chunk_num, current_start, current_end, stride_length
                )
                chunks.append(chunk_info)
                
                # Move to next chunk with overlap
                current_start += (chunk_length - stride_length)
                chunk_num += 1
                
                # Prevent infinite loop
                if current_start >= duration:
                    break
            
            # Log chunking summary
            self._log_chunking_summary(chunks, duration, stride_length)
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error creating overlapping chunks: {e}")
            raise RuntimeError(f"Overlapping chunking failed: {e}")
    
    def _create_chunk_info(self, chunk_num: int, start_time: float, end_time: float, 
                           stride_length: float) -> Dict[str, Any]:
        """Create chunk metadata for overlapping chunks"""
        chunk_filename = f"chunk_{chunk_num + 1:03d}_{int(start_time)}s_{int(end_time)}s"
        
        return {
            'start': start_time,
            'end': end_time,
            'duration': end_time - start_time,
            'chunk_number': chunk_num + 1,
            'filename': chunk_filename,
            'chunking_strategy': 'overlapping',
            'overlap_start': max(0, start_time - stride_length),
            'overlap_end': end_time + stride_length,
            'stride_length': stride_length
        }
    
    def _log_chunking_summary(self, chunks: List[Dict[str, Any]], duration: float, stride_length: float):
        """Log summary of chunking results"""
        total_chunks = len(chunks)
        if total_chunks == 0:
            logger.warning("⚠️ No chunks created")
            return
            
        avg_duration = sum(c['duration'] for c in chunks) / total_chunks
        max_duration = max(c['duration'] for c in chunks)
        min_duration = min(c['duration'] for c in chunks)
        
        logger.info("=" * 60)
        logger.info("✅ OVERLAPPING CHUNKS COMPLETED")
        logger.info("=" * 60)
        logger.info(f"📊 Total chunks created: {total_chunks}")
        logger.info(f"📏 Average chunk duration: {avg_duration:.1f}s")
        logger.info(f"📏 Maximum chunk duration: {max_duration:.1f}s")
        logger.info(f"📏 Minimum chunk duration: {min_duration:.1f}s")
        logger.info(f"🔄 Overlap between chunks: {stride_length}s")
        logger.info(f"⏱️  Total audio coverage: {sum(c['duration'] for c in chunks):.1f}s")
        logger.info(f"📈 Coverage efficiency: {(duration / sum(c['duration'] for c in chunks)) * 100:.1f}%")
        logger.info("=" * 60)
    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return "OverlappingChunkingStrategy"


class ChunkingStrategyFactory:
    """Factory for creating chunking strategies"""
    
    @staticmethod
    def create_strategy(config_manager) -> ChunkingStrategy:
        """Create the overlapping chunking strategy (always)"""
        try:
            logger.info("🎯 Creating overlapping chunking strategy")
            return OverlappingChunkingStrategy(config_manager)
                
        except Exception as e:
            logger.error(f"❌ Error creating chunking strategy: {e}")
            raise RuntimeError(f"Failed to create overlapping chunking strategy: {e}")
