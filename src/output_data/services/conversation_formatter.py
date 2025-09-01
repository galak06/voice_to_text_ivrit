"""
Conversation Formatter Service
Formats transcription output as natural conversation between speakers
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

from src.utils.config_manager import ConfigManager


class ConversationFormatter:
    """
    Formats transcription output as natural conversation between speakers.
    
    This service follows the Single Responsibility Principle by handling only
    conversation formatting logic, and uses dependency injection for configuration.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the conversation formatter.
        
        Args:
            config_manager: Configuration manager for dependency injection
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Load configuration with defaults
        self.time_gap_threshold = self._get_config_value('time_gap_threshold', 3.0)
        self.min_segment_duration = self._get_config_value('min_segment_duration', 0.5)
        self.include_timing = self._get_config_value('include_timing', True)
        self.include_chunk_source = self._get_config_value('include_chunk_source', False)
        
        # Load paragraph grouping configuration
        self.paragraph_grouping_enabled = self._get_config_value('paragraph_grouping.enabled', True)
        self.max_gap_seconds = self._get_config_value('paragraph_grouping.max_gap_seconds', 2.0)
        self.min_paragraph_duration = self._get_config_value('paragraph_grouping.min_paragraph_duration', 1.0)
        
        # Load output format configuration
        self.output_formats = self._get_config_value('output_formats', {
            'txt': True,
            'json': True,
            'docx': False
        })
        
        # Load speaker display configuration
        self.show_emojis = self._get_config_value('speaker_display.show_emojis', True)
        self.show_timing = self._get_config_value('speaker_display.show_timing', True)
        self.show_duration = self._get_config_value('speaker_display.show_duration', True)
        
        # Check if speaker recognition is disabled
        self.speaker_recognition_disabled = self._is_speaker_recognition_disabled()
        if self.speaker_recognition_disabled:
            self.logger.info("🎤 Speaker recognition is disabled - will use single speaker mode")
    
    def _get_config_value(self, key: str, default_value: Any) -> Any:
        """Get configuration value with fallback to default."""
        try:
            if hasattr(self.config_manager.config, 'speaker') and hasattr(self.config_manager.config.speaker, 'conversation_formatting'):
                config = self.config_manager.config.speaker.conversation_formatting
                
                # Handle nested keys (e.g., 'paragraph_grouping.enabled')
                if '.' in key:
                    keys = key.split('.')
                    current = config
                    for k in keys:
                        if hasattr(current, k):
                            current = getattr(current, k)
                        else:
                            return default_value
                    return current
                else:
                    return getattr(config, key, default_value)
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
    
    def format_as_conversation(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert speaker-separated data to conversation format.
        
        Args:
            merged_data: Merged transcription data with speaker information
            
        Returns:
            Dictionary containing conversation-formatted data
        """
        try:
            self.logger.info("🔄 Formatting transcription as conversation...")
            
            if self.speaker_recognition_disabled:
                self.logger.info("🎤 Speaker recognition disabled - using single speaker mode")
                return self._format_as_single_speaker(merged_data)
            else:
                self.logger.info("🎤 Speaker recognition enabled - using multi-speaker mode")
                return self._format_as_multi_speaker(merged_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error formatting conversation: {e}")
            raise
    
    def _format_as_single_speaker(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format transcription as single speaker (when speaker recognition is disabled)."""
        try:
            # Collect all text segments and sort by time
            all_segments = self._collect_text_segments_only(merged_data)
            all_segments.sort(key=lambda x: x['start'])
            
            # Group consecutive segments into paragraphs
            conversation_turns = self._group_text_into_paragraphs(all_segments)
            
            # Generate metadata
            conversation_metadata = self._generate_conversation_metadata(merged_data, conversation_turns)
            
            formatted_data = {
                'conversation_turns': conversation_turns,
                'metadata': conversation_metadata,
                'speaker_summary': {'SINGLE_SPEAKER': {'total_segments': len(all_segments), 'total_duration': merged_data.get('total_duration', 0)}},
                'formatted_at': datetime.now().isoformat(),
                'format_version': '1.0',
                'mode': 'single_speaker'
            }
            
            self.logger.info(f"✅ Single speaker formatting completed: {len(conversation_turns)} paragraphs")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"❌ Error in single speaker formatting: {e}")
            raise
    
    def _format_as_multi_speaker(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format transcription as multi-speaker conversation."""
        try:
            # Collect all segments from all speakers and sort by start time
            all_segments = self._collect_all_segments(merged_data)
            
            # Sort all segments by start time to create chronological conversation
            all_segments.sort(key=lambda x: x['start'])
            
            # Group consecutive segments from the same speaker into conversation turns
            conversation_turns = self._group_into_conversation_turns(all_segments)
            
            # Generate conversation metadata
            conversation_metadata = self._generate_conversation_metadata(merged_data, conversation_turns)
            
            formatted_data = {
                'conversation_turns': conversation_turns,
                'metadata': conversation_metadata,
                'speaker_summary': self._generate_speaker_summary(merged_data),
                'formatted_at': datetime.now().isoformat(),
                'format_version': '1.0',
                'mode': 'multi_speaker'
            }
            
            self.logger.info(f"✅ Multi-speaker formatting completed: {len(conversation_turns)} turns")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"❌ Error in multi-speaker formatting: {e}")
            raise
    
    def _collect_all_segments(self, merged_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect all segments from all speakers."""
        all_segments = []
        
        for speaker_name, segments in merged_data.get('speakers', {}).items():
            for segment in segments:
                all_segments.append({
                    'speaker': speaker_name,
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'duration': segment.get('duration', 0),
                    'chunk_source': segment.get('chunk_source', 'unknown')
                })
        
        return all_segments
    
    def _group_into_conversation_turns(self, all_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group consecutive segments from the same speaker into conversation turns."""
        if not all_segments:
            return []
        
        conversation_turns = []
        current_speaker = None
        current_turn = []
        current_timing = []
        
        for i, segment in enumerate(all_segments):
            # Check if this should start a new speaker turn
            should_start_new_turn = self._should_start_new_turn(i, segment, all_segments)
            
            if should_start_new_turn and current_turn:
                # Add the current turn to conversation
                turn_data = self._create_turn_data(current_speaker, current_turn, current_timing)
                conversation_turns.append(turn_data)
                
                # Start new turn
                current_speaker = segment['speaker']
                current_turn = [segment['text']]
                current_timing = [segment['start'], segment['end']]
            else:
                # Continue current turn
                if current_speaker is None:
                    current_speaker = segment['speaker']
                current_turn.append(segment['text'])
                current_timing.append(segment['end'])
        
        # Add the last turn
        if current_turn:
            turn_data = self._create_turn_data(current_speaker, current_turn, current_timing)
            conversation_turns.append(turn_data)
        
        return conversation_turns
    
    def _should_start_new_turn(self, index: int, segment: Dict[str, Any], all_segments: List[Dict[str, Any]]) -> bool:
        """Determine if a new speaker turn should start."""
        if index == 0:
            return True
        
        prev_segment = all_segments[index - 1]
        speaker_changed = segment['speaker'] != prev_segment['speaker']
        time_gap = segment['start'] - prev_segment['end']
        
        return speaker_changed or time_gap > self.time_gap_threshold
    
    def _create_turn_data(self, speaker: Optional[str], texts: List[str], timing: List[float]) -> Dict[str, Any]:
        """Create a conversation turn data structure."""
        return {
            'speaker': speaker or 'UNKNOWN_SPEAKER',
            'texts': texts,
            'start_time': timing[0],
            'end_time': timing[-1],
            'duration': timing[-1] - timing[0],
            'text_count': len(texts),
            'combined_text': ' '.join(texts)
        }
    
    def _generate_conversation_metadata(self, merged_data: Dict[str, Any], conversation_turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate metadata about the conversation."""
        total_duration = merged_data.get('total_duration', 0)
        total_chunks = merged_data.get('total_chunks', 0)
        
        return {
            'total_turns': len(conversation_turns),
            'total_duration': total_duration,
            'total_chunks': total_chunks,
            'average_turn_duration': total_duration / len(conversation_turns) if conversation_turns else 0,
            'formatting_config': {
                'time_gap_threshold': self.time_gap_threshold,
                'min_segment_duration': self.min_segment_duration,
                'include_timing': self.include_timing,
                'include_chunk_source': self.include_chunk_source
            }
        }
    
    def _generate_speaker_summary(self, merged_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate summary statistics for each speaker."""
        speaker_summary = {}
        
        for speaker_name, segments in merged_data.get('speakers', {}).items():
            if segments:
                total_duration = sum(seg.get('duration', 0) for seg in segments)
                segment_count = len(segments)
                
                speaker_summary[speaker_name] = {
                    'total_segments': segment_count,
                    'total_duration': total_duration,
                    'average_segment_duration': total_duration / segment_count if segment_count > 0 else 0,
                    'participation_percentage': (total_duration / merged_data.get('total_duration', 1)) * 100 if merged_data.get('total_duration', 0) > 0 else 0
                }
        
        return speaker_summary
    
    def _collect_text_segments_only(self, merged_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect text segments when speaker recognition is disabled."""
        all_segments = []
        
        # Try to get segments from different possible locations
        if 'transcription_data' in merged_data and 'segments' in merged_data['transcription_data']:
            segments = merged_data['transcription_data']['segments']
            for segment in segments:
                all_segments.append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'duration': segment.get('duration', 0)
                })
        elif 'segments' in merged_data:
            segments = merged_data['segments']
            for segment in segments:
                all_segments.append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'duration': segment.get('duration', 0)
                })
        else:
            # Fallback: create segments from full text
            full_text = merged_data.get('text', merged_data.get('full_text', ''))
            if full_text:
                all_segments.append({
                    'start': 0,
                    'end': merged_data.get('total_duration', 0),
                    'text': full_text,
                    'duration': merged_data.get('total_duration', 0)
                })
        
        return all_segments
    
    def _group_text_into_paragraphs(self, all_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group text segments into paragraphs for single speaker mode."""
        if not all_segments:
            return []
        
        conversation_turns = []
        current_turn = []
        current_timing = []
        
        for i, segment in enumerate(all_segments):
            # Check if this should start a new paragraph
            should_start_new_paragraph = False
            
            if i == 0:
                # First segment always starts a new paragraph
                should_start_new_paragraph = True
            else:
                # Check if there's a significant gap (>3 seconds)
                prev_segment = all_segments[i-1]
                time_gap = segment['start'] - prev_segment['end']
                
                if time_gap > self.time_gap_threshold:
                    should_start_new_paragraph = True
            
            if should_start_new_paragraph and current_turn:
                # Add the current paragraph to conversation
                turn_data = self._create_single_speaker_turn_data(current_turn, current_timing)
                conversation_turns.append(turn_data)
                
                # Start new paragraph
                current_turn = [segment['text']]
                current_timing = [segment['start'], segment['end']]
            else:
                # Continue current paragraph
                current_turn.append(segment['text'])
                current_timing.append(segment['end'])
        
        # Add the last paragraph
        if current_turn:
            turn_data = self._create_single_speaker_turn_data(current_turn, current_timing)
            conversation_turns.append(turn_data)
        
        return conversation_turns
    
    def _create_single_speaker_turn_data(self, texts: List[str], timing: List[float]) -> Dict[str, Any]:
        """Create a conversation turn data structure for single speaker mode."""
        return {
            'speaker': 'SINGLE_SPEAKER',
            'texts': texts,
            'start_time': timing[0],
            'end_time': timing[-1],
            'duration': timing[-1] - timing[0],
            'text_count': len(texts),
            'combined_text': ' '.join(texts)
        }


class ConversationOutputGenerator:
    """
    Generates conversation-formatted output files (TXT, DOCX, JSON).
    
    This service handles the actual file generation using the formatted
    conversation data from ConversationFormatter.
    """
    
    def __init__(self, config_manager: ConfigManager, output_dir: Path):
        """
        Initialize the conversation output generator.
        
        Args:
            config_manager: Configuration manager for dependency injection
            output_dir: Directory for output files
        """
        self.config_manager = config_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_text_output(self, formatted_data: Dict[str, Any], output_filename: str = None) -> str:
        """Generate TXT output with conversation format."""
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"conversation_{timestamp}.txt"
        
        output_path = self.output_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write("CONVERSATION TRANSCRIPT\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {formatted_data['formatted_at']}\n")
                f.write(f"Total turns: {formatted_data['metadata']['total_turns']}\n")
                f.write(f"Total duration: {formatted_data['metadata']['total_duration']:.2f} seconds\n")
                f.write(f"Format version: {formatted_data['format_version']}\n")
                f.write("=" * 50 + "\n\n")
                
                # Write conversation turns
                mode = formatted_data.get('mode', 'unknown')
                if mode == 'single_speaker':
                    f.write("📝 TRANSCRIPTION PARAGRAPHS\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for turn in formatted_data['conversation_turns']:
                        timing_range = f"[{turn['start_time']:.1f}s - {turn['end_time']:.1f}s]"
                        f.write(f"{timing_range}:\n")
                        f.write(f"{turn['combined_text']}\n\n")
                else:
                    f.write("💬 CONVERSATION TRANSCRIPT\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for turn in formatted_data['conversation_turns']:
                        timing_range = f"[{turn['start_time']:.1f}s - {turn['end_time']:.1f}s]"
                        f.write(f"🎤 {turn['speaker']} {timing_range}:\n")
                        f.write(f"{turn['combined_text']}\n\n")
                
                # Write summary
                mode = formatted_data.get('mode', 'unknown')
                if mode == 'single_speaker':
                    f.write("\n" + "=" * 50 + "\n")
                    f.write("TRANSCRIPTION SUMMARY\n")
                    f.write("=" * 50 + "\n")
                    
                    summary = formatted_data['speaker_summary']['SINGLE_SPEAKER']
                    f.write(f"\n📝 Single Speaker Mode:\n")
                    f.write(f"  Total paragraphs: {summary['total_segments']}\n")
                    f.write(f"  Total duration: {summary['total_duration']:.1f}s\n")
                else:
                    f.write("\n" + "=" * 50 + "\n")
                    f.write("SPEAKER SUMMARY\n")
                    f.write("=" * 50 + "\n")
                    
                    for speaker_name, summary in formatted_data['speaker_summary'].items():
                        f.write(f"\n🎤 {speaker_name}:\n")
                        f.write(f"  Total segments: {summary['total_segments']}\n")
                        f.write(f"  Total duration: {summary['total_duration']:.1f}s\n")
                        f.write(f"  Average segment: {summary['average_segment_duration']:.1f}s\n")
                        f.write(f"  Participation: {summary['participation_percentage']:.1f}%\n")
            
            self.logger.info(f"✅ Generated TXT output: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating TXT output: {e}")
            raise
    
    def generate_json_output(self, formatted_data: Dict[str, Any], output_filename: str = None) -> str:
        """Generate JSON output with conversation format."""
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"conversation_{timestamp}.json"
        
        output_path = self.output_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Generated JSON output: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating JSON output: {e}")
            raise
    
    def generate_all_outputs(self, formatted_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all output formats."""
        outputs = {}
        
        try:
            # Generate TXT output
            txt_path = self.generate_text_output(formatted_data)
            if txt_path:
                outputs['txt'] = txt_path
            
            # Generate JSON output
            json_path = self.generate_json_output(formatted_data)
            if json_path:
                outputs['json'] = json_path
            
            self.logger.info(f"✅ Generated {len(outputs)} conversation output files")
            return outputs
            
        except Exception as e:
            self.logger.error(f"❌ Error generating conversation outputs: {e}")
            raise
