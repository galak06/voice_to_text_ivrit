"""
Output saver implementations
"""

from typing import Dict, Any, List


class DefaultOutputSaver:
    """Default implementation of output saver"""
    
    def save(self, audio_file_path: str, segments: List[Dict[str, Any]], 
             model: str, engine: str) -> Dict[str, str]:
        """Save transcription outputs in multiple formats"""
        try:
            from src.output_data import OutputManager
            
            output_manager = OutputManager()
            
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