"""
Output saver implementations
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path
from src.core.interfaces import OutputSaverInterface

if TYPE_CHECKING:
    from src.output_data.utils.data_utils import DataUtils


class OutputSaver(OutputSaverInterface):
    """Default implementation of output saver"""
    
    def __init__(self, data_utils: Optional['DataUtils'] = None):
        """
        Initialize output saver with dependency injection
        
        Args:
            data_utils: DataUtils instance for data processing
        """
        from src.output_data.utils.data_utils import DataUtils
        self.data_utils = data_utils or DataUtils()
    
    def save_text(self, output_path: Path, text_content: str) -> Path:
        """Save text content to file"""
        output_path.write_text(text_content, encoding='utf-8')
        return output_path
    
    def save_json(self, output_path: Path, data: Dict[str, Any]) -> Path:
        """Save data as JSON file"""
        import json
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return output_path
    
    def create_output_directory(self, base_path: Path, filename: str) -> Path:
        """Create output directory for saving files"""
        output_dir = base_path / filename
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
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
