#!/usr/bin/env python3
"""
Output manager for transcription results with caching and output strategy injection
"""

import os
import logging
from typing import Dict, Any, List, Union, Optional
from pathlib import Path

# Import default output path
from definition import TRANSCRIPTIONS_DIR
DEFAULT_OUTPUT_PATH = TRANSCRIPTIONS_DIR

from src.output_data.utils.data_utils import DataUtils
from src.output_data.formatters.text_formatter import TextFormatter
from src.output_data.formatters.json_formatter import JsonFormatter

from .file_manager import FileManager
from src.output_data.utils.path_utils import PathUtils

logger = logging.getLogger(__name__)

class OutputManager:
    """Main output manager for transcription results with caching and output strategy injection"""
    
    def __init__(self, output_base_path: str, data_utils: DataUtils, output_strategy: Any, config_manager: Any = None):
        """Initialize output manager with dependency injection and caching"""
        # Persist injected ConfigManager for downstream checks (e.g., speaker disable)
        self.config_manager = config_manager

        # Use ConfigManager for output paths if available, otherwise fallback to provided path
        if config_manager and hasattr(config_manager, 'get_directory_paths'):
            directory_paths = config_manager.get_directory_paths()
            self.output_base_path = directory_paths.get('transcriptions_dir', output_base_path)
            logger.info(f"🚀 OutputManager using ConfigManager path: {self.output_base_path}")
        else:
            self.output_base_path = output_base_path
            logger.info(f"⚠️ OutputManager using fallback path: {self.output_base_path}")
        
        self.data_utils = data_utils or DataUtils()
        
        # Inject output strategy for intelligent text processing
        self.output_strategy = output_strategy
        if self.output_strategy:
            logger.info("🚀 OutputManager initialized with injected output strategy")
        else:
            logger.info("⚠️ OutputManager initialized without output strategy - using legacy processing")
        
        # Cache for processed data to avoid duplicate processing
        self._processed_data_cache = {}
        self._speakers_cache = {}
        self._text_content_cache = {}
        
        # Ensure base output directory exists
        os.makedirs(self.output_base_path, exist_ok=True)
    
    def save_transcription(
        self,
        transcription_data: Any,
        audio_file: str,
        model: Optional[str] = None,
        engine: Optional[str] = None,
        input_metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Save transcription in JSON and TXT formats only. High-quality DOCX is generated separately."""
        try:
            logger.info(f"💾 SAVING TRANSCRIPTION:")
            logger.info(f"   - Audio file: {audio_file}")
            logger.info(f"   - Model: {model}")
            logger.info(f"   - Engine: {engine}")
            logger.info(f"   - Session ID: {session_id}")
            
            # Convert dataclass to dict if needed
            data_dict = self.data_utils.convert_transcription_result_to_dict(transcription_data)

            # Resolve model/engine defaults from data if not provided
            model_final = model or self.data_utils.get_model_name(data_dict) or "unknown-model"
            
            # Extract engine information - TranscriptionResult has model_name but not engine
            # Use the provided engine parameter or extract from data, or use a default based on model
            engine_final = engine
            if not engine_final:
                # Try to get engine from data
                engine_final = data_dict.get('engine') or data_dict.get('engine_name')
                
                # If still no engine, infer from model name or use default
                if not engine_final:
                    if 'ct2' in model_final.lower() or 'ctranslate' in model_final.lower():
                        engine_final = "ctranslate2"
                    elif 'whisper' in model_final.lower():
                        engine_final = "whisper"
                    else:
                        engine_final = "transcription-engine"
            
            # Log input data structure
            logger.info(f"   - Input data type: {type(transcription_data)}")
            logger.info(f"   - Converted data keys: {list(data_dict.keys())}")
            logger.info(f"   - Final model: {model_final}")
            logger.info(f"   - Final engine: {engine_final}")
            
            # Extract file path
            input_file_path = self.data_utils.get_audio_file(data_dict) or audio_file
            
            # Create output directory with timestamp
            output_dir = self._create_output_directory(model_final, engine_final)
            
            # Process data using output strategy if available
            if self.output_strategy:
                logger.info("🔄 Using injected output strategy for intelligent text processing")
                # Extract segments from the data - check both 'segments' and 'speakers' fields
                segments = None
                if 'segments' in data_dict:
                    segments = data_dict['segments']
                elif 'speakers' in data_dict:
                    # Extract segments from speakers data
                    speakers_data = data_dict['speakers']
                    if isinstance(speakers_data, dict) and '0' in speakers_data:
                        segments = speakers_data['0']  # Get segments from speaker '0'
                        logger.info(f"🔄 Extracted {len(segments)} segments from speakers data")
                
                if segments:
                    # Use the output strategy to create final output with overlapping detection
                    logger.info(f"🔄 Applying overlapping detection and deduplication to {len(segments)} segments...")
                    
                    # Log first few segments for debugging
                    for i, seg in enumerate(segments[:3]):
                        # Handle both dict and object segments
                        if hasattr(seg, 'start'):
                            start_time = getattr(seg, 'start', 0)
                            end_time = getattr(seg, 'end', 0)
                            text_content = getattr(seg, 'text', '')[:50] if getattr(seg, 'text', '') else ''
                        else:
                            start_time = seg.get('start', 0)
                            end_time = seg.get('end', 0)
                            text_content = seg.get('text', '')[:50] if seg.get('text', '') else ''
                        
                        logger.info(f"   - Segment {i}: {start_time:.1f}s - {end_time:.1f}s, text: '{text_content}...'")
                    
                    processed_text = self.output_strategy.create_final_output(segments)
                    deduplicated_segments = self.output_strategy.create_segmented_output(segments)
                    
                    # Log overlapping detection results
                    original_chars = 0
                    for seg in segments:
                        if hasattr(seg, 'text'):
                            original_chars += len(getattr(seg, 'text', ''))
                        else:
                            original_chars += len(seg.get('text', ''))
                    
                    final_chars = len(processed_text)
                    chars_removed = original_chars - final_chars
                    
                    logger.info(f"   - Output strategy processed: {len(segments)} → {len(deduplicated_segments)} segments")
                    logger.info(f"   - Final text created: {len(processed_text)} characters")
                    logger.info(f"   - Overlapping text removed: {chars_removed} characters ({chars_removed/original_chars*100:.1f}% reduction)")
                    
                    # Log segments that had overlap removed
                    overlap_segments = [seg for seg in deduplicated_segments if hasattr(seg, 'overlap_removed') and seg.overlap_removed]
                    if overlap_segments:
                        logger.info(f"   - Segments with overlap removed: {len(overlap_segments)}")
                        for seg in overlap_segments[:3]:  # Show first 3
                            logger.info(f"      - Chunk {getattr(seg, 'chunk_number', '?')}: {getattr(seg, 'overlap_duration', 0):.1f}s overlap removed")
                    
                    # Update the data with processed text
                    processed_data = data_dict.copy()
                    processed_data['full_text'] = processed_text
                    processed_data['_cached_text_content'] = processed_text
                    processed_data['_cached_word_count'] = len(processed_text.split()) if processed_text else 0
                    processed_data['_cached_char_count'] = len(processed_text) if processed_text else 0
                    processed_data['_deduplication_applied'] = True
                    logger.info(f"✅ Output strategy processed {len(segments)} segments into {len(processed_text)} characters")
                else:
                    # Fallback if no segments found
                    logger.warning("⚠️ No segments found in data, using legacy processing")
                    processed_data = self._process_data_legacy(data_dict)
            else:
                logger.info("🔄 Using legacy text processing (no output strategy injected)")
                processed_data = self._process_data_legacy(data_dict)
            
            # Save in different formats
            results = {}
            
            # Check configuration for output format
            config = getattr(self, 'config_manager', None)
            use_processed_text = True
            
            if config and hasattr(config, 'config') and config.config.output:
                output_config = config.config.output
                use_processed_text = getattr(output_config, 'use_processed_text_only', True)
            
            # Save JSON only - text and DOCX handled separately from processed text
            json_file = self._save_json(processed_data, output_dir, model_final, engine_final)
            if json_file:
                results['json'] = json_file
            
            # Note: High-quality DOCX is generated separately from processed text file
            # This ensures only the best quality output is produced without duplication
            
            # Generate conversation output if using conversation strategy
            if hasattr(self.output_strategy, 'create_conversation_files'):
                try:
                    logger.info("🔄 Generating conversation output files...")
                    conversation_files = self.output_strategy.create_conversation_files(
                        segments, output_dir
                    )
                    
                    # Add conversation files to results
                    for file_type, file_path in conversation_files.items():
                        results[f'conversation_{file_type}'] = file_path
                    
                    if conversation_files:
                        logger.info(f"✅ Generated {len(conversation_files)} conversation output files")
                    else:
                        logger.warning("⚠️ No conversation output files were generated")
                        
                except Exception as e:
                    logger.error(f"❌ Error generating conversation output: {e}")
                    # Continue with other outputs
            
            if results:
                logger.info(f"✅ Saved {len(results)} output files to {output_dir}")
                logger.info(f"   - Files: {list(results.keys())}")
                if use_processed_text:
                    logger.info("   - Using processed text only - no duplicate text files created")
                    
                    # Create text and DOCX files from processed text
                    try:
                        text_file = self._create_text_from_processed_data(processed_data, output_dir, model_final, engine_final)
                        if text_file:
                            results['text'] = text_file
                            
                            # Create DOCX from the text file
                            docx_file = self._create_docx_from_text_file(text_file, output_dir, model_final, engine_final)
                            if docx_file:
                                results['docx'] = docx_file
                                logger.info("✅ Created text and DOCX files from processed data")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not create text/DOCX from processed data: {e}")
                
                return results
            else:
                logger.error("❌ No output files were saved successfully")
                return {}
                
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
            return {}

    # Backwards-compatibility helpers expected by some pipeline tests
    def save_json(self, data: Dict[str, Any], base_filename: str) -> Dict[str, Any]:
        """Save a JSON file to the base output directory.
        Returns a dict with success and file_path for compatibility with tests."""
        try:
            os.makedirs(self.output_base_path, exist_ok=True)
            file_path = os.path.join(self.output_base_path, f"{base_filename}.json")
            if JsonFormatter.save_json_file(data, file_path):
                return {'success': True, 'file_path': file_path}
            return {'success': False}
        except Exception as e:
            logger.error(f"Error in save_json: {e}")
            return {'success': False}
    
    def generate_conversation_from_chunks(self, chunk_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate conversation output from existing chunk results.
        
        This method is useful for post-processing chunk results into conversation format
        without needing to re-run the transcription pipeline.
        
        Args:
            chunk_dir: Optional directory containing chunk JSON files (uses config default if not provided)
            
        Returns:
            Dictionary containing generated conversation output file paths and metadata
        """
        try:
            logger.info("🔄 Generating conversation output from existing chunks...")
            
            # Check if we have a conversation strategy
            if not hasattr(self.output_strategy, 'create_conversation_files'):
                logger.error("❌ Output strategy does not support conversation generation")
                return {
                    'success': False,
                    'error': 'Output strategy does not support conversation generation'
                }
            
            # Import conversation service for chunk processing
            from src.output_data.services import ConversationService
            
            # Create conversation service
            conversation_service = ConversationService(getattr(self, 'config_manager', None))
            
            # Generate conversation from chunks
            result = conversation_service.generate_conversation_from_chunks(
                Path(chunk_dir) if chunk_dir else None
            )
            
            if result.get('success'):
                logger.info("✅ Conversation generation completed successfully")
                logger.info(f"   - Output files: {list(result.get('output_files', {}).keys())}")
                logger.info(f"   - Mode: {result.get('metadata', {}).get('mode', 'unknown')}")
                logger.info(f"   - Speakers: {result.get('metadata', {}).get('speakers', [])}")
            else:
                logger.error(f"❌ Conversation generation failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating conversation from chunks: {e}")
            return {
                'success': False,
                'error': str(e)
            }


    
    def _process_and_cache_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data once and cache results for reuse using injected output strategy"""
        # Create a cache key based on data content
        cache_key = hash(str(sorted(data.items())))
        
        if cache_key in self._processed_data_cache:
            logger.info("Using cached processed data")
            return self._processed_data_cache[cache_key]
        
        # Use injected output strategy if available for intelligent text processing
        if self.output_strategy and 'segments' in data:
            logger.info("🚀 Using injected output strategy for intelligent text processing")
            
            try:
                # Get segments from data
                segments = data['segments']
                logger.info(f"   - Processing {len(segments)} segments with output strategy")
                
                # Use output strategy to create final output and deduplicated segments
                logger.info(f"🔄 Applying overlapping detection and deduplication to {len(segments)} segments...")
                
                # Log first few segments for debugging
                for i, seg in enumerate(segments[:3]):
                    logger.info(f"   - Segment {i}: {seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s, text: '{seg.get('text', '')[:50]}...'")
                
                final_text = self.output_strategy.create_final_output(segments)
                deduplicated_segments = self.output_strategy.create_segmented_output(segments)
                
                # Log overlapping detection results
                original_chars = sum(len(seg.get('text', '')) for seg in segments)
                final_chars = len(final_text)
                chars_removed = original_chars - final_chars
                
                logger.info(f"   - Output strategy processed: {len(segments)} → {len(deduplicated_segments)} segments")
                logger.info(f"   - Final text created: {len(final_text)} characters")
                logger.info(f"   - Overlapping text removed: {chars_removed} characters ({chars_removed/original_chars*100:.1f}% reduction)")
                
                # Log segments that had overlap removed
                overlap_segments = [seg for seg in deduplicated_segments if seg.get('overlap_removed', False)]
                if overlap_segments:
                    logger.info(f"   - Segments with overlap removed: {len(overlap_segments)}")
                    for seg in overlap_segments[:3]:  # Show first 3
                        logger.info(f"      - Chunk {seg.get('chunk_number', '?')}: {seg.get('overlap_duration', 0):.1f}s overlap removed")
                
                # Update data with processed results
                processed_data = data.copy()
                processed_data['segments'] = deduplicated_segments
                processed_data['full_text'] = final_text
                processed_data['_output_strategy_processed'] = True
                
                # Process speakers data from deduplicated segments
                speakers = self.data_utils.extract_speakers_data(processed_data)
                self._speakers_cache[cache_key] = speakers
                
                # Use the deduplicated text directly from the output strategy
                # This ensures overlapping text is actually removed
                text_content = final_text
                self._text_content_cache[cache_key] = text_content
                
                # Add metadata
                processed_data['_cached_speakers'] = speakers
                processed_data['_cached_text_content'] = text_content
                processed_data['_cached_word_count'] = len(text_content.split())
                processed_data['_cached_char_count'] = len(text_content)
                processed_data['_deduplication_applied'] = True
                
                logger.info("✅ Output strategy processing completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Output strategy processing failed: {e}")
                logger.info("🔄 Falling back to legacy processing")
                # Fall back to legacy processing
                processed_data = self._legacy_process_and_cache_data(data, cache_key)
        else:
            # Use legacy processing if no output strategy available
            logger.info("🔄 Using legacy text processing (no output strategy injected)")
            processed_data = self._legacy_process_and_cache_data(data, cache_key)
        
        # Cache the processed data
        self._processed_data_cache[cache_key] = processed_data
        
        # Limit cache size to prevent memory issues
        if len(self._processed_data_cache) > 100:
            # Remove oldest entries
            oldest_key = next(iter(self._processed_data_cache))
            del self._processed_data_cache[oldest_key]
            del self._speakers_cache[oldest_key]
            del self._text_content_cache[oldest_key]
        
        return processed_data
    
    def _legacy_process_and_cache_data(self, data: Dict[str, Any], cache_key: int) -> Dict[str, Any]:
        """Legacy data processing method (fallback when output strategy is not available)"""
        # Remove empty/whitespace-only segments using DataUtils helper
        try:
            cleaned_data = self.data_utils.clean_segments(data)
        except Exception as e:
            logger.warning(f"Segment cleanup skipped due to error: {e}")
            cleaned_data = data.copy()

        # Process and cache speakers data
        speakers = self.data_utils.extract_speakers_data(cleaned_data)
        self._speakers_cache[cache_key] = speakers
        
        # Process and cache text content
        if speakers:
            text_content = TextFormatter.format_conversation_text(speakers)
        else:
            text_content = self.data_utils.extract_text_content(cleaned_data)
        self._text_content_cache[cache_key] = text_content
        
        # Create processed data with all computed values
        processed_data = cleaned_data.copy()
        processed_data['_cached_speakers'] = speakers
        processed_data['_cached_text_content'] = text_content
        processed_data['_cached_word_count'] = len(text_content.split())
        processed_data['_cached_char_count'] = len(text_content)
        processed_data['_legacy_processing'] = True
        
        return processed_data
    
    def _create_output_directory(self, model: str, engine: str) -> str:
        """Create output directory with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"run_{timestamp}"
        
        # Create the main run directory
        run_dir = os.path.join(self.output_base_path, dir_name)
        os.makedirs(run_dir, exist_ok=True)
        
        # Create the specific transcription directory
        transcription_dir = os.path.join(run_dir, f"{timestamp}_{model}_{engine}_chunks")
        os.makedirs(transcription_dir, exist_ok=True)
        
        return transcription_dir
    
    def _process_data_legacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data using legacy method when no output strategy is available"""
        # Cache the processed data
        if '_legacy_processing' not in data:
            data['_legacy_processing'] = True
            
            # Extract speakers data
            if '_cached_speakers' not in data:
                data['_cached_speakers'] = self.data_utils.extract_speakers_data(data)
            
            # Extract text content
            if '_cached_text_content' not in data:
                data['_cached_text_content'] = self.data_utils.extract_text_content(data)
            
            # Cache word and character counts
            if '_cached_word_count' not in data:
                text_content = data.get('_cached_text_content', '')
                data['_cached_word_count'] = len(text_content.split()) if text_content else 0
            
            if '_cached_char_count' not in data:
                text_content = data.get('_cached_text_content', '')
                data['_cached_char_count'] = len(text_content) if text_content else 0
        
        return data

    def _save_json(self, data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Union[str, None]:
        """Save transcription as JSON"""
        try:
            filename = PathUtils.generate_output_filename(
                "transcription", model, engine, "json"
            )
            file_path = os.path.join(output_dir, filename)
            
            if JsonFormatter.save_json_file(data, file_path):
                logger.info(f"JSON saved: {file_path}")
                logger.info(f"   - JSON file size: {os.path.getsize(file_path)} bytes")
                if 'segments' in data:
                    logger.info(f"   - JSON segments count: {len(data['segments'])}")
                return file_path
            return None
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            return None
    
    def _save_text(self, data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Union[str, None]:
        """Save transcription as text file with speaker alignment"""
        try:
            from ..formatters.text_formatter import TextFormatter
            
            filename = PathUtils.generate_output_filename(
                "transcription", model, engine, "txt"
            )
            file_path = os.path.join(output_dir, filename)
            
            # Extract text content
            text_content = ""
            
            # Try to get processed text first
            if 'full_text' in data and data['full_text']:
                text_content = data['full_text']
                logger.info(f"Using processed full_text for text file")
            elif 'text' in data and data['text']:
                text_content = data['text']
                logger.info(f"Using basic text for text file")
            else:
                # Fallback to extracting from segments
                text_content = self.data_utils.extract_text_content(data)
                logger.info(f"Extracted text from segments for text file")
            
            # Format with speaker information if available and enabled
            # Extract speakers data using DataUtils to handle various formats
            speakers_data = self.data_utils.extract_speakers_data(data)

            # Determine if speakers should be included based on injected ConfigManager
            include_speakers = False
            if hasattr(self, 'config_manager') and self.config_manager:
                try:
                    # Prefer new 'speaker' section, then legacy
                    cfg = getattr(self.config_manager, 'config', None)
                    if cfg and hasattr(cfg, 'speaker') and cfg.speaker:
                        include_speakers = bool(getattr(cfg.speaker, 'enabled', True)) and not bool(getattr(cfg.speaker, 'disable_completely', False))
                    elif cfg and hasattr(cfg, 'speaker_diarization') and cfg.speaker_diarization:
                        include_speakers = bool(getattr(cfg.speaker_diarization, 'enabled', True)) and not bool(getattr(cfg.speaker_diarization, 'disable_completely', False))
                except Exception as e:
                    logger.debug(f"Could not check speaker configuration: {e}")
                    include_speakers = True

            if include_speakers and speakers_data:
                logger.info(f"Adding speaker information to text file")
                speaker_text = TextFormatter.format_conversation_text(speakers_data)
                if speaker_text:
                    text_content = f"=== SPEAKER ALIGNMENT ===\n\n{speaker_text}\n\n=== FULL TRANSCRIPTION ===\n\n{text_content}"
            else:
                if speakers_data and not include_speakers:
                    logger.info(f"Speaker diarization disabled - creating text file without speaker information")
                else:
                    logger.info(f"No speaker information available - creating basic text file")
                text_content = f"=== TRANSCRIPTION ===\n\n{text_content}"
            
            # Save text file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"Text file saved: {file_path}")
            logger.info(f"   - Text file size: {os.path.getsize(file_path)} bytes")
            logger.info(f"   - Text content length: {len(text_content)} characters")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving text file: {e}")
            return None
    
    def _save_docx(self, data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Union[str, None]:
        """Save transcription as DOCX file with speaker alignment"""
        try:
            from ..formatters.docx_formatter import DocxFormatter
            
            filename = PathUtils.generate_output_filename(
                "transcription", model, engine, "docx"
            )
            file_path = os.path.join(output_dir, filename)
            
            # Extract text content (same logic as text file)
            text_content = ""
            
            if 'full_text' in data and data['full_text']:
                text_content = data['full_text']
            elif 'text' in data and data['text']:
                text_content = data['text']
            else:
                text_content = self.data_utils.extract_text_content(data)
            
            # Format with speaker information if available and enabled
            # Extract speakers data using DataUtils to handle various formats
            speakers_data = self.data_utils.extract_speakers_data(data)

            # Determine if speakers should be included based on injected ConfigManager
            include_speakers = False
            if hasattr(self, 'config_manager') and self.config_manager:
                try:
                    cfg = getattr(self.config_manager, 'config', None)
                    if cfg and hasattr(cfg, 'speaker') and cfg.speaker:
                        include_speakers = bool(getattr(cfg.speaker, 'enabled', True)) and not bool(getattr(cfg.speaker, 'disable_completely', False))
                    elif cfg and hasattr(cfg, 'speaker_diarization') and cfg.speaker_diarization:
                        include_speakers = bool(getattr(cfg.speaker_diarization, 'enabled', True)) and not bool(getattr(cfg.speaker_diarization, 'disable_completely', False))
                except Exception as e:
                    logger.debug(f"Could not check speaker configuration: {e}")
                    include_speakers = True

            if include_speakers and speakers_data:
                from ..formatters.text_formatter import TextFormatter
                speaker_text = TextFormatter.format_conversation_text(speakers_data)
                if speaker_text:
                    text_content = f"=== SPEAKER ALIGNMENT ===\n\n{speaker_text}\n\n=== FULL TRANSCRIPTION ===\n\n{text_content}"
            else:
                if speakers_data and not include_speakers:
                    logger.info(f"No speaker information available - creating DOCX without speaker information")
                else:
                    logger.info(f"No speaker information available - creating basic DOCX")
                text_content = f"=== TRANSCRIPTION ===\n\n{text_content}"
            
            # Create DOCX from the text content
            if DocxFormatter.create_docx_from_text_content(text_content, file_path, model, engine):
                logger.info(f"DOCX file saved: {file_path}")
                logger.info(f"   - DOCX file size: {os.path.getsize(file_path)} bytes")
                return file_path
            return None
            
        except Exception as e:
            logger.error(f"Error saving DOCX file: {e}")
            return None
    

    

    
    def clear_cache(self):
        """Clear all cached data to free memory"""
        self._processed_data_cache.clear()
        self._speakers_cache.clear()
        self._text_content_cache.clear()
        logger.info("Output manager cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'processed_data_cache_size': len(self._processed_data_cache),
            'speakers_cache_size': len(self._speakers_cache),
            'text_content_cache_size': len(self._text_content_cache),
            'total_cache_entries': len(self._processed_data_cache)
        }
    
    def _create_text_from_processed_data(self, processed_data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Union[str, None]:
        """Create text file from processed data using output strategy"""
        try:
            # Use the output strategy to create text content
            if hasattr(self.output_strategy, 'create_text_output'):
                text_content = self.output_strategy.create_text_output(processed_data)
            else:
                # Fallback: extract text from processed data
                text_content = processed_data.get('full_text', '') or processed_data.get('text', '')
            
            if not text_content:
                logger.warning("No text content available for text file creation")
                return None
            
            # Generate filename
            filename = PathUtils.generate_output_filename("transcription", model, engine, "txt")
            file_path = os.path.join(output_dir, filename)
            
            # Save text file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"Text file created from processed data: {file_path}")
            logger.info(f"   - Text file size: {os.path.getsize(file_path)} bytes")
            logger.info(f"   - Text content length: {len(text_content)} characters")
            return file_path
            
        except Exception as e:
            logger.error(f"Error creating text file from processed data: {e}")
            return None
    
    def _create_docx_from_text_file(self, text_file_path: str, output_dir: str, model: str, engine: str) -> Union[str, None]:
        """Create DOCX file from text file using DocxFormatter"""
        try:
            from ..formatters.docx_formatter import DocxFormatter
            
            # Generate DOCX filename
            filename = PathUtils.generate_output_filename("transcription", model, engine, "docx")
            file_path = os.path.join(output_dir, filename)
            
            # Use DocxFormatter to create DOCX from text file
            success = DocxFormatter.create_docx_from_word_ready_text(
                text_file_path=text_file_path,
                output_docx_path=file_path,
                audio_file=model,
                model=model,
                engine=engine
            )
            
            if success:
                logger.info(f"DOCX created successfully from text file: {file_path}")
                logger.info(f"   - DOCX file size: {os.path.getsize(file_path)} bytes")
                logger.info(f"   - Source text file: {os.path.basename(text_file_path)}")
                return file_path
            else:
                logger.error("Failed to create DOCX from text file")
                return None
                
        except Exception as e:
            logger.error(f"Error creating DOCX from text file: {e}")
            return None 