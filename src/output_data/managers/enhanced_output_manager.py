#!/usr/bin/env python3
"""
Enhanced Output Manager
Improved output management following SOLID principles and clean code rules
"""

import os
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

from ..formatters.json_formatter_class import JsonFormatter
from ..formatters.text_formatter import TextFormatter
from ..formatters.docx_formatter import DocxFormatter
from ..utils.path_utils import PathUtils
from ..utils.data_utils import DataUtils
from .file_manager import FileManager

logger = logging.getLogger(__name__)


class OutputFormatterInterface(ABC):
    """Interface for output formatters following Interface Segregation Principle"""
    
    @abstractmethod
    def format_and_save(self, data: Any, output_dir: str, filename: str) -> Optional[str]:
        """Format and save data, return file path if successful"""
        pass


class JsonOutputFormatter(OutputFormatterInterface):
    """JSON output formatter following Single Responsibility Principle"""
    
    def format_and_save(self, data: Any, output_dir: str, filename: str) -> Optional[str]:
        """Format and save as enhanced JSON"""
        try:
            filepath = os.path.join(output_dir, filename)
            if JsonFormatter.save_json_file(data, filepath):
                logger.info(f"✅ Enhanced JSON saved: {filepath}")
                return filepath
            return None
        except Exception as e:
            logger.error(f"❌ Error saving enhanced JSON: {e}")
            return None


class TextOutputFormatter(OutputFormatterInterface):
    """Text output formatter following Single Responsibility Principle"""
    
    def format_and_save(self, data: Any, output_dir: str, filename: str) -> Optional[str]:
        """Format and save as conversation text"""
        try:
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._create_conversation_text(data))
            
            logger.info(f"✅ Conversation text saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error saving conversation text: {e}")
            return None
    
    def _create_conversation_text(self, data: Any) -> str:
        """Create conversation text format following Single Responsibility Principle"""
        lines = [
            "CONVERSATION TRANSCRIPTION",
            f"Generated: {datetime.now().
