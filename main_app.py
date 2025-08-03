#!/usr/bin/env python3
"""
Main Application Entry Point
Uses the new software architecture with proper dependency injection
All functionality is controlled through configuration files
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.ui_manager import ApplicationUI


def setup_logging(verbose: bool = False):
    """Setup application logging"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler()
        ]
    )


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="Voice-to-Text Transcription Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_app.py single examples/audio/voice/rachel_1.wav --model base
  python main_app.py batch --model base --engine faster-whisper
  python main_app.py batch --config-file config/environments/voice_task.json
  python main_app.py batch --config-file config/environments/docker_batch.json
  python main_app.py status
  python main_app.py --help
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--config-file', help='Configuration file path')
    parser.add_argument('--help-config', action='store_true', help='Show configuration information')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single file processing
    single_parser = subparsers.add_parser('single', help='Process a single audio file')
    single_parser.add_argument('file', help='Audio file to process')
    single_parser.add_argument('--model', help='Model to use for transcription')
    single_parser.add_argument('--engine', help='Engine to use for transcription')
    single_parser.add_argument('--speaker-preset', choices=['default', 'conversation', 'interview'], 
                              help='Speaker diarization preset')
    
    # Batch processing
    batch_parser = subparsers.add_parser('batch', help='Process multiple audio files')
    batch_parser.add_argument('--model', help='Model to use for transcription')
    batch_parser.add_argument('--engine', help='Engine to use for transcription')
    batch_parser.add_argument('--input-dir', help='Input directory (overrides config)')
    batch_parser.add_argument('--speaker-preset', choices=['default', 'conversation', 'interview'], 
                             help='Speaker diarization preset')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Show application status')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Print banner
    ApplicationUI.print_banner()
    
    # Handle help-config
    if args.help_config:
        ApplicationUI.print_config_info(args.config_file)
        return
    
    # Handle no command
    if not args.command:
        ApplicationUI.print_help()
        return
    
    try:
        # Initialize application with configuration
        config_file: Optional[str] = args.config_file if args.config_file else None
        with TranscriptionApplication(config_file) as app:
            
            if args.command == 'status':
                ApplicationUI.print_status(app)
                return
            
            elif args.command == 'single':
                # Print processing information
                ApplicationUI.print_processing_info(
                    "single",
                    file=args.file,
                    model=args.model,
                    engine=args.engine,
                    speaker_preset=args.speaker_preset
                )
                
                # Process single file
                result = app.process_single_file(
                    args.file,
                    model=args.model,
                    engine=args.engine,
                    speaker_preset=args.speaker_preset
                )
                
                # Print results
                ApplicationUI.print_processing_result(result, "single")
                
                if not result['success']:
                    return 1
            
            elif args.command == 'batch':
                # Print processing information
                ApplicationUI.print_processing_info(
                    "batch",
                    model=args.model,
                    engine=args.engine,
                    input_dir=args.input_dir,
                    speaker_preset=args.speaker_preset
                )
                
                # Process batch
                result = app.process_batch(
                    input_directory=args.input_dir,
                    model=args.model,
                    engine=args.engine,
                    speaker_preset=args.speaker_preset
                )
                
                # Print results
                ApplicationUI.print_processing_result(result, "batch")
                
                if not result['success']:
                    return 1
        
        ApplicationUI.print_success_message()
        return 0
        
    except KeyboardInterrupt:
        ApplicationUI.print_interrupt_message()
        return 130
    except Exception as e:
        ApplicationUI.print_error_message(str(e), args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 