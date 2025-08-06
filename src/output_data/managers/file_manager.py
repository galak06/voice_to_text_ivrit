#!/usr/bin/env python3
"""
File Manager
Handles file operations and directory management
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManager:
    """File management utilities"""
    
    @staticmethod
    def create_output_directory(base_path: str, model: str, engine: str, session_id: Optional[str] = None) -> str:
        """Create timestamped output directory"""
        from ..utils.path_utils import PathUtils
        
        # Use provided session_id or create new timestamp
        if session_id:
            timestamp = session_id
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        model_safe = PathUtils.sanitize_model_name(model)
        engine_safe = PathUtils.sanitize_model_name(engine)
        
        # Create directory path
        output_dir = os.path.join(
            base_path,
            f"run_{timestamp}",
            f"{timestamp}_{PathUtils.sanitize_model_name(model)}"
        )
        
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    @staticmethod
    def save_file(content: str, file_path: str, encoding: str = 'utf-8') -> bool:
        """Save content to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {e}")
            return False
    
    @staticmethod
    def copy_file(source: str, destination: str) -> bool:
        """Copy file from source to destination"""
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logger.error(f"Error copying file from {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def list_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
        """List files in directory with optional extension filter"""
        try:
            if not os.path.exists(directory):
                return []
            
            files = []
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    if extensions:
                        if any(file.lower().endswith(ext.lower()) for ext in extensions):
                            files.append(file_path)
                    else:
                        files.append(file_path)
            
            return sorted(files)
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            return []
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str) -> bool:
        """Clean up temporary files and directory"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return True
        except Exception as e:
            logger.error(f"Error cleaning up temp directory {temp_dir}: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists"""
        return os.path.isfile(file_path) 