"""
Output Saver Interface
Defines the contract for saving transcription outputs
"""

from typing import Dict, Any, List, Protocol


class OutputSaverInterface(Protocol):
    """Protocol for saving transcription outputs"""
    
    def save(self, audio_file_path: str, segments: List[Dict[str, Any]], 
             model: str, engine: str) -> Dict[str, str]:
        """
        Save transcription outputs in multiple formats
        
        Args:
            audio_file_path: Path to the audio file
            segments: List of transcription segments
            model: Model used for transcription
            engine: Engine used for transcription
            
        Returns:
            Dictionary mapping format names to saved file paths
        """
        ... 