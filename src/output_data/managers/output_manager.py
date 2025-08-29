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
                        logger.info(f"   - Segment {i}: {seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s, text: '{seg.get('text', '')[:50]}...'")
                    
                    processed_text = self.output_strategy.create_final_output(segments)
                    deduplicated_segments = self.output_strategy.create_segmented_output(segments)
                    
                    # Log overlapping detection results
                    original_chars = sum(len(seg.get('text', '')) for seg in segments)
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
            
            if results:
                logger.info(f"✅ Saved {len(results)} output files to {output_dir}")
                logger.info(f"   - Files: {list(results.keys())}")
                if use_processed_text:
                    logger.info("   - Using processed text only - no duplicate text files created")
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