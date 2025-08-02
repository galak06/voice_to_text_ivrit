#!/usr/bin/env python3
"""
Output manager utility
Handles file outputs, logging, and temporary file management
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

try:
    from docx import Document
    from docx.shared import Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class OutputManager:
    """Manages output files, logs, and temporary files"""
    
    def __init__(self, base_output_dir: str = None, run_session_id: str = None):
        """Initialize output manager with base directory"""
        from src.utils.config_manager import config
        
        if base_output_dir is None:
            base_output_dir = config.output.output_dir
        
        self.base_output_dir = Path(base_output_dir)
        self.logs_dir = self.base_output_dir / "logs"
        self.transcriptions_dir = self.base_output_dir / "transcriptions"
        self.temp_dir = self.base_output_dir / "temp"
        
        # Generate run session ID if not provided
        if run_session_id is None:
            self.run_session_id = self._generate_run_session_id()
        else:
            self.run_session_id = run_session_id
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Setup logging
        self._setup_logging()
    
    def _generate_run_session_id(self) -> str:
        """Generate a unique run session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"run_{timestamp}"
    
    def get_run_session_dir(self) -> Path:
        """Get the run session directory"""
        return self.transcriptions_dir / self.run_session_id
    
    def _ensure_directories(self):
        """Ensure all output directories exist"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.transcriptions_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        from src.utils.config_manager import config
        
        log_file = self.logs_dir / f"transcription_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, config.output.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ivrit-ai')
    
    def save_transcription(self, audio_file: str, transcription_data: Any, 
                          model: str = "unknown", engine: str = "unknown") -> str:
        """
        Save transcription results to file
        
        Args:
            audio_file: Original audio file path
            transcription_data: Transcription results
            model: Model used for transcription
            engine: Engine used for transcription
            
        Returns:
            Path to saved transcription file
        """
        # Create run session directory
        run_session_dir = self.get_run_session_dir()
        run_session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped folder for this transcription session
        audio_name = Path(audio_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = f"{timestamp}_{audio_name}"
        session_dir = run_session_dir / session_folder
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"transcription_{model}_{engine}.json"
        output_file = session_dir / filename
        
        # Prepare output data
        output_data = {
            "metadata": {
                "audio_file": audio_file,
                "model": model,
                "engine": engine,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "transcription": transcription_data
        }
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Transcription saved to: {output_file}")
        return str(output_file)
    
    def save_transcription_text(self, audio_file: str, text: str, 
                               model: str = "unknown", engine: str = "unknown") -> str:
        """
        Save transcription as plain text
        
        Args:
            audio_file: Original audio file path
            text: Transcription text
            model: Model used for transcription
            engine: Engine used for transcription
            
        Returns:
            Path to saved text file
        """
        # Create run session directory
        run_session_dir = self.get_run_session_dir()
        run_session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped folder for this transcription session
        audio_name = Path(audio_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = f"{timestamp}_{audio_name}"
        session_dir = run_session_dir / session_folder
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"transcription_{model}_{engine}.txt"
        output_file = session_dir / filename
        
        # Prepare text content
        content = f"Transcription of: {audio_file}\n"
        content += f"Model: {model}\n"
        content += f"Engine: {engine}\n"
        content += f"Timestamp: {datetime.now().isoformat()}\n"
        content += "=" * 60 + "\n\n"
        content += text
        
        # Save to text file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Transcription text saved to: {output_file}")
        return str(output_file)
    
    def save_transcription_docx(self, audio_file: str, transcription_data: List[Dict[str, Any]], 
                               model: str = "unknown", engine: str = "unknown") -> Optional[str]:
        """
        Save transcription as Word document (.docx)
        
        Args:
            audio_file: Original audio file path
            transcription_data: List of transcription segments
            model: Model used for transcription
            engine: Engine used for transcription
            
        Returns:
            Path to saved Word document, or None if python-docx not available
        """
        if not DOCX_AVAILABLE:
            self.logger.warning("python-docx not available. Skipping Word document creation.")
            return None
        
        # Create run session directory
        run_session_dir = self.get_run_session_dir()
        run_session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped folder for this transcription session
        audio_name = Path(audio_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = f"{timestamp}_{audio_name}"
        session_dir = run_session_dir / session_folder
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"transcription_{model}_{engine}.docx"
        output_file = session_dir / filename
        
        # Create Word document
        doc = Document()
        
        # Add title
        title = doc.add_heading('Transcription Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add metadata
        doc.add_heading('Metadata', level=1)
        metadata_table = doc.add_table(rows=4, cols=2)
        metadata_table.style = 'Table Grid'
        
        metadata_cells = [
            ('Audio File:', audio_file),
            ('Model:', model),
            ('Engine:', engine),
            ('Timestamp:', datetime.now().isoformat())
        ]
        
        for i, (key, value) in enumerate(metadata_cells):
            metadata_table.cell(i, 0).text = key
            metadata_table.cell(i, 1).text = str(value)
        
        doc.add_paragraph()  # Add spacing
        
        # Add transcription content
        doc.add_heading('Conversation Transcript', level=1)
        
        # Group segments by speaker
        speakers = {}
        for segment in transcription_data:
            speaker = segment.get('speaker', 'Unknown Speaker')
            if speaker not in speakers:
                speakers[speaker] = []
            speakers[speaker].append(segment)
        
        # Sort speakers by their first appearance
        speaker_order = []
        for segment in transcription_data:
            speaker = segment.get('speaker', 'Unknown Speaker')
            if speaker not in speaker_order:
                speaker_order.append(speaker)
        
        # Create conversation format
        for speaker in speaker_order:
            if speaker in speakers:
                speaker_segments = speakers[speaker]
                
                # Combine all text from this speaker
                speaker_text = ""
                for segment in speaker_segments:
                    text = segment.get('text', '').strip()
                    if text:
                        speaker_text += text + " "
                
                if speaker_text.strip():
                    # Add speaker label and text in conversation format
                    speaker_para = doc.add_paragraph()
                    speaker_para.add_run(f"{speaker}: ").bold = True
                    speaker_para.add_run(speaker_text.strip())
                    doc.add_paragraph()  # Add spacing between speakers
        
        # Save document
        doc.save(str(output_file))
        self.logger.info(f"Transcription Word document saved to: {output_file}")
        return str(output_file)
    
    def get_temp_file(self, prefix: str = "temp", suffix: str = ".tmp") -> str:
        """
        Get a temporary file path
        
        Args:
            prefix: File prefix
            suffix: File suffix
            
        Returns:
            Path to temporary file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}{suffix}"
        return str(self.temp_dir / filename)
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up temporary files older than specified hours
        
        Args:
            older_than_hours: Age threshold in hours
        """
        import time
        current_time = time.time()
        threshold = current_time - (older_than_hours * 3600)
        
        cleaned_count = 0
        for temp_file in self.temp_dir.glob("*"):
            if temp_file.is_file() and temp_file.stat().st_mtime < threshold:
                temp_file.unlink()
                cleaned_count += 1
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} temporary files")
    
    def get_output_stats(self) -> Dict[str, Any]:
        """
        Get statistics about output files
        
        Returns:
            Dictionary with output statistics
        """
        # Count run sessions (parent folders)
        run_sessions = [d for d in self.transcriptions_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        
        # Count transcription sessions (subfolders within run sessions)
        transcription_sessions = []
        json_files = []
        txt_files = []
        docx_files = []
        
        for run_session_dir in run_sessions:
            # Count subfolders within this run session
            subfolders = [d for d in run_session_dir.iterdir() if d.is_dir()]
            transcription_sessions.extend(subfolders)
            
            # Count files in all subfolders
            for subfolder in subfolders:
                json_files.extend(subfolder.glob("*.json"))
                txt_files.extend(subfolder.glob("*.txt"))
                docx_files.extend(subfolder.glob("*.docx"))
        
        stats = {
            "logs": {
                "count": len(list(self.logs_dir.glob("*.log"))),
                "size_mb": sum(f.stat().st_size for f in self.logs_dir.glob("*.log")) / (1024 * 1024)
            },
            "transcriptions": {
                "run_sessions": len(run_sessions),
                "sessions": len(transcription_sessions),
                "json_files": len(json_files),
                "txt_files": len(txt_files),
                "docx_files": len(docx_files),
                "total_files": len(json_files) + len(txt_files) + len(docx_files),
                "size_mb": sum(f.stat().st_size for f in json_files + txt_files + docx_files) / (1024 * 1024)
            },
            "temp_files": {
                "count": len(list(self.temp_dir.glob("*"))),
                "size_mb": sum(f.stat().st_size for f in self.temp_dir.glob("*")) / (1024 * 1024)
            }
        }
        
        return stats
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message) 