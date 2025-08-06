"""
Output saver implementations
"""

from typing import Dict, Any, List, Optional
from .interfaces import OutputSaverInterface


class DefaultOutputSaver(OutputSaverInterface):
    """Default implementation of output saver"""
    
    def __init__(self, data_utils: Optional['DataUtils'] = None):
        """
        Initialize output saver with dependency injection
        
        Args:
            data_utils: DataUtils instance for data processing
        """
        from src.output_data.utils.data_utils import DataUtils
        self.data_utils = data_utils or DataUtils()
    
    def save(self, audio_file_path: str, segments: List[Dict[str, Any]], 
             model: str, engine: str) -> Dict[str, str]:
        """Save transcription outputs in multiple formats"""
        try:
            from src.output_data.managers.output_manager import OutputManager
            
            output_manager = OutputManager(data_utils=self.data_utils)
            
            # Save all formats using the unified method
            saved_files = output_manager.save_transcription(
                transcription_data=segments,
                audio_file=audio_file_path,
                model=model,
                engine=engine
            )
            
            return saved_files
            
        except Exception as e:
            raise RuntimeError(f"Failed to save outputs: {e}") 