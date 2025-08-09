#!/usr/bin/env python3
"""
Output Manager
Main orchestrator for all output operations
"""

import os
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..formatters.json_formatter import JsonFormatter, CustomJSONEncoder
from ..formatters.text_formatter import TextFormatter
from ..formatters.docx_formatter import DocxFormatter
from ..utils.path_utils import PathUtils
from ..utils.data_utils import DataUtils
from .file_manager import FileManager

logger = logging.getLogger(__name__)

class OutputManager:
    """Main output manager for transcription results with caching"""
    
    def __init__(self, output_base_path: str = "output/transcriptions", data_utils: Optional[DataUtils] = None):
        """Initialize output manager with dependency injection and caching"""
        self.output_base_path = output_base_path
        self.data_utils = data_utils or DataUtils()
        
        # Cache for processed data to avoid duplicate processing
        self._processed_data_cache = {}
        self._speakers_cache = {}
        self._text_content_cache = {}
        
        # Ensure base output directory exists
        os.makedirs(output_base_path, exist_ok=True)
    
    def save_transcription(
        self,
        transcription_data: Any,
        audio_file: str,
        model: Optional[str] = None,
        engine: Optional[str] = None,
        input_metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Save transcription in all formats"""
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
            # Avoid strict type issues by extracting engine from dict directly
            engine_final = engine or data_dict.get('engine') or data_dict.get('engine_name') or "unknown-engine"
            
            # Log input data structure
            logger.info(f"   - Input data type: {type(transcription_data)}")
            logger.info(f"   - Converted data keys: {list(data_dict.keys())}")
            
            # Extract file path
            input_file_path = self.data_utils.get_audio_file(data_dict) or audio_file
            
            # Create output directory
            output_dir = FileManager.create_output_directory(
                self.output_base_path, model_final, engine_final, session_id, audio_file
            )
            
            # Process data once and cache results
            processed_data = self._process_and_cache_data(data_dict)
            
            # Save in different formats using cached data
            saved_files = {}
            
            # Save JSON
            json_file = self._save_json(processed_data, output_dir, model_final, engine_final)
            if json_file:
                saved_files['json'] = json_file
            
            # Save TXT
            txt_file = self._save_text(processed_data, output_dir, model_final, engine_final)
            if txt_file:
                saved_files['txt'] = txt_file
            
            # Save DOCX
            docx_file = self._save_docx(processed_data, output_dir, model_final, engine_final)
            if docx_file:
                saved_files['docx'] = docx_file
            
            # Log success
            logger.info(f"✅ Saved {len(saved_files)} output files to {output_dir}")
            logger.info(f"   - Files: {list(saved_files.keys())}")
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
            import traceback
            logger.error(f"Error details: {traceback.format_exc()}")
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

    def save_text(self, text: str, base_filename: str) -> Dict[str, Any]:
        """Save a text file to the base output directory.
        Returns a dict with success and file_path for compatibility with tests."""
        try:
            os.makedirs(self.output_base_path, exist_ok=True)
            file_path = os.path.join(self.output_base_path, f"{base_filename}.txt")
            if FileManager.save_file(text, file_path):
                return {'success': True, 'file_path': file_path}
            return {'success': False}
        except Exception as e:
            logger.error(f"Error in save_text: {e}")
            return {'success': False}
    
    def _process_and_cache_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data once and cache results for reuse"""
        # Create a cache key based on data content
        cache_key = hash(str(sorted(data.items())))
        
        if cache_key in self._processed_data_cache:
            logger.info("Using cached processed data")
            return self._processed_data_cache[cache_key]
        
        # Remove empty/whitespace-only segments before any processing
        cleaned_data = data.copy()
        try:
            if isinstance(cleaned_data.get('segments'), list):
                original_count = len(cleaned_data['segments'])
                cleaned_segments = [
                    seg for seg in cleaned_data['segments']
                    if isinstance(seg, dict) and isinstance(seg.get('text', ''), str) and seg.get('text', '').strip()
                ]
                if len(cleaned_segments) != original_count:
                    logger.info(
                        f"🧹 Filtered empty segments: kept {len(cleaned_segments)} of {original_count}"
                    )
                cleaned_data['segments'] = cleaned_segments

            if isinstance(cleaned_data.get('speakers'), dict):
                total_before = sum(len(v) for v in cleaned_data['speakers'].values() if isinstance(v, list))
                new_speakers = {}
                for speaker_name, segs in cleaned_data['speakers'].items():
                    if isinstance(segs, list):
                        filtered = [
                            seg for seg in segs
                            if isinstance(seg, dict) and isinstance(seg.get('text', ''), str) and seg.get('text', '').strip()
                        ]
                        if filtered:
                            new_speakers[speaker_name] = filtered
                total_after = sum(len(v) for v in new_speakers.values())
                if total_after != total_before:
                    logger.info(
                        f"🧹 Filtered empty speaker segments: kept {total_after} of {total_before}"
                    )
                if new_speakers:
                    cleaned_data['speakers'] = new_speakers
                else:
                    cleaned_data.pop('speakers', None)
        except Exception as e:
            logger.warning(f"Segment cleanup skipped due to error: {e}")

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
    
    def _save_json(self, data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Optional[str]:
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
    
    def _save_text(self, data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Optional[str]:
        """Save transcription as text using cached data"""
        try:
            # Log input data for text saving
            logger.info(f"📝 SAVING TEXT FORMAT:")
            logger.info(f"   - Input data keys: {list(data.keys())}")
            
            # Use cached data if available
            if '_cached_speakers' in data:
                speakers = data['_cached_speakers']
                text_content = data['_cached_text_content']
                logger.info(f"   - Using cached text content")
            else:
                # Fallback to processing if not cached
                if 'segments' in data:
                    logger.info(f"   - Input segments count: {len(data['segments'])}")
                    total_text_length = sum(len(seg.get('text', '')) for seg in data['segments'])
                    total_words = sum(len(seg.get('text', '').split()) for seg in data['segments'])
                    logger.info(f"   - Input total text length: {total_text_length} characters")
                    logger.info(f"   - Input total word count: {total_words} words")
                
                # Extract and format text
                speakers = self.data_utils.extract_speakers_data(data)
                if speakers:
                    logger.info(f"   - Extracted speakers: {list(speakers.keys())}")
                    for speaker, segments in speakers.items():
                        speaker_words = sum(len(seg.get('text', '').split()) for seg in segments)
                        logger.info(f"   - {speaker}: {len(segments)} segments, {speaker_words} words")
                    text_content = TextFormatter.format_conversation_text(speakers)
                else:
                    logger.info(f"   - No speakers data extracted, using fallback")
                    text_content = self.data_utils.extract_text_content(data)
            
            filename = PathUtils.generate_output_filename(
                "transcription", model, engine, "txt"
            )
            file_path = os.path.join(output_dir, filename)
            
            # Log text content before saving
            final_word_count = len(text_content.split())
            logger.info(f"   - Final text content length: {len(text_content)} characters")
            logger.info(f"   - Final text word count: {final_word_count} words")
            logger.info(f"   - Text content lines: {text_content.count(chr(10)) + 1}")
            logger.info(f"   - Text file path: {file_path}")
            
            if FileManager.save_file(text_content, file_path):
                logger.info(f"Text saved: {file_path}")
                return file_path
            return None
        except Exception as e:
            logger.error(f"Error saving text: {e}")
            return None
    
    def _save_docx(self, data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Optional[str]:
        """Save transcription as DOCX using cached data"""
        try:
            # Log input data for DOCX saving
            logger.info(f"📄 SAVING DOCX FORMAT:")
            logger.info(f"   - Input data keys: {list(data.keys())}")
            
            # Use cached data if available
            if '_cached_speakers' in data:
                speakers = data['_cached_speakers']
                logger.info(f"   - Using cached speakers data")
            else:
                # Fallback to processing if not cached
                if 'segments' in data:
                    logger.info(f"   - Input segments count: {len(data['segments'])}")
                    total_text_length = sum(len(seg.get('text', '')) for seg in data['segments'])
                    total_words = sum(len(seg.get('text', '').split()) for seg in data['segments'])
                    logger.info(f"   - Input total text length: {total_text_length} characters")
                    logger.info(f"   - Input total word count: {total_words} words")
                
                # Convert data to DOCX format
                speakers = self.data_utils.extract_speakers_data(data)
            
            docx_data = []
            
            for speaker_name, segments in speakers.items():
                for segment in segments:
                    if isinstance(segment, dict) and 'text' in segment:
                        docx_data.append({
                            'speaker': speaker_name,
                            'text': segment['text'],
                            'start': segment.get('start', 0),
                            'end': segment.get('end', 0)
                        })
            
            # Log DOCX data preparation
            logger.info(f"   - DOCX data segments: {len(docx_data)}")
            if docx_data:
                total_docx_text = sum(len(seg['text']) for seg in docx_data)
                total_docx_words = sum(len(seg['text'].split()) for seg in docx_data)
                logger.info(f"   - DOCX total text length: {total_docx_text} characters")
                logger.info(f"   - DOCX total word count: {total_docx_words} words")
                logger.info(f"   - First DOCX segment: {docx_data[0]['start']:.1f}s - {docx_data[0]['end']:.1f}s")
                logger.info(f"   - Last DOCX segment: {docx_data[-1]['start']:.1f}s - {docx_data[-1]['end']:.1f}s")
            
            # Create document
            doc = DocxFormatter.create_transcription_document(
                docx_data, 
                self.data_utils.get_audio_file(data),
                self.data_utils.get_model_name(data),
                engine
            )
            
            if doc:
                filename = PathUtils.generate_output_filename(
                    "transcription", model, engine, "docx"
                )
                file_path = os.path.join(output_dir, filename)
                
                doc.save(file_path)
                logger.info(f"DOCX saved: {file_path}")
                logger.info(f"   - DOCX file size: {os.path.getsize(file_path)} bytes")
                return file_path
            
            return None
        except Exception as e:
            logger.error(f"Error saving DOCX: {e}")
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