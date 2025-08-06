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
            # Convert dataclass to dict if needed
            data_dict = self.data_utils.convert_transcription_result_to_dict(transcription_data)
            
            # Extract file path
            input_file_path = self.data_utils.get_audio_file(data_dict) or audio_file
            
            # Create output directory
            output_dir = FileManager.create_output_directory(
                self.output_base_path, model, engine, session_id
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
            logger.info(f"Saved {len(saved_files)} output files to {output_dir}")
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
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
                return file_path
            return None
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            return None
    
    def _save_text(self, data: Dict[str, Any], output_dir: str, model: str, engine: str) -> Optional[str]:
        """Save transcription as text"""
        try:
            # Extract and format text
            speakers = self.data_utils.extract_speakers_data(data)
            if speakers:
                text_content = TextFormatter.format_conversation_text(speakers)
            else:
                text_content = self.data_utils.extract_text_content(data)
            
            # Improve Hebrew punctuation
            text_content = TextFormatter.improve_hebrew_punctuation(text_content)
            
            filename = PathUtils.generate_output_filename(
                "transcription", model, engine, "txt"
            )
            file_path = os.path.join(output_dir, filename)
            
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
                return file_path
            
            return None
        except Exception as e:
            logger.error(f"Error saving DOCX: {e}")
            return None 