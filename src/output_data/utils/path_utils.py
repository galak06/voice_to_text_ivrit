#!/usr/bin/env python3
"""
Path Utilities
Handles file path operations and sanitization
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class PathUtils:
    """Path utility functions"""
    
    @staticmethod
    def sanitize_model_name(model_name: str) -> str:
        """Sanitize model name for use in file paths"""
        if not model_name:
            return "unknown_model"
        
        # Replace problematic characters
        sanitized = model_name.replace('/', '_').replace('\\', '_')
        sanitized = re.sub(r'[<>:"|?*]', '_', sanitized)
        
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        return sanitized or "unknown_model"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for use in file paths"""
        if not filename:
            return "unknown_file"
        
        # Remove file extension
        filename = Path(filename).stem
        
        # Replace problematic characters
        sanitized = filename.replace('/', '_').replace('\\', '_')
        sanitized = re.sub(r'[<>:"|?*]', '_', sanitized)
        
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Limit length to avoid path issues
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized or "unknown_file"
    
    @staticmethod
    def create_output_directory(base_path: str, model: str, engine: str) -> str:
        """Create output directory for transcription results"""
        model_safe = PathUtils.sanitize_model_name(model)
        engine_safe = PathUtils.sanitize_model_name(engine)
        
        # Create directory path
        output_dir = os.path.join(base_path, f"transcription_{model_safe}_{engine_safe}")
        
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    @staticmethod
    def generate_output_filename(
        base_name: str,
        model: str,
        engine: str,
        extension: str
    ) -> str:
        """Generate output filename with model and engine info"""
        model_safe = PathUtils.sanitize_model_name(model)
        engine_safe = PathUtils.sanitize_model_name(engine)
        
        # Remove extension from base name if present
        base_name = Path(base_name).stem
        
        return f"transcription_{model_safe}_{engine_safe}.{extension}"
    
    @staticmethod
    def ensure_directory_exists(path: str) -> bool:
        """Ensure directory exists, create if it doesn't"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return False
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension from path"""
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def is_valid_file_path(file_path: str) -> bool:
        """Check if file path is valid"""
        try:
            Path(file_path)
            return True
        except Exception:
            return False 