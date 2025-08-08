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
    """Main output manager for transcription results"""
    
    def __init__(self, output_base_path: str = "output/transcriptions", data_utils: Optional[DataUtils] = None):
        """Initialize output manager with dependency injection"""
        self.output_base_path = output_base_path
        self.data_utils = data_utils or DataUtils()
        
        # Ensure base output directory exists
        os.makedirs(output_base_path, exist_ok=True)
    
    def save_transcription(
        self,
        transcription_data: Any,
        audio_file: str,
        model: str,
        engine: str,
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
            
            # Log input data structure
            logger.info(f"   - Input data type: {type(transcription_data)}")
            logger.info(f"   - Converted data keys: {list(data_dict.keys())}")
            
            # Extract file path
            input_file_path = self.data_utils.get_audio_file(data_dict) or audio_file
            
            # Create output directory
            output_dir = FileManager.create_output_directory(
                self.output_base_path, model, engine, session_id, audio_file
            )
            
            # Save in different formats
            saved_files = {}
            
            # Save JSON
            json_file = self._save_json(data_dict, output_dir, model, engine)
            if json_file:
                saved_files['json'] = json_file
            
            # Save TXT
            txt_file = self._save_text(data_dict, output_dir, model, engine)
            if txt_file:
                saved_files['txt'] = txt_file
            
            # Save DOCX
            docx_file = self._save_docx(data_dict, output_dir, model, engine)
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
        """Save transcription as text"""
        try:
            # Log input data for text saving
            logger.info(f"📝 SAVING TEXT FORMAT:")
            logger.info(f"   - Input data keys: {list(data.keys())}")
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
        """Save transcription as DOCX"""
        try:
            # Log input data for DOCX saving
            logger.info(f"📄 SAVING DOCX FORMAT:")
            logger.info(f"   - Input data keys: {list(data.keys())}")
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