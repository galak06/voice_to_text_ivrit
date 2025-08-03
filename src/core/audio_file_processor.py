#!/usr/bin/env python3
"""
Audio file processor
Handles audio file preparation and processing
"""

import base64
import tempfile
from typing import Dict, Any, Optional, Tuple
from src.utils.file_downloader import FileDownloader

class AudioFileProcessor:
    """Handles audio file preparation and processing"""
    
    def __init__(self, max_payload_size: int = 200 * 1024 * 1024):
        """Initialize processor with size limit"""
        self.max_payload_size = max_payload_size
        self.downloader = FileDownloader(max_payload_size)
    
    def prepare_audio_file(self, job: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Prepare audio file from job input following Single Responsibility Principle.
        
        Args:
            job: The job dictionary containing input parameters
            
        Returns:
            Tuple of (temp_directory, audio_file_path) or (None, error_message)
        """
        datatype = job['input'].get('type')
        api_key = job['input'].get('api_key', None)
        
        temp_dir = tempfile.mkdtemp()
        audio_file = f'{temp_dir}/audio.mp3'
        
        if datatype == 'blob':
            try:
                mp3_bytes = base64.b64decode(job['input']['data'])
                with open(audio_file, 'wb') as f:
                    f.write(mp3_bytes)
            except Exception as e:
                return None, f"Error decoding blob data: {e}"
        elif datatype == 'url':
            success = self.downloader.download_file(job['input']['url'], audio_file, api_key)
            if not success:
                return None, f"Error downloading data from {job['input']['url']}"
        elif datatype == 'file':
            try:
                import shutil
                source_file = job['input']['data']
                # Copy the file to temp directory with .mp3 extension
                shutil.copy2(source_file, audio_file)
            except Exception as e:
                return None, f"Error copying file {job['input']['data']}: {e}"
        else:
            return None, f"Unsupported datatype: {datatype}"
        
        return temp_dir, audio_file
    
    def cleanup_temp_files(self, temp_dir: str) -> None:
        """
        Clean up temporary files
        
        Args:
            temp_dir: Directory to clean up
        """
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            # Silently handle cleanup errors in production
            pass
    
    def get_audio_file_info(self, audio_file: str) -> Dict[str, Any]:
        """
        Get information about an audio file
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Dictionary with file information
        """
        from pathlib import Path
        
        file_path = Path(audio_file)
        if not file_path.exists():
            return {"error": "File not found"}
        
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "modified": stat.st_mtime,
            "extension": file_path.suffix
        } 