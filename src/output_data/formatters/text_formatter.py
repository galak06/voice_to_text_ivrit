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
        
        improvements = [
            (r'([א-ת])\s*([,\.!?;:])', r'\1\2'),
            (r'([,\.!?;:])\s*([א-ת])', r'\1 \2'),
            (r'([א-ת])\s*([a-zA-Z])', r'\1 \2'),
            (r'([a-zA-Z])\s*([א-ת])', r'\1 \2'),
            (r'([א-ת])\s*\.\s*([א-ת])', r'\1. \2'),
            (r'([א-ת])\s*,\s*([א-ת])', r'\1, \2'),
            (r'"([א-ת]+)"', r'"\1"'),
            (r"'([א-ת]+)'", r"'\1'"),
            (r'\s+', ' '),
            (r'([א-ת])\s*(\d+)', r'\1 \2'),
            (r'(\d+)\s*([א-ת])', r'\1 \2'),
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
        
        for speaker_name, segments in speakers.items():
            for segment in segments:
                if isinstance(segment, dict) and 'text' in segment:
                    start_time = segment.get('start', 0)
                    end_time = segment.get('end', 0)
                    text = segment['text']
                    
                    # Format timestamp
                    start_str = TextFormatter._format_timestamp(start_time)
                    end_str = TextFormatter._format_timestamp(end_time)
                    
                    conversation_parts.append(f"[{start_str}-{end_str}] {speaker_name}: {text}")
        
        return '\n'.join(conversation_parts)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}" 