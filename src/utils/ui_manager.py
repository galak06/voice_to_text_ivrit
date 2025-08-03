#!/usr/bin/env python3
"""
UI Manager for the Voice-to-Text Transcription Application
Provides clean, organized, and readable output formatting
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.application import TranscriptionApplication


class ApplicationUI:
    """Clean and organized UI for the transcription application"""
    
    # UI Constants
    BANNER_WIDTH = 60
    SECTION_WIDTH = 50
    SEPARATOR_CHAR = "─"
    SUCCESS_ICON = "✅"
    ERROR_ICON = "❌"
    WARNING_ICON = "⚠️"
    INFO_ICON = "ℹ️"
    
    @classmethod
    def print_banner(cls):
        """Print clean application banner"""
        print()
        print("🎤 Voice-to-Text Transcription Application".center(cls.BANNER_WIDTH))
        print("=" * cls.BANNER_WIDTH)
        print(f"🚀 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(cls.BANNER_WIDTH))
        print()
    
    @classmethod
    def print_section_header(cls, title: str, icon: str = "📋"):
        """Print a clean section header"""
        print(f"{icon} {title}")
        print(cls.SEPARATOR_CHAR * cls.SECTION_WIDTH)
    
    @classmethod
    def print_section_footer(cls):
        """Print section footer"""
        print()
    
    @classmethod
    def print_status(cls, app: 'TranscriptionApplication'):
        """Print clean application status"""
        status = app.get_status()
        
        cls.print_section_header("Application Status", "📊")
        
        # Status items with consistent formatting
        status_items = [
            ("Session ID", status['session_id']),
            ("Config Loaded", status['config_loaded']),
            ("Output Manager", status['output_manager_ready']),
            ("Input Processor", status['input_processor_ready']),
            ("Output Processor", status['output_processor_ready']),
            ("Transcription Orchestrator", status['transcription_orchestrator_ready'])
        ]
        
        for label, value in status_items:
            if isinstance(value, bool):
                icon = cls.SUCCESS_ICON if value else cls.ERROR_ICON
                status_text = "Ready" if value else "Not Ready"
                print(f"  {label:<25} {icon} {status_text}")
            else:
                print(f"  {label:<25} {value}")
        
        cls.print_section_footer()
    
    @classmethod
    def print_help(cls):
        """Print clean and organized help information"""
        help_sections = [
            {
                "title": "Voice-to-Text Transcription Application",
                "description": "Modern, well-structured audio transcription using SOLID principles and dependency injection.",
                "icon": "🎤"
            },
            {
                "title": "Architecture",
                "items": [
                    "TranscriptionApplication (Main orchestrator)",
                    "InputProcessor (Input validation and discovery)",
                    "OutputProcessor (Output formatting and saving)",
                    "TranscriptionOrchestrator (Transcription coordination)",
                    "OutputManager (File operations and logging)"
                ],
                "icon": "🏗️"
            },
            {
                "title": "Configuration Files",
                "description": "All functionality controlled through config/environments/:",
                "items": [
                    "base.json - Default configuration",
                    "voice_task.json - Voice folder processing",
                    "docker_batch.json - Docker-enabled batch processing",
                    "runpod.json - RunPod cloud processing",
                    "development.json - Development settings",
                    "production.json - Production settings"
                ],
                "icon": "⚙️"
            },
            {
                "title": "Usage Examples",
                "items": [
                    "Single File: python main_app.py single file.wav --model base",
                    "Batch: python main_app.py batch --model base --engine faster-whisper",
                    "Voice Folder: python main_app.py --config-file config/environments/voice_task.json batch",
                    "Docker Batch: python main_app.py --config-file config/environments/docker_batch.json batch",
                    "Status: python main_app.py status"
                ],
                "icon": "🚀"
            },
            {
                "title": "Available Models",
                "items": [
                    "tiny - Fastest, least accurate",
                    "base - Balanced speed/accuracy",
                    "small - Good accuracy",
                    "medium - Better accuracy",
                    "large - Best accuracy, slowest",
                    "large-v2 - Improved accuracy",
                    "large-v3 - Latest and most accurate"
                ],
                "icon": "🤖"
            },
            {
                "title": "Available Engines",
                "items": [
                    "faster-whisper - Fast Whisper engine",
                    "stable-whisper - Stable Whisper engine",
                    "speaker-diarization - Speaker diarization with transcription"
                ],
                "icon": "⚙️"
            },
            {
                "title": "Output Formats",
                "items": [
                    "JSON - Structured transcription data",
                    "TXT - Plain text transcription",
                    "DOCX - Formatted document with speaker information"
                ],
                "icon": "📄"
            },
            {
                "title": "Configuration Features",
                "items": [
                    "Input validation and discovery",
                    "Batch processing with progress tracking",
                    "Docker container management",
                    "RunPod cloud integration",
                    "Speaker diarization presets",
                    "Comprehensive logging",
                    "Error handling and retry logic"
                ],
                "icon": "🔧"
            }
        ]
        
        for section in help_sections:
            cls.print_section_header(section["title"], section["icon"])
            
            if "description" in section:
                print(f"  {section['description']}")
                print()
            
            if "items" in section:
                for item in section["items"]:
                    print(f"  • {item}")
            
            cls.print_section_footer()
    
    @classmethod
    def print_config_info(cls, config_file: Optional[str] = None):
        """Print clean configuration information"""
        cls.print_section_header("Configuration Information", "📋")
        
        # Current configuration
        if config_file:
            print(f"  Current Config: {config_file}")
        else:
            print("  Current Config: Using default (config/environments/base.json)")
        
        print()
        
        # Available configuration files
        print("  Available Configuration Files:")
        config_dir = Path("config/environments")
        if config_dir.exists():
            config_files = sorted([f.name for f in config_dir.glob("*.json")])
            for config_file_name in config_files:
                print(f"    • {config_file_name}")
        else:
            print(f"    {cls.WARNING_ICON} No configuration directory found")
        
        print()
        
        # Configuration sections
        print("  Configuration Sections:")
        sections = [
            "transcription - Model and engine settings",
            "speaker - Speaker diarization configuration",
            "input - Input file discovery and validation",
            "batch - Batch processing settings",
            "docker - Docker container management",
            "runpod - RunPod cloud integration",
            "output - Output formatting and file management",
            "system - System-level settings"
        ]
        
        for section in sections:
            print(f"    • {section}")
        
        cls.print_section_footer()
    
    @classmethod
    def print_processing_info(cls, command: str, **kwargs):
        """Print clean processing information"""
        if command == "single":
            cls.print_section_header("Single File Processing", "🎤")
            print(f"  File: {kwargs.get('file', 'Unknown')}")
            print(f"  Model: {kwargs.get('model', 'default')}")
            print(f"  Engine: {kwargs.get('engine', 'default')}")
            if kwargs.get('speaker_preset'):
                print(f"  Speaker Preset: {kwargs['speaker_preset']}")
        
        elif command == "batch":
            cls.print_section_header("Batch Processing", "🔄")
            print(f"  Model: {kwargs.get('model', 'default')}")
            print(f"  Engine: {kwargs.get('engine', 'default')}")
            if kwargs.get('input_dir'):
                print(f"  Input Directory: {kwargs['input_dir']}")
            if kwargs.get('speaker_preset'):
                print(f"  Speaker Preset: {kwargs['speaker_preset']}")
        
        print(cls.SEPARATOR_CHAR * cls.SECTION_WIDTH)
    
    @classmethod
    def print_processing_result(cls, result: Dict[str, Any], command: str):
        """Print clean processing results"""
        if result['success']:
            if command == "single":
                cls.print_section_header("Processing Complete", "✅")
                print("  Single file processing completed successfully!")
                
                output_info = result.get('output', {})
                if 'formats_generated' in output_info:
                    formats = ', '.join(output_info['formats_generated'])
                    print(f"  Output Formats: {formats}")
            
            elif command == "batch":
                cls.print_section_header("Batch Processing Complete", "✅")
                print("  Batch processing completed successfully!")
                print()
                print("  Summary:")
                print(f"    • Total Files: {result['total_files']}")
                print(f"    • Successful: {result['successful']}")
                print(f"    • Failed: {result['failed']}")
        else:
            cls.print_section_header("Processing Failed", "❌")
            error_msg = result.get('error', 'Unknown error')
            print(f"  {error_msg}")
        
        cls.print_section_footer()
    
    @classmethod
    def print_success_message(cls):
        """Print clean success message"""
        print()
        print("🎉 Application completed successfully!".center(cls.BANNER_WIDTH))
        print()
    
    @classmethod
    def print_error_message(cls, error: str, verbose: bool = False):
        """Print clean error message"""
        print()
        cls.print_section_header("Application Error", "❌")
        print(f"  {error}")
        
        if verbose:
            print()
            print("  Detailed traceback:")
            import traceback
            traceback.print_exc()
        
        cls.print_section_footer()
    
    @classmethod
    def print_interrupt_message(cls):
        """Print clean interrupt message"""
        print()
        print("⚠️  Application interrupted by user".center(cls.BANNER_WIDTH))
        print() 