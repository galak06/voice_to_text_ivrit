#!/usr/bin/env python3
"""
Main Application Entry Point
Voice-to-Text Transcription Application
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.argument_parser import ArgumentParser
from src.utils.config_manager import ConfigManager
from src.utils.ui_manager import ApplicationUI


# Constants for clean code
class ExitCodes:
    """Exit codes for the application"""
    SUCCESS = 0
    ERROR = 1
    INTERRUPT = 130


def setup_logging(verbose: bool = False) -> None:
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


class CommandHandler:
    """Handles different application commands following Single Responsibility Principle"""
    
    def __init__(self, app: TranscriptionApplication, ui: ApplicationUI):
        self.app = app
        self.ui = ui
    
    def handle_status(self) -> int:
        """Handle status command"""
        self.ui.print_status(self.app)
        return ExitCodes.SUCCESS
    
    def handle_help(self) -> int:
        """Handle help command"""
        self.ui.print_help()
        return ExitCodes.SUCCESS
    
    def handle_config_info(self, config_file: Optional[str]) -> int:
        """Handle config info command"""
        self.ui.print_config_info(config_file)
        return ExitCodes.SUCCESS
    
    def handle_single_file(self, args) -> int:
        """Handle single file processing command"""
        # Print processing information
        self.ui.print_processing_info(
            "single",
            file=args.file,
            model=args.model,
            engine=args.engine,
            speaker_preset=args.speaker_preset
        )
        
        # Process single file
        result = self.app.process_single_file(
            args.file,
            model=args.model,
            engine=args.engine,
            speaker_preset=args.speaker_preset
        )
        
        # Print results
        self.ui.print_processing_result(result, "single")
        
        return ExitCodes.SUCCESS if result['success'] else ExitCodes.ERROR
    
    def handle_batch(self, args) -> int:
        """Handle batch processing command"""
        # Print processing information
        self.ui.print_processing_info(
            "batch",
            model=args.model,
            engine=args.engine,
            input_dir=args.input_dir,
            speaker_preset=args.speaker_preset
        )
        
        # Process batch
        result = self.app.process_batch(
            input_directory=args.input_dir,
            model=args.model,
            engine=args.engine,
            speaker_preset=args.speaker_preset
        )
        
        # Print results
        self.ui.print_processing_result(result, "batch")
        
        return ExitCodes.SUCCESS if result['success'] else ExitCodes.ERROR


class ApplicationOrchestrator:
    """Orchestrates the application lifecycle following Single Responsibility Principle"""
    
    def __init__(self):
        self.config_manager: Optional[ConfigManager] = None
        self.app: Optional[TranscriptionApplication] = None
        self.ui: Optional[ApplicationUI] = None
        self.command_handler: Optional[CommandHandler] = None
    
    def initialize(self, config_file: Optional[str] = None) -> None:
        """Initialize application components with dependency injection"""
        # Initialize configuration manager
        if config_file:
            # Extract directory from config file path
            config_dir = str(Path(config_file).parent)
            self.config_manager = ConfigManager(config_dir)
        else:
            self.config_manager = ConfigManager()
        
        # Initialize application with dependency injection
        self.app = TranscriptionApplication(config_manager=self.config_manager)
        self.ui = self.app.ui_manager
        self.command_handler = CommandHandler(self.app, self.ui)
    
    def run(self, args) -> int:
        """Run the application with proper error handling"""
        try:
            if self.app is None:
                raise RuntimeError("Application not initialized")
            
            with self.app:
                # Print banner
                if self.ui:
                    self.ui.print_banner()
                
                # Handle special commands first
                if args.help_config:
                    if self.command_handler:
                        return self.command_handler.handle_config_info(args.config_file)
                    return ExitCodes.ERROR
                
                if not args.command:
                    if self.command_handler:
                        return self.command_handler.handle_help()
                    return ExitCodes.ERROR
                
                # Handle main commands
                if args.command == 'status':
                    if self.command_handler:
                        return self.command_handler.handle_status()
                    return ExitCodes.ERROR
                
                elif args.command == 'single':
                    if self.command_handler:
                        return self.command_handler.handle_single_file(args)
                    return ExitCodes.ERROR
                
                elif args.command == 'batch':
                    if self.command_handler:
                        return self.command_handler.handle_batch(args)
                    return ExitCodes.ERROR
                
                # If we get here, command was not recognized
                if self.ui:
                    self.ui.print_error_message(f"Unknown command: {args.command}")
                return ExitCodes.ERROR
            
        except KeyboardInterrupt:
            return self._handle_interrupt()
        except Exception as e:
            return self._handle_error(e, args.verbose)
    
    def _handle_interrupt(self) -> int:
        """Handle keyboard interrupt with proper UI"""
        logger = logging.getLogger(__name__)
        if self.ui:
            self.ui.print_interrupt_message()
        else:
            # Fallback if UI not available
            logger.warning("Application interrupted by user")
        return ExitCodes.INTERRUPT
    
    def _handle_error(self, error: Exception, verbose: bool) -> int:
        """Handle application errors with proper UI"""
        logger = logging.getLogger(__name__)
        if self.ui:
            self.ui.print_error_message(str(error), verbose)
        else:
            # Fallback if UI not available
            logger.error(f"Application Error: {error}")
            if verbose:
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
        return ExitCodes.ERROR


def main() -> int:
    """Main application entry point - now follows Single Responsibility Principle"""
    # Parse command-line arguments
    args = ArgumentParser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Create and run application orchestrator
    orchestrator = ApplicationOrchestrator()
    orchestrator.initialize(args.config_file)
    
    return orchestrator.run(args)


if __name__ == "__main__":
    sys.exit(main()) 