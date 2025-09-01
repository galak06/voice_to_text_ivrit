"""
Chunk Merger Service
Merges individual chunk results into consolidated transcription data
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.utils.config_manager import ConfigManager


class ChunkMerger:
    """
    Merges chunk results into consolidated transcription data.
    
    This service follows the Single Responsibility Principle by handling only
    chunk merging logic, and uses dependency injection for configuration.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the chunk merger.
        
        Args:
            config_manager: Configuration manager for dependency injection
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Load configuration with defaults
        self.chunk_duration = self._get_config_value('chunk_duration', 30)
        self.stride_length = self._get_config_value('stride_length', 5)
        self.overlapping_chunks = self._get_config_value('overlapping_chunks', True)
        
        # Check if speaker recognition is disabled
        self.speaker_recognition_disabled = self._is_speaker_recognition_disabled()
        if self.speaker_recognition_disabled:
            self.logger.info("🎤 Speaker recognition is disabled - will merge chunks without speaker data")
    
    def _get_config_value(self, key: str, default_value: Any) -> Any:
        """Get configuration value with fallback to default."""
        try:
            if hasattr(self.config_manager.config, 'processing'):
                return getattr(self.config_manager.config.processing, key, default_value)
        except AttributeError:
            pass
        return default_value
    
    def _is_speaker_recognition_disabled(self) -> bool:
        """Check if speaker recognition is disabled in configuration."""
        try:
            if hasattr(self.config_manager.config, 'disable_options'):
                disable_options = self.config_manager.config.disable_options
                return (
                    getattr(disable_options, 'disable_speaker_detection', False) or
                    getattr(disable_options, 'disable_speaker_labeling', False) or
                    getattr(disable_options, 'disable_speaker_segmentation', False) or
                    getattr(disable_options, 'use_single_speaker_mode', False)
                )
        except AttributeError:
            pass
        return False
    
    def merge_chunks_from_directory(self, chunk_dir: Path) -> Dict[str, Any]:
        """
        Merge all chunk files from a directory.
        
        Args:
            chunk_dir: Directory containing chunk JSON files
            
        Returns:
            Merged transcription data
        """
        try:
            self.logger.info(f"🔄 Merging chunks from directory: {chunk_dir}")
            
            # Find all chunk files
            chunk_files = list(chunk_dir.glob("chunk_*.json"))
            chunk_files.sort(key=lambda x: self._extract_chunk_number(x.name))
            
            self.logger.info(f"Found {len(chunk_files)} chunk files")
            
            # Load and merge chunks
            chunks = self._load_chunk_files(chunk_files)
            merged_data = self._merge_chunks_with_overlapping(chunks)
            
            self.logger.info(f"✅ Chunk merging completed: {len(chunks)} chunks merged")
            return merged_data
            
        except Exception as e:
            self.logger.error(f"❌ Error merging chunks: {e}")
            raise
    
    def _load_chunk_files(self, chunk_files: List[Path]) -> List[Dict[str, Any]]:
        """Load all chunk files and return their data."""
        chunks = []
        
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                chunks.append(chunk_data)
            except Exception as e:
                self.logger.error(f"Error loading {chunk_file}: {e}")
                # Continue with other chunks
        
        return chunks
    
    def _extract_chunk_number(self, filename: str) -> int:
        """Extract chunk number from filename."""
        try:
            if 'chunk_' in filename:
                parts = filename.split('_')
                if len(parts) >= 2:
                    return int(parts[1])
        except (ValueError, IndexError):
            pass
        return 0
    
    def _merge_chunks_with_overlapping(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge chunks considering overlapping strategy."""
        if not chunks:
            return {}
        
        # Sort chunks by start time
        sorted_chunks = sorted(chunks, key=lambda x: self._get_chunk_start_time(x))
        
        # Initialize merged data
        merged_data = {
            'total_duration': 0,
            'total_chunks': len(chunks),
            'speakers': {},
            'full_text': '',
            'segments': [],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'chunk_count': len(chunks),
                'overlapping_strategy': f"{self.chunk_duration}s chunks with {self.stride_length}s overlap",
                'merging_config': {
                    'chunk_duration': self.chunk_duration,
                    'stride_length': self.stride_length,
                    'overlapping_chunks': self.overlapping_chunks
                }
            }
        }
        
        # Process each chunk
        for i, chunk in enumerate(sorted_chunks):
            chunk_start = self._get_chunk_start_time(chunk)
            chunk_end = self._get_chunk_end_time(chunk)
            
            # Add chunk duration (accounting for overlap)
            if i == 0:
                merged_data['total_duration'] += chunk_end - chunk_start
            else:
                # For overlapping chunks, only add the non-overlapping portion
                overlap = chunk_end - chunk_start - self.stride_length
                merged_data['total_duration'] += overlap
            
            # Process speaker recognition (only if enabled)
            if not self.speaker_recognition_disabled:
                speaker_recognition = chunk.get('speaker_recognition', {})
                if speaker_recognition:
                    self._merge_speaker_data(merged_data, speaker_recognition, chunk_start, chunk)
            else:
                # When speaker recognition is disabled, collect text segments directly
                self._collect_text_segments(merged_data, chunk, chunk_start)
            
            # Add to full text
            chunk_text = chunk.get('text', '')
            if chunk_text:
                if merged_data['full_text']:
                    merged_data['full_text'] += ' ' + chunk_text
                else:
                    merged_data['full_text'] = chunk_text
        
        return merged_data
    
    def _get_chunk_start_time(self, chunk: Dict[str, Any]) -> float:
        """Get the start time of a chunk."""
        # Try different possible locations for start time
        if 'transcription_data' in chunk and 'segments' in chunk['transcription_data']:
            segments = chunk['transcription_data']['segments']
            if segments and 'start' in segments[0]:
                return segments[0]['start']
        
        # Fallback to chunk metadata
        if 'chunk_metadata' in chunk and 'start' in chunk['chunk_metadata']:
            return chunk['chunk_metadata']['start']
        
        # Fallback to audio chunk metadata
        if 'audio_chunk_metadata' in chunk and 'start' in chunk['audio_chunk_metadata']:
            return chunk['audio_chunk_metadata']['start']
        
        return 0.0
    
    def _get_chunk_end_time(self, chunk: Dict[str, Any]) -> float:
        """Get the end time of a chunk."""
        # Try different possible locations for end time
        if 'transcription_data' in chunk and 'segments' in chunk['transcription_data']:
            segments = chunk['transcription_data']['segments']
            if segments and 'end' in segments[0]:
                return segments[0]['end']
        
        # Fallback to chunk metadata
        if 'chunk_metadata' in chunk and 'end' in chunk['chunk_metadata']:
            return chunk['chunk_metadata']['end']
        
        # Fallback to audio chunk metadata
        if 'audio_chunk_metadata' in chunk and 'end' in chunk['audio_chunk_metadata']:
            return chunk['audio_chunk_metadata']['end']
        
        return 0.0
    
    def _merge_speaker_data(self, merged_data: Dict[str, Any], speaker_recognition: Dict[str, Any], 
                           chunk_start: float, chunk: Dict[str, Any]):
        """Merge speaker data from a chunk."""
        speaker_names = speaker_recognition.get('speaker_names', [])
        speaker_details = speaker_recognition.get('speaker_details', {})
        
        for speaker_name in speaker_names:
            if speaker_name not in merged_data['speakers']:
                merged_data['speakers'][speaker_name] = []
            
            # Get speaker segments
            if speaker_name in speaker_details:
                speaker_data = speaker_details[speaker_name]
                segments = speaker_data.get('segments', [])
                
                for segment in segments:
                    # Convert relative timing to absolute timing
                    absolute_start = chunk_start + segment.get('start', 0)
                    absolute_end = chunk_start + segment.get('end', 0)
                    
                    merged_segment = {
                        'start': absolute_start,
                        'end': absolute_end,
                        'text': segment.get('text', ''),
                        'duration': segment.get('duration', 0),
                        'chunk_source': chunk.get('file_name', 'unknown')
                    }
                    
                    merged_data['speakers'][speaker_name].append(merged_segment)
        
        # Sort segments by start time for each speaker
        for speaker_name in merged_data['speakers']:
            merged_data['speakers'][speaker_name].sort(key=lambda x: x['start'])
    
    def validate_merged_data(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the merged data for consistency and completeness.
        
        Args:
            merged_data: Merged transcription data to validate
            
        Returns:
            Validation results
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'statistics': {}
        }
        
        try:
            # Check basic structure
            if not merged_data.get('speakers'):
                validation_result['errors'].append("No speaker data found")
                validation_result['is_valid'] = False
            
            if not merged_data.get('total_duration', 0) > 0:
                validation_result['warnings'].append("Total duration is zero or missing")
            
            # Check speaker consistency (only if speaker recognition is enabled)
            if not self.speaker_recognition_disabled:
                speaker_names = list(merged_data.get('speakers', {}).keys())
                if len(speaker_names) != 2:
                    validation_result['warnings'].append(f"Expected 2 speakers, found {len(speaker_names)}")
                
                # Generate statistics for speakers
                total_segments = sum(len(segments) for segments in merged_data.get('speakers', {}).values())
            else:
                # When speaker recognition is disabled, use segments directly
                speaker_names = ['SINGLE_SPEAKER']
                total_segments = len(merged_data.get('segments', []))
            validation_result['statistics'] = {
                'total_speakers': len(speaker_names),
                'total_segments': total_segments,
                'total_duration': merged_data.get('total_duration', 0),
                'total_chunks': merged_data.get('total_chunks', 0)
            }
            
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {e}")
            validation_result['is_valid'] = False
        
        return validation_result
    
    def _collect_text_segments(self, merged_data: Dict[str, Any], chunk: Dict[str, Any], chunk_start: float):
        """Collect text segments when speaker recognition is disabled."""
        # Initialize segments list if it doesn't exist
        if 'segments' not in merged_data:
            merged_data['segments'] = []
        
        # Try to get segments from different possible locations
        if 'transcription_data' in chunk and 'segments' in chunk['transcription_data']:
            segments = chunk['transcription_data']['segments']
            for segment in segments:
                merged_segment = {
                    'start': chunk_start + segment.get('start', 0),
                    'end': chunk_start + segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'duration': segment.get('duration', 0),
                    'chunk_source': chunk.get('file_name', 'unknown')
                }
                merged_data['segments'].append(merged_segment)
        elif 'segments' in chunk:
            segments = chunk['segments']
            for segment in segments:
                merged_segment = {
                    'start': chunk_start + segment.get('start', 0),
                    'end': chunk_start + segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'duration': segment.get('duration', 0),
                    'chunk_source': chunk.get('file_name', 'unknown')
                }
                merged_data['segments'].append(merged_segment)
        
        # Sort segments by start time
        merged_data['segments'].sort(key=lambda x: x['start'])
