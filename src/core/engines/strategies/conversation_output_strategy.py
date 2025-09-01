#!/usr/bin/env python3
"""
Conversation Output Strategy for creating conversation-formatted transcription results
Extends the existing OutputStrategy system with speaker-aware conversation formatting
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .output_strategy import OutputStrategy
from src.output_data.services import ConversationService

logger = logging.getLogger(__name__)


class ConversationOutputStrategy(OutputStrategy):
    """
    Strategy for creating conversation-formatted output with intelligent speaker handling.
    
    This strategy automatically detects speaker recognition settings and adapts
    the output format accordingly (multi-speaker conversation vs. single-speaker paragraphs).
    """
    
    def __init__(self, config_manager, conversation_service: ConversationService):
        """
        Initialize with ConfigManager and ConversationService dependency injection.
        
        Args:
            config_manager: Configuration manager for dependency injection
            conversation_service: Service for conversation formatting and output generation
        """
        self.config_manager = config_manager
        self.conversation_service = conversation_service
        logger.info("🚀 Initializing ConversationOutputStrategy")
        
        # Check speaker recognition status
        self._log_speaker_configuration()
    
    def _log_speaker_configuration(self):
        """Log the current speaker recognition configuration."""
        try:
            if hasattr(self.config_manager.config, 'disable_options'):
                disable_options = self.config_manager.config.disable_options
                speaker_disabled = (
                    getattr(disable_options, 'disable_speaker_detection', False) or
                    getattr(disable_options, 'disable_speaker_labeling', False) or
                    getattr(disable_options, 'disable_speaker_segmentation', False) or
                    getattr(disable_options, 'use_single_speaker_mode', False)
                )
                
                if speaker_disabled:
                    logger.info("🎤 Speaker recognition is DISABLED - will use single speaker mode")
                else:
                    logger.info("🎤 Speaker recognition is ENABLED - will use multi-speaker conversation mode")
            else:
                logger.info("🎤 Speaker recognition configuration not found - using default multi-speaker mode")
                
        except Exception as e:
            logger.warning(f"Could not determine speaker configuration: {e}")
            logger.info("🎤 Using default multi-speaker mode")
    
    def create_final_output(self, segments: List[Dict[str, Any]]) -> str:
        """
        Create final conversation-formatted output from segments.
        
        This method delegates to the conversation service for intelligent
        conversation formatting based on speaker recognition settings.
        
        Args:
            segments: List of transcription segments
            
        Returns:
            Formatted conversation text
        """
        try:
            logger.info(f"🔄 ConversationOutputStrategy.create_final_output called with {len(segments)} segments")
            
            if not segments:
                logger.warning("No segments provided, returning empty string")
                return ""
            
            # Create a mock merged data structure for the conversation service
            # This simulates what would come from chunk merging
            merged_data = self._create_merged_data_from_segments(segments)
            
            # Use the conversation service to format the output
            formatted_data = self.conversation_service.conversation_formatter.format_as_conversation(merged_data)
            
            # Extract the conversation text
            conversation_text = self._extract_conversation_text(formatted_data)
            
            logger.info(f"✅ Conversation output created: {len(conversation_text)} characters")
            logger.info(f"   - Mode: {formatted_data.get('mode', 'unknown')}")
            logger.info(f"   - Turns/Paragraphs: {len(formatted_data.get('conversation_turns', []))}")
            
            return conversation_text
            
        except Exception as e:
            logger.error(f"❌ Error creating conversation output: {e}")
            # Fallback to simple text concatenation
            return self._fallback_text_creation(segments)
    
    def create_segmented_output(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create segmented output with conversation formatting metadata.
        
        Args:
            segments: List of transcription segments
            
        Returns:
            List of segments with conversation formatting metadata
        """
        try:
            logger.info(f"🔄 ConversationOutputStrategy.create_segmented_output called with {len(segments)} segments")
            
            if not segments:
                return []
            
            # Create merged data structure
            merged_data = self._create_merged_data_from_segments(segments)
            
            # Format as conversation
            formatted_data = self.conversation_service.conversation_formatter.format_as_conversation(merged_data)
            
            # Convert conversation turns back to segments with metadata
            conversation_segments = self._convert_conversation_to_segments(formatted_data)
            
            logger.info(f"✅ Conversation segmented output created: {len(conversation_segments)} segments")
            return conversation_segments
            
        except Exception as e:
            logger.error(f"❌ Error creating conversation segmented output: {e}")
            # Fallback to original segments
            return segments
    
    def create_conversation_files(self, segments: List[Dict[str, Any]], output_dir: Optional[Path] = None) -> Dict[str, str]:
        """
        Create conversation output files (TXT, JSON) from segments.
        
        Args:
            segments: List of transcription segments
            output_dir: Optional output directory (uses config default if not provided)
            
        Returns:
            Dictionary containing generated output file paths
        """
        try:
            logger.info(f"🔄 Creating conversation files from {len(segments)} segments")
            
            if not segments:
                logger.warning("No segments provided, cannot create conversation files")
                return {}
            
            # Create merged data structure
            merged_data = self._create_merged_data_from_segments(segments)
            
            # Use the conversation service to generate all outputs
            if output_dir:
                # Temporarily override the output directory
                original_output_dir = self.conversation_service.output_dir
                self.conversation_service.output_dir = Path(output_dir)
                try:
                    result = self.conversation_service.generate_conversation_from_chunks()
                finally:
                    self.conversation_service.output_dir = original_output_dir
            else:
                result = self.conversation_service.generate_conversation_from_chunks()
            
            if result.get('success'):
                logger.info(f"✅ Conversation files created successfully")
                logger.info(f"   - Output files: {list(result.get('output_files', {}).keys())}")
                return result.get('output_files', {})
            else:
                logger.error(f"❌ Failed to create conversation files: {result.get('error', 'Unknown error')}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error creating conversation files: {e}")
            return {}
    
    def _create_merged_data_from_segments(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a merged data structure from segments for the conversation service."""
        if not segments:
            return {}
        
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: x.get('start', 0))
        
        # Calculate total duration
        total_duration = 0
        if sorted_segments:
            total_duration = sorted_segments[-1].get('end', 0) - sorted_segments[0].get('start', 0)
        
        # Check if we have speaker information
        has_speakers = any('speaker' in seg for seg in segments)
        
        if has_speakers:
            # Multi-speaker mode
            speakers_data = {}
            for segment in sorted_segments:
                speaker = segment.get('speaker', 'UNKNOWN_SPEAKER')
                if speaker not in speakers_data:
                    speakers_data[speaker] = []
                
                speakers_data[speaker].append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'duration': segment.get('end', 0) - segment.get('start', 0),
                    'chunk_source': segment.get('chunk_source', 'unknown')
                })
            
            return {
                'total_duration': total_duration,
                'total_chunks': 1,  # Single chunk of segments
                'speakers': speakers_data,
                'segments': sorted_segments
            }
        else:
            # Single speaker mode - create segments structure
            segments_data = []
            for segment in sorted_segments:
                segments_data.append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'duration': segment.get('end', 0) - segment.get('start', 0)
                })
            
            return {
                'total_duration': total_duration,
                'total_chunks': 1,
                'segments': segments_data,
                'text': ' '.join(seg.get('text', '') for seg in sorted_segments)
            }
    
    def _extract_conversation_text(self, formatted_data: Dict[str, Any]) -> str:
        """Extract conversation text from formatted data."""
        conversation_turns = formatted_data.get('conversation_turns', [])
        
        if not conversation_turns:
            return ""
        
        # Build conversation text
        conversation_lines = []
        for turn in conversation_turns:
            speaker = turn.get('speaker', 'UNKNOWN')
            text = turn.get('combined_text', '')
            start_time = turn.get('start_time', 0)
            end_time = turn.get('end_time', 0)
            
            if formatted_data.get('mode') == 'single_speaker':
                # Single speaker mode - just show timing and text
                conversation_lines.append(f"[{start_time:.1f}s - {end_time:.1f}s] {text}")
            else:
                # Multi-speaker mode - show speaker and timing
                conversation_lines.append(f"{speaker} [{start_time:.1f}s - {end_time:.1f}s]: {text}")
        
        return '\n\n'.join(conversation_lines)
    
    def _convert_conversation_to_segments(self, formatted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert conversation turns back to segments with metadata."""
        conversation_turns = formatted_data.get('conversation_turns', [])
        
        segments = []
        for turn in conversation_turns:
            segment = {
                'start': turn.get('start_time', 0),
                'end': turn.get('end_time', 0),
                'text': turn.get('combined_text', ''),
                'speaker': turn.get('speaker', 'UNKNOWN'),
                'duration': turn.get('duration', 0),
                'text_count': turn.get('text_count', 0),
                'conversation_mode': formatted_data.get('mode', 'unknown'),
                'turn_number': len(segments) + 1
            }
            segments.append(segment)
        
        return segments
    
    def _fallback_text_creation(self, segments: List[Dict[str, Any]]) -> str:
        """Fallback method for creating text when conversation formatting fails."""
        logger.warning("Using fallback text creation method")
        
        if not segments:
            return ""
        
        # Simple concatenation of segment texts
        texts = []
        for segment in sorted(segments, key=lambda x: x.get('start', 0)):
            text = segment.get('text', '')
            if text:
                texts.append(text)
        
        return ' '.join(texts)
