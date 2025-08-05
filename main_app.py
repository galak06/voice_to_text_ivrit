#!/usr/bin/env python3
"""
Main Application Entry Point
Voice-to-Text Transcription Application
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.argument_parser import ArgumentParser
from src.utils.config_manager import ConfigManager
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
    # Parse command-line arguments
    args = ArgumentParser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Initialize configuration manager
        config_manager = None
        if args.config_file:
            config_manager = ConfigManager(args.config_file)
        
        # Initialize application with dependency injection
        with TranscriptionApplication(config_manager=config_manager) as app:
            
            # Print banner
            app.ui_manager.print_banner()
            
            # Handle help-config
            if args.help_config:
                app.ui_manager.print_config_info(args.config_file)
                return 0
            
            # Handle no command
            if not args.command:
                app.ui_manager.print_help()
                return 0
            
            if args.command == 'status':
                app.ui_manager.print_status(app)
                return 0
            
            elif args.command == 'single':
                # Print processing information
                app.ui_manager.print_processing_info(
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
                app.ui_manager.print_processing_result(result, "single")
                
                if not result['success']:
                    return 1
            
            elif args.command == 'batch':
                # Print processing information
                app.ui_manager.print_processing_info(
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
                app.ui_manager.print_processing_result(result, "batch")
                
                if not result['success']:
                    return 1
        
        app.ui_manager.print_success_message()
        return 0
        
    except KeyboardInterrupt:
        # Create temporary UI for error messages
        temp_ui = ApplicationUI()
        temp_ui.print_interrupt_message()
        return 130
    except Exception as e:
        # Create temporary UI for error messages
        temp_ui = ApplicationUI()
        temp_ui.print_error_message(str(e), args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 