#!/usr/bin/env python3
"""
Argument Parser for the Voice-to-Text Transcription Application
Handles command-line argument parsing and validation
"""

import argparse
from typing import Optional
import sys


class ArgumentParser:
    """Handles command-line argument parsing for the transcription application"""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create and configure the argument parser"""
        parser = argparse.ArgumentParser(
            description='Voice-to-Text Transcription Application',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main_app.py single file.wav --model base
  python main_app.py batch --model base --engine speaker-diarization
  python main_app.py --config-file config/environments/voice_task.json batch
  python main_app.py status
            """
        )
        
        # Global arguments
        parser.add_argument('--config-file', help='Configuration file path')
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
        parser.add_argument('--help-config', action='store_true',
                           help='Show configuration information and examples')
        
        # Add examples
        parser.add_argument('--examples', action='store_true',
                           help='Show usage examples')
        
        # Example usage
        if len(sys.argv) > 1 and sys.argv[1] == '--examples':
            print("Usage Examples:")
            print("Single file: python main_app.py single examples/audio/voice/audio.wav --model base --engine speaker-diarization")
            print("Batch: python main_app.py batch --model base --engine speaker-diarization")
            print("Stable-whisper: python main_app.py single examples/audio/voice/audio.wav --engine stable-whisper")
            sys.exit(0)
        
        # Subparsers for different commands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Single file processing
        single_parser = subparsers.add_parser('single', help='Process a single audio file')
        single_parser.add_argument('file', help='Audio file to process')
        single_parser.add_argument('--model', help='Model to use for transcription')
        single_parser.add_argument('--engine', help='Engine to use for transcription')
        single_parser.add_argument('--speaker-preset', 
                                 choices=['default', 'conversation', 'interview'], 
                                 help='Speaker diarization preset')
        
        # Batch processing
        batch_parser = subparsers.add_parser('batch', help='Process multiple audio files')
        batch_parser.add_argument('--model', help='Model to use for transcription')
        batch_parser.add_argument('--engine', help='Engine to use for transcription')
        batch_parser.add_argument('--input-dir', help='Input directory (overrides config)')
        batch_parser.add_argument('--speaker-preset', 
                                choices=['default', 'conversation', 'interview'], 
                                help='Speaker diarization preset')
        
        # Status
        status_parser = subparsers.add_parser('status', help='Show application status')
        
        return parser
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """Parse command-line arguments"""
        parser = ArgumentParser.create_parser()
        return parser.parse_args() 