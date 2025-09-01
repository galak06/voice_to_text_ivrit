#!/usr/bin/env python3
"""
Output strategy for creating final transcription results with intelligent deduplication
Follows SOLID principles with dependency injection
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class OutputStrategy(ABC):
    """Abstract base class for output strategies"""
    
    @abstractmethod
    def create_final_output(self, segments: List[Dict[str, Any]]) -> str:
        """Create final output from segments"""
        pass


class IntelligentDeduplicationStrategy(ABC):
    """Abstract base class for deduplication strategies"""
    
    @abstractmethod
    def deduplicate_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate overlapping segments"""
        pass


class OverlappingTextDeduplicator(IntelligentDeduplicationStrategy):
    """Handles intelligent deduplication of overlapping text between audio chunks"""
    
    def __init__(self, config_manager):
        """Initialize with ConfigManager dependency injection"""
        self.config_manager = config_manager
        logger.info("🚀 Initializing OverlappingTextDeduplicator")
    
    def deduplicate_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Intelligent deduplication that removes overlapping text portions ONLY if they are actually the same"""
        if not segments:
            return []
        
        logger.info(f"🔄 Starting intelligent deduplication for {len(segments)} segments...")
        
        processed_segments = []
        overlap_count = 0
        
        for i, current_segment in enumerate(segments):
            if i == 0:
                processed_segments.append(current_segment.copy())
                continue
            
            prev_segment = processed_segments[-1]
            if self._segments_overlap(prev_segment, current_segment):
                logger.debug(f"🔄 Detected overlap between segments {i-1} and {i}")
                logger.debug(f"   - Prev: {prev_segment.get('start', 0):.1f}s - {prev_segment.get('end', 0):.1f}s")
                logger.debug(f"   - Curr: {current_segment.get('start', 0):.1f}s - {current_segment.get('end', 0):.1f}s")
                
                processed_segment = self._remove_overlapping_text(prev_segment, current_segment)
                processed_segments.append(processed_segment)
                overlap_count += 1
            else:
                processed_segments.append(current_segment.copy())
        
        logger.info(f"✅ Intelligent deduplication completed: {len(segments)} → {len(processed_segments)} segments")
        logger.info(f"   - Overlaps detected and processed: {overlap_count}")
        return processed_segments
    
    def _segments_overlap(self, segment1: Dict[str, Any], segment2: Dict[str, Any]) -> bool:
        """Check if two segments overlap in time"""
        start1 = segment1.get('start', 0.0)
        end1 = segment1.get('end', 0.0)
        start2 = segment2.get('start', 0.0)
        end2 = segment2.get('end', 0.0)
        
        # Check for overlap (including small gaps)
        return start2 < end1 + 1.0  # Allow 1 second gap
    
    def _remove_overlapping_text(self, prev_segment: Dict[str, Any], current_segment: Dict[str, Any]) -> Dict[str, Any]:
        """Remove overlapping text portions between two segments ONLY if they are actually the same"""
        prev_start = prev_segment.get('start', 0.0)
        prev_end = prev_segment.get('end', 0.0)
        curr_start = current_segment.get('start', 0.0)
        curr_end = current_segment.get('end', 0.0)
        
        overlap_start = max(prev_start, curr_start)
        overlap_end = min(prev_end, curr_end)
        overlap_duration = overlap_end - overlap_start
        
        processed_segment = current_segment.copy()
        
        if overlap_duration > 0:
            prev_text = prev_segment.get('text', '')
            curr_text = current_segment.get('text', '')
            
            logger.debug(f"🔄 Processing overlap: {overlap_duration:.1f}s duration")
            logger.debug(f"   - Prev text end: '{prev_text[-50:]}...'")
            logger.debug(f"   - Curr text start: '{curr_text[:50]}...'")
            
            cleaned_text = self._remove_overlapping_text_portion(prev_text, curr_text)
            
            if cleaned_text != curr_text:
                chars_removed = len(curr_text) - len(cleaned_text)
                logger.info(f"✅ Overlap removed: {chars_removed} characters from chunk {current_segment.get('chunk_number', '?')}")
                logger.debug(f"   - Original: '{curr_text[:100]}...'")
                logger.debug(f"   - Cleaned: '{cleaned_text[:100]}...'")
                
                processed_segment['text'] = cleaned_text
                processed_segment['overlap_removed'] = True
                processed_segment['overlap_duration'] = overlap_duration
                processed_segment['overlap_with_chunk'] = prev_segment.get('chunk_number', 0)
                processed_segment['overlap_chars_removed'] = chars_removed
            else:
                logger.debug(f"ℹ️ No text overlap found despite time overlap")
        
        return processed_segment
    
    def _remove_overlapping_text_portion(self, prev_text: str, curr_text: str) -> str:
        """Remove overlapping text portion from the beginning of current text ONLY if it's actually the same"""
        if not prev_text or not curr_text:
            return curr_text
        
        overlap_text = self._find_actual_overlapping_text(prev_text, curr_text)
        if overlap_text:
            cleaned_text = curr_text[len(overlap_text):].strip()
            return cleaned_text
        
        return curr_text
    
    def _find_actual_overlapping_text(self, prev_text: str, curr_text: str) -> str:
        """Find the actual overlapping text between two segments using text similarity detection for overlap time"""
        if not prev_text or not curr_text:
            return ""
        
        # First try exact match
        exact_overlap = self._find_exact_overlap(prev_text, curr_text)
        if exact_overlap:
            return exact_overlap
        
        # If no exact match, try similarity detection for overlap time
        similarity_overlap = self._find_similarity_overlap(prev_text, curr_text)
        if similarity_overlap:
            return similarity_overlap
        
        # If still no match, try partial matching for Hebrew text
        partial_overlap = self._find_partial_hebrew_overlap(prev_text, curr_text)
        if partial_overlap:
            return partial_overlap
        
        return ""
    
    def _find_exact_overlap(self, prev_text: str, curr_text: str) -> str:
        """Find exact overlapping text with more flexible matching"""
        if not prev_text or not curr_text:
            return ""
        
        # Clean and normalize texts for comparison
        prev_clean = self._normalize_text(prev_text)
        curr_clean = self._normalize_text(curr_text)
        
        max_overlap_length = min(len(prev_clean), len(curr_clean), 100)
        
        for overlap_length in range(max_overlap_length, 10, -1):  # Minimum 10 chars for meaningful overlap
            prev_end = prev_clean[-overlap_length:]
            
            # Check if current text starts with this portion
            if curr_clean.startswith(prev_end):
                # Get the original text portion (not normalized)
                original_overlap = prev_text[-overlap_length:]
                if len(original_overlap.strip()) > 10:  # Ensure meaningful overlap
                    if not self._is_just_common_words(original_overlap):
                        logger.debug(f"🔄 Found exact overlap: '{original_overlap[:30]}...' ({overlap_length} chars)")
                        return original_overlap
        
        return ""
    
    def _find_similarity_overlap(self, prev_text: str, curr_text: str) -> str:
        """Find overlapping text using similarity detection for overlap time period"""
        # Estimate overlap time based on text length and position
        estimated_overlap_ratio = 5.0 / 30.0  # 5s overlap / 30s chunk
        
        # Calculate estimated overlap text length for both chunks
        prev_overlap_chars = int(len(prev_text) * estimated_overlap_ratio)
        curr_overlap_chars = int(len(curr_text) * estimated_overlap_ratio)
        
        # Get the text portions that likely correspond to the overlap time
        prev_overlap_text = prev_text[-prev_overlap_chars:] if prev_overlap_chars > 0 else ""
        curr_overlap_text = curr_text[:curr_overlap_chars] if curr_overlap_chars > 0 else ""
        
        if not prev_overlap_text or not curr_overlap_text:
            return ""
        
        # Calculate text similarity for these overlap portions
        similarity_score = self._calculate_text_similarity(prev_overlap_text, curr_overlap_text)
        
        # If similarity is high enough (e.g., > 70%), consider it overlapping text
        if similarity_score > 0.7:
            logger.debug(f"🔄 Found similar overlap: similarity {similarity_score:.2f}")
            return curr_text[:len(prev_overlap_text)]
        
        # If the estimated overlap didn't work, try a more flexible approach
        flexible_overlap = self._find_flexible_overlap(prev_text, curr_text)
        if flexible_overlap:
            return flexible_overlap
        
        return ""
    
    def _find_flexible_overlap(self, prev_text: str, curr_text: str) -> str:
        """Find overlapping text using a more flexible approach for common phrases"""
        if not prev_text or not curr_text:
            return ""
        
        # Look for common phrases that might indicate overlap
        max_phrase_length = min(len(prev_text), len(curr_text), 50)
        
        for phrase_length in range(max_phrase_length, 10, -1):
            # Get the end portion of previous text
            prev_end = prev_text[-phrase_length:]
            
            # Check if this phrase appears at the beginning of current text
            if curr_text.startswith(prev_end):
                # Calculate similarity for this specific phrase
                similarity = self._calculate_text_similarity(prev_end, curr_text[:phrase_length])
                
                if similarity > 0.6:  # Lower threshold for flexible detection
                    logger.debug(f"🔄 Found flexible overlap: '{prev_end[:30]}...' (similarity: {similarity:.2f})")
                    return curr_text[:phrase_length]
            
            # Also check for partial matches with high similarity
            for i in range(phrase_length, 10, -1):
                prev_partial = prev_text[-i:]
                curr_partial = curr_text[:i]
                
                # Check if the partial texts are similar enough
                if len(prev_partial) > 10 and len(curr_partial) > 10:
                    similarity = self._calculate_text_similarity(prev_partial, curr_partial)
                    
                    if similarity > 0.6:  # Lower threshold for partial matches
                        logger.debug(f"🔄 Found partial overlap: '{prev_partial[:30]}...' (similarity: {similarity:.2f})")
                        return curr_text[:i]
        
        return ""
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings (0.0 to 1.0)"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts (remove punctuation, extra spaces)
        text1_clean = self._normalize_text(text1)
        text2_clean = self._normalize_text(text2)
        
        if not text1_clean or not text2_clean:
            return 0.0
        
        # Split into words
        words1 = text1_clean.split()
        words2 = text2_clean.split()
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate word overlap
        common_words = set(words1) & set(words2)
        total_words = set(words1) | set(words2)
        
        if not total_words:
            return 0.0
        
        # Word-based similarity
        word_similarity = len(common_words) / len(total_words)
        
        # Character-based similarity for partial word matches
        char_similarity = self._calculate_character_similarity(text1_clean, text2_clean)
        
        # Combine both similarities (word similarity is more important)
        combined_similarity = (word_similarity * 0.7) + (char_similarity * 0.3)
        
        return combined_similarity
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (remove punctuation, extra spaces)"""
        if not text:
            return ""
        
        # Remove common punctuation and normalize spaces
        import re
        # Remove punctuation but keep Hebrew text intact
        normalized = re.sub(r'[^\w\s\u0590-\u05FF]', ' ', text)  # Keep Hebrew characters
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize spaces
        normalized = normalized.strip()
        
        return normalized
    
    def _calculate_character_similarity(self, text1: str, text2: str) -> float:
        """Calculate character-level similarity"""
        if not text1 or not text2:
            return 0.0
        
        # Simple character overlap calculation
        common_chars = 0
        total_chars = len(text1) + len(text2)
        
        # Count common characters (approximate)
        for char in set(text1):
            if char in text2:
                common_chars += min(text1.count(char), text2.count(char))
        
        if total_chars == 0:
            return 0.0
        
        return (common_chars * 2) / total_chars  # Normalize to 0-1 range
    
    def _find_partial_hebrew_overlap(self, prev_text: str, curr_text: str) -> str:
        """Find partial overlapping text for Hebrew content with flexible matching"""
        if not prev_text or not curr_text:
            return ""
        
        # Look for common phrases at the end of previous text and beginning of current text
        max_phrase_length = min(len(prev_text), len(curr_text), 80)
        
        for phrase_length in range(max_phrase_length, 15, -1):  # Minimum 15 chars for meaningful overlap
            # Get the end portion of previous text
            prev_end = prev_text[-phrase_length:]
            
            # Check if current text starts with this phrase (allowing for slight differences)
            if curr_text.startswith(prev_end):
                if len(prev_end.strip()) > 15:  # Ensure meaningful overlap
                    logger.debug(f"🔄 Found partial Hebrew overlap: '{prev_end[:30]}...' ({phrase_length} chars)")
                    return prev_end
            
            # Also try with some flexibility - check if current text starts with a similar phrase
            # Remove common prefixes like "אז" (so) from current text for comparison
            curr_start = curr_text[:phrase_length]
            if curr_start.startswith('אז '):
                curr_start = curr_start[3:]  # Remove "אז " prefix
                if prev_end.endswith(curr_start) and len(curr_start) > 10:
                    logger.debug(f"🔄 Found flexible Hebrew overlap: '{curr_start[:30]}...' ({len(curr_start)} chars)")
                    return curr_start
        
        return ""
    
    def _is_just_common_words(self, text: str) -> bool:
        """Check if text is just common words that shouldn't be considered overlap"""
        if not text or len(text.strip()) < 10:
            return True
        
        common_phrases = [
            "אז", "אז סיפרתי", "אז סיפרתי שבסוף", "בסוף מאי",
            "היה", "היו", "זה", "זהו", "אני", "אנחנו", "הוא", "היא",
            "של", "על", "ב", "ל", "מ", "אל", "עם", "עד", "אחרי", "לפני"
        ]
        
        text_lower = text.strip().lower()
        for phrase in common_phrases:
            if text_lower == phrase.lower():
                return True
        
        return False


class MergedOutputStrategy(OutputStrategy):
    """Strategy for creating merged output with intelligent deduplication"""
    
    def __init__(self, config_manager, deduplicator: IntelligentDeduplicationStrategy):
        """Initialize with ConfigManager and deduplicator dependency injection"""
        self.config_manager = config_manager
        self.deduplicator = deduplicator
        logger.info("🚀 Initializing MergedOutputStrategy")
    
    def create_final_output(self, segments: List[Any]) -> str:
        """Create final merged output from segments with deduplication"""
        if not segments:
            return ""
        
        logger.info(f"🔄 MergedOutputStrategy.create_final_output called with {len(segments)} segments")
        
        # Helper function to get segment attributes
        def get_segment_attr(seg, attr, default=0):
            if hasattr(seg, attr):
                return getattr(seg, attr, default)
            else:
                return seg.get(attr, default)
        
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: get_segment_attr(x, 'start', 0.0))
        
        if len(sorted_segments) >= 2:
            logger.info(f"   - First segment: {get_segment_attr(sorted_segments[0], 'start', 0):.1f}s - {get_segment_attr(sorted_segments[0], 'end', 0):.1f}s")
            logger.info(f"   - Second segment: {get_segment_attr(sorted_segments[1], 'start', 0):.1f}s - {get_segment_attr(sorted_segments[1], 'end', 0):.1f}s")
        
        # Apply intelligent deduplication
        logger.info(f"🔄 Calling deduplicator.deduplicate_segments...")
        deduplicated_segments = self.deduplicator.deduplicate_segments(sorted_segments)
        
        # Build final text
        final_text = ""
        for segment in deduplicated_segments:
            text = get_segment_attr(segment, 'text', '')
            if text:
                final_text += text + " "
        
        final_text = final_text.strip()
        
        logger.info(f"✅ Final output created: {len(final_text)} characters from {len(segments)} segments")
        return final_text
    
    def create_segmented_output(self, segments: List[Any]) -> List[Any]:
        """Create segmented output with deduplication metadata"""
        if not segments:
            return []
        
        # Sort segments by start time - handle both dict and object segments
        def get_start_time(seg):
            if hasattr(seg, 'start'):
                return getattr(seg, 'start', 0.0)
            else:
                return seg.get('start', 0.0)
        
        sorted_segments = sorted(segments, key=get_start_time)
        
        # Apply intelligent deduplication
        deduplicated_segments = self.deduplicator.deduplicate_segments(sorted_segments)
        
        return deduplicated_segments
    
    def create_text_output(self, processed_data: Dict[str, Any]) -> str:
        """Create text output from processed data"""
        try:
            # Extract text content from processed data
            text_content = processed_data.get('full_text', '') or processed_data.get('text', '')
            
            if not text_content:
                logger.warning("No text content available in processed data")
                return ""
            
            # Format the text content
            formatted_text = f"=== TRANSCRIPTION ===\n\n{text_content}"
            
            logger.info(f"✅ Text output created: {len(text_content)} characters")
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error creating text output: {e}")
            return ""
