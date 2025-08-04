#!/usr/bin/env python3
"""
JSON Formatter Class
Handles JSON formatting utilities for output data
"""

import json
import logging
from typing import Any

from .json_encoder import CustomJSONEncoder

logger = logging.getLogger(__name__)

class JsonFormatter:
    """JSON formatting utilities"""
    
    @staticmethod
    def format_transcription_data(data: Any) -> str:
        """Format transcription data as JSON string"""
        return json.dumps(data, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)
    
    @staticmethod
    def save_json_file(data: Any, file_path: str) -> bool:
        """Save data as JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")
            return False 