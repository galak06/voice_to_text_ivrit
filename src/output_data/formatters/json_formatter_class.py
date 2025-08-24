#!/usr/bin/env python3
"""
Enhanced JSON Formatter Class
Handles JSON formatting with improved speaker organization and conversation structure
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .json_encoder import CustomJSONEncoder

logger = logging.getLogger(__name__)


class DataEnhancer:
    """Enhances data structure with conversation organization following Single Responsibility Principle"""
    
    @staticmethod
    def enhance_conversation_structure(data: Any) -> Dict[str, Any]:
        """Enhance data structure with conversation organization"""
        if not isinstance(data, dict):
            return data
        
        enhanced_data = data.copy()
        
        # Add conversation metadata
        enhanced_data['conversation_metadata'] = DataEnhancer._create_metadata(data)
        
        # Reorganize speakers into conversation format
        if 'speakers' in data:
            enhanced_data['conversation'] = DataEnhancer._create_conversation_sections(data['speakers'])
            enhanced_data['speaker_statistics'] = DataEnhancer._calculate_speaker_statistics(data['speakers'])
            enhanced_data['timeline'] = DataEnhancer._create_timeline_view(data['speakers'])
        
        return enhanced_data
    
    @staticmethod
    def _create_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create conversation metadata following Single Responsibility Principle"""
        return {
            'format_version': '2.0',
            'generated_at': datetime.now().isoformat(),
            'total_speakers': len(data.get('speakers', {})),
            'total_segments': sum(len(segs) for segs in data.get('speakers', {}).values()),
            'has_overlapping_chunks': DataEnhancer._detect_overlapping_chunks(data)
        }
    
    @staticmethod
    def _create_conversation_sections(speakers: Dict[str, List]) -> Dict[str, Any]:
        """Create conversation sections for each speaker following Single Responsibility Principle"""
        conversation = {}
        
        for speaker_id, segments in speakers.items():
            # Sort segments by start time
            sorted_segments = sorted(segments, key=lambda x: getattr(x, 'start', 0))
            
            # Create speaker section
            speaker_section = {
                'speaker_id': speaker_id,
                'display_name': DataEnhancer._format_speaker_name(speaker_id),
                'total_segments': len(sorted_segments),
                'total_duration': DataEnhancer._calculate_speaker_duration(sorted_segments),
                'total_words': DataEnhancer._calculate_speaker_words(sorted_segments),
                'segments': []
            }
            
            # Add individual segments with enhanced metadata
            for i, segment in enumerate(sorted_segments):
                segment_data = DataEnhancer._create_segment_data(segment, speaker_id, i)
                speaker_section['segments'].append(segment_data)
            
            conversation[speaker_id] = speaker_section
        
        return conversation
    
    @staticmethod
    def _format_speaker_name(speaker_id: str) -> str:
        """Format speaker name following Single Responsibility Principle"""
        if '_' in speaker_id:
            return f"Speaker {speaker_id.split('_')[-1]}"
        return speaker_id
    
    @staticmethod
    def _create_segment_data(segment, speaker_id: str, index: int) -> Dict[str, Any]:
        """Create segment data following Single Responsibility Principle"""
        return {
            'segment_id': f"{speaker_id}_seg_{index + 1:03d}",
            'start_time': getattr(segment, 'start', 0),
            'end_time': getattr(segment, 'end', 0),
            'duration': getattr(segment, 'end', 0) - getattr(segment, 'start', 0),
            'text': getattr(segment, 'text', ''),
            'word_count': len(getattr(segment, 'text', '').split()),
            'confidence': getattr(segment, 'confidence', None),
            'chunk_info': {
                'chunk_file': getattr(segment, 'chunk_file', None),
                'chunk_number': getattr(segment, 'chunk_number', None)
            },
            'start_time_formatted': DataEnhancer._format_timestamp(getattr(segment, 'start', 0)),
            'end_time_formatted': DataEnhancer._format_timestamp(getattr(segment, 'end', 0))
        }
    
    @staticmethod
    def _create_timeline_view(speakers: Dict[str, List]) -> List[Dict[str, Any]]:
        """Create chronological timeline view of all segments following Single Responsibility Principle"""
        timeline = []
        
        # Collect all segments with speaker info
        all_segments = []
        for speaker_id, segments in speakers.items():
            for segment in segments:
                all_segments.append({
                    'speaker_id': speaker_id,
                    'start_time': getattr(segment, 'start', 0),
                    'end_time': getattr(segment, 'end', 0),
                    'text': getattr(segment, 'text', ''),
                    'segment': segment
                })
        
        # Sort by start time
        all_segments.sort(key=lambda x: x['start_time'])
        
        # Create timeline entries
        for i, entry in enumerate(all_segments):
            timeline_entry = {
                'timeline_id': f"timeline_{i + 1:04d}",
                'timestamp': entry['start_time'],
                'timestamp_formatted': DataEnhancer._format_timestamp(entry['start_time']),
                'speaker_id': entry['speaker_id'],
                'speaker_name': DataEnhancer._format_speaker_name(entry['speaker_id']),
                'text': entry['text'],
                'duration': entry['end_time'] - entry['start_time'],
                'word_count': len(entry['text'].split())
            }
            timeline.append(timeline_entry)
        
        return timeline
    
    @staticmethod
    def _calculate_speaker_statistics(speakers: Dict[str, List]) -> Dict[str, Any]:
        """Calculate statistics for each speaker following Single Responsibility Principle"""
        stats = {}
        
        for speaker_id, segments in speakers.items():
            total_duration = DataEnhancer._calculate_speaker_duration(segments)
            total_words = DataEnhancer._calculate_speaker_words(segments)
            
            stats[speaker_id] = {
                'total_segments': len(segments),
                'total_duration': total_duration,
                'total_words': total_words,
                'average_segment_duration': total_duration / len(segments) if segments else 0,
                'average_words_per_segment': total_words / len(segments) if segments else 0,
                'speaking_percentage': 0  # Will be calculated below
            }
        
        # Calculate speaking percentages
        total_duration_all = sum(stat['total_duration'] for stat in stats.values())
        if total_duration_all > 0:
            for speaker_stats in stats.values():
                speaker_stats['speaking_percentage'] = (speaker_stats['total_duration'] / total_duration_all) * 100
        
        return stats
    
    @staticmethod
    def _calculate_speaker_duration(segments: List) -> float:
        """Calculate total duration for a speaker's segments following Single Responsibility Principle"""
        return sum(getattr(seg, 'end', 0) - getattr(seg, 'start', 0) for seg in segments)
    
    @staticmethod
    def _calculate_speaker_words(segments: List) -> int:
        """Calculate total word count for a speaker's segments following Single Responsibility Principle"""
        return sum(len(getattr(seg, 'text', '').split()) for seg in segments)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds into MM:SS format following Single Responsibility Principle"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def _detect_overlapping_chunks(data: Dict[str, Any]) -> bool:
        """Detect if there are overlapping chunks in the data following Single Responsibility Principle"""
        if 'speakers' not in data:
            return False
        
        # Check for overlapping time ranges
        all_segments = []
        for speaker_id, segments in data['speakers'].items():
            for segment in segments:
                all_segments.append({
                    'start': getattr(segment, 'start', 0),
                    'end': getattr(segment, 'end', 0),
                    'speaker': speaker_id
                })
        
        # Sort by start time
        all_segments.sort(key=lambda x: x['start'])
        
        # Check for overlaps
        for i in range(len(all_segments) - 1):
            if all_segments[i]['end'] > all_segments[i + 1]['start']:
                return True
        
        return False


class JsonFormatter:
    """Enhanced JSON formatting utilities with conversation structure following Single Responsibility Principle"""
    
    @staticmethod
    def format_transcription_data(data: Any) -> str:
        """Format transcription data as JSON string with conversation structure"""
        enhanced_data = DataEnhancer.enhance_conversation_structure(data)
        return json.dumps(enhanced_data, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)
    
    @staticmethod
    def save_json_file(data: Any, file_path: str) -> bool:
        """Save data as JSON file with conversation structure"""
        try:
            enhanced_data = DataEnhancer.enhance_conversation_structure(data)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving enhanced JSON file: {e}")
            return False 