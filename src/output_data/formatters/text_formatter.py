#!/usr/bin/env python3
"""
Text Formatter
Handles text formatting and Hebrew punctuation improvements
"""

import re
from typing import Dict, Any, List


class TextFormatter:
    """Text formatting utilities"""
    
    @staticmethod
    def improve_hebrew_punctuation(text: str) -> str:
        """Improve punctuation for Hebrew text"""
        if not text:
            return text
        
        # First, normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Hebrew punctuation improvements
        improvements = [
            # Fix spacing around Hebrew punctuation marks
            (r'([א-ת])\s*([,\.!?;:])', r'\1\2'),  # Remove space before punctuation
            (r'([,\.!?;:])\s*([א-ת])', r'\1 \2'),  # Add space after punctuation before Hebrew
            (r'([א-ת])\s*\.\s*([א-ת])', r'\1. \2'),  # Period between Hebrew words
            (r'([א-ת])\s*,\s*([א-ת])', r'\1, \2'),  # Comma between Hebrew words
            (r'([א-ת])\s*!\s*([א-ת])', r'\1! \2'),  # Exclamation between Hebrew words
            (r'([א-ת])\s*\?\s*([א-ת])', r'\1? \2'),  # Question mark between Hebrew words
            
            # Fix spacing around quotes
            (r'"([א-ת]+)"', r'"\1"'),
            (r"'([א-ת]+)'", r"'\1'"),
            
            # Fix spacing around numbers
            (r'([א-ת])\s*(\d+)', r'\1 \2'),
            (r'(\d+)\s*([א-ת])', r'\1 \2'),
            
            # Fix spacing around English letters
            (r'([א-ת])\s*([a-zA-Z])', r'\1 \2'),
            (r'([a-zA-Z])\s*([א-ת])', r'\1 \2'),
            
            # Fix common Hebrew text issues
            (r'([א-ת])\s*-\s*([א-ת])', r'\1-\2'),  # Hyphens in Hebrew words
            (r'([א-ת])\s*/\s*([א-ת])', r'\1/\2'),  # Slashes in Hebrew words
            
            # Clean up multiple spaces (but preserve line breaks)
            (r'[ \t]+', ' '),
        ]
        
        for pattern, replacement in improvements:
            text = re.sub(pattern, replacement, text)
        
        return text.strip()
    
    @staticmethod
    def format_speakers_text(speakers: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format speakers data as readable text"""
        text_parts = []
        
        for speaker_name, segments in speakers.items():
            for segment in segments:
                if isinstance(segment, dict) and 'text' in segment:
                    text_parts.append(f"{speaker_name}: {segment['text']}")
        
        return '\n'.join(text_parts)
    
    @staticmethod
    def format_conversation_text(speakers: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format speakers data as conversation text with timestamps"""
        conversation_parts = []
        
        # Collect all segments with timing information
        all_segments = []
        for speaker_name, segments in speakers.items():
            for segment in segments:
                if isinstance(segment, dict) and 'text' in segment:
                    all_segments.append({
                        'speaker': speaker_name,
                        'start': segment.get('start', 0),
                        'end': segment.get('end', 0),
                        'text': segment['text']
                    })
        
        # Sort by start time to maintain chronological order
        all_segments.sort(key=lambda x: x['start'])
        
        # Format each segment
        for segment in all_segments:
            start_time = segment['start']
            end_time = segment['end']
            speaker = segment['speaker']
            text = segment['text']
            
            # Improve punctuation for the text
            text = TextFormatter.improve_hebrew_punctuation(text)
            
            # Format timestamp
            start_str = TextFormatter._format_timestamp(start_time)
            end_str = TextFormatter._format_timestamp(end_time)
            
            # Create formatted line
            formatted_line = f"[{start_str}-{end_str}] {speaker}: {text}"
            conversation_parts.append(formatted_line)
        
        return '\n'.join(conversation_parts)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}" 