#!/usr/bin/env python3
"""
Text Processor Utility
Handles language-specific text processing and quality validation
"""

import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text processing and quality validation for transcriptions"""
    
    def __init__(self, app_config=None):
        """Initialize text processor with configuration"""
        self.app_config = app_config
    
    def get_language_suppression_tokens(self, language: str) -> List[int]:
        """Get tokens to suppress for language-specific transcription"""
        if (self.app_config and 
            hasattr(self.app_config, 'transcription') and 
            hasattr(self.app_config.transcription, 'suppress_tokens')):
            config_tokens = self.app_config.transcription.suppress_tokens
            if config_tokens and isinstance(config_tokens, list):
                return config_tokens
        
        base_tokens = [-1]
        if language == "he":
            english_tokens = [262, 290, 264, 286, 257, 279, 281, 294, 302, 291, 278, 259, 267, 269]
            language_tokens = [50259, 50260, 50261, 50262, 50263, 50264, 50265, 50266, 50267, 50268]
            return base_tokens + english_tokens + language_tokens
        
        return base_tokens
    
    def filter_language_only(self, text: str, language: str) -> str:
        """Filter text to keep only specified language characters"""
        if language == "he":
            hebrew_pattern = r'[^\u0590-\u05FF\u2000-\u206F\u0020-\u007F\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0E00-\u0E7F\u1B00-\u1B7F\u1CD0-\u1CFF\uA880-\uA8DF\uA900-\uA92F\uAA00-\uAA5F\u0C80-\u0CFF\u0D00-\u0D7F\u0D80-\u0DFF\u0E80-\u0EFF\u0F00-\u0FFF\u1000-\u109F\u1100-\u11FF\u1200-\u137F\u1380-\u139F\u13A0-\u13FF\u1400-\u167F\u1680-\u169F\u16A0-\u16FF\u1700-\u171F\u1720-\u173F\u1740-\u175F\u1760-\u177F\u1780-\u17FF\u1800-\u18AF\u1900-\u194F\u1950-\u197F\u1980-\u19DF\u19E0-\u19FF\u1A00-\u1A1F\u1A20-\u1AAF\u1AB0-\u1AFF\u1B00-\u1B7F\u1B80-\u1BBF\u1BC0-\u1BFF\u1C00-\u1C4F\u1C50-\u1C7F\u1C80-\u1CDF\u1CD0-\u1CFF\u1D00-\u1D7F\u1D80-\u1DBF\u1DC0-\u1DFF\u1E00-\u1E7F\u1E80-\u1EFF\u1F00-\u1FFF\u2000-\u206F\u2070-\u209F\u20A0-\u20CF\u20D0-\u20FF\u2100-\u214F\u2150-\u218F\u2190-\u21FF\u2200-\u22FF\u2300-\u23FF\u2400-\u243F\u2440-\u245F\u2460-\u24FF\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u27C0-\u27EF\u27F0-\u27FF\u2800-\u28FF\u2900-\u297F\u2980-\u29FF\u2A00-\u2AFF\u2B00-\u2BFF\u2C00-\u2C5F\u2C60-\u2C7F\u2C80-\u2CFF\u2D00-\u2D2F\u2D30-\u2D7F\u2D80-\u2DDF\u2DE0-\u2DFF\u2E00-\u2E7F\u2E80-\u2EFF\u2F00-\u2FDF\u2FF0-\u2FFF\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u3100-\u312F\u3130-\u318F\u3190-\u319F\u31A0-\u31BF\u31C0-\u31EF\u31F0-\u31FF\u3200-\u32FF\u3300-\u33FF\u3400-\u4DBF\u4DC0-\u4DFF\u4E00-\u9FFF\uA000-\uA48F\uA490-\uA4CF\uA4D0-\uA4FF\uA500-\uA63F\uA640-\uA69F\uA6A0-\uA6FF\uA700-\uA71F\uA720-\uA7FF\uA800-\uA82F\uA830-\uA83F\uA840-\uA87F\uA880-\uA8DF\uA8E0-\uA8FF\uA900-\uA92F\uA930-\uA95F\uA960-\uA97F\uA980-\uA9DF\uA9E0-\uA9FF\uAA00-\uAA5F\uAA60-\uAA7F\uAA80-\uAADF\uAAE0-\uAAFF\uAB00-\uAB2F\uAB30-\uAB6F\uAB70-\uABBF\uABC0-\uABFF\uAC00-\uD7AF\uD7B0-\uD7FF\uD800-\uDB7F\uDB80-\uDBFF\uDC00-\uDFFF\uE000-\uF8FF\uF900-\uFAFF\uFB00-\uFB4F\uFB50-\uFDFF\uFE00-\uFE0F\uFE10-\uFE1F\uFE20-\uFE2F\uFE30-\uFE4F\uFE50-\uFE6F\uFE70-\uFEFF\uFF00-\uFFEF\uFFF0-\uFFFF\u20000-\u2A6DF\u2A700-\u2B73F\u2B740-\u2B81F\u2B820-\u2CEAF\u2CEB0-\u2EBEF\u2F800-\u2FA1F\u30000-\u3134F\u31350-\u323AF\uE0000-\uE007F\uE0100-\uE01EF\uF0000-\uFFFFF\u100000-\u10FFFF0-9\s\.,!?;:()\[\]{}"\'-]'
            filtered_text = re.sub(hebrew_pattern, '', text)
        else:
            filtered_text = re.sub(r'[^\w\s\.,!?;:()\[\]{}"\'-]', '', text)
        
        filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
        return self._remove_repetitions(filtered_text)
    
    def _remove_repetitions(self, text: str) -> str:
        """Remove repeated words/phrases from transcription"""
        words = text.split()
        if len(words) < 3:
            return text
        
        cleaned_words = self._remove_triple_repetitions(words)
        cleaned_text = ' '.join(cleaned_words)
        
        cleaned_text = self._remove_pattern_repetitions(cleaned_text)
        cleaned_text = self._cleanup_text_formatting(cleaned_text)
        
        return cleaned_text
    
    def _remove_triple_repetitions(self, words: list) -> list:
        """Remove triple and consecutive word repetitions"""
        cleaned_words = []
        i = 0
        while i < len(words):
            if i + 2 < len(words) and words[i] == words[i + 1] == words[i + 2]:
                cleaned_words.append(words[i])
                i += 3
                while i < len(words) and words[i] == words[i - 1]:
                    i += 1
            else:
                cleaned_words.append(words[i])
                i += 1
        return cleaned_words
    
    def _remove_pattern_repetitions(self, text: str) -> str:
        """Remove comma-separated and consecutive repetition patterns"""
        # Remove comma-separated repetition patterns
        pattern = r'(\b\w+\b)(?:\s*,\s*\1\s*)+'
        text = re.sub(pattern, r'\1', text)
        
        # Remove consecutive word repetition patterns
        pattern = r'(\b\w+\b)(?:\s+\1\s*)+'
        text = re.sub(pattern, r'\1', text)
        
        return text
    
    def _cleanup_text_formatting(self, text: str) -> str:
        """Clean up text formatting and spacing"""
        text = re.sub(r'\s*,\s*$', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def validate_transcription_quality(self, text: str) -> Dict[str, Any]:
        """Validate transcription quality and detect repetition issues"""
        words = text.split()
        word_counts = self._count_word_frequency(words)
        
        total_words = len(words)
        unique_words = len(word_counts)
        repetition_ratio = unique_words / total_words if total_words > 0 else 1.0
        
        suspicious_patterns = self._detect_suspicious_patterns(text, word_counts, total_words)
        quality_score = repetition_ratio * 100
        
        self._log_quality_issues(suspicious_patterns, quality_score)
        
        return self._create_quality_result(quality_score, total_words, unique_words, repetition_ratio, suspicious_patterns)
    
    def _create_quality_result(self, quality_score: float, total_words: int, unique_words: int, repetition_ratio: float, suspicious_patterns: list) -> dict:
        """Create quality result dictionary"""
        return {
            'quality_score': quality_score,
            'total_words': total_words,
            'unique_words': unique_words,
            'repetition_ratio': repetition_ratio,
            'suspicious_patterns': suspicious_patterns,
            'is_acceptable': quality_score > 50 and len(suspicious_patterns) == 0
        }
    
    def _count_word_frequency(self, words: list) -> dict:
        """Count frequency of each word"""
        word_counts = {}
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word:
                word_counts[clean_word] = word_counts.get(clean_word, 0) + 1
        return word_counts
    
    def _detect_suspicious_patterns(self, text: str, word_counts: dict, total_words: int) -> list:
        """Detect suspicious repetition patterns"""
        suspicious_patterns = []
        
        # Check for high-frequency words
        for word, count in word_counts.items():
            if count > total_words * 0.3:
                suspicious_patterns.append(f"'{word}' appears {count} times ({count/total_words*100:.1f}%)")
        
        # Check for comma-separated repetition
        comma_pattern = r'(\b\w+\b)(?:\s*,\s*\1\s*)+'
        if re.search(comma_pattern, text):
            suspicious_patterns.append("Comma-separated repetition detected")
        
        # Check for consecutive repetition
        consecutive_pattern = r'(\b\w+\b)(?:\s+\1\s*)+'
        if re.search(consecutive_pattern, text):
            suspicious_patterns.append("Consecutive repetition detected")
        
        return suspicious_patterns
    
    def _log_quality_issues(self, suspicious_patterns: list, quality_score: float):
        """Log quality issues if detected"""
        if suspicious_patterns:
            logger.warning(f"⚠️ Transcription quality issues detected:")
            for pattern in suspicious_patterns:
                logger.warning(f"   - {pattern}")
            logger.warning(f"   Quality score: {quality_score:.1f}/100")
