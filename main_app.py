#!/usr/bin/env python3
"""
Main Application Entry Point
Voice-to-Text Transcription Application
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Callable, Union
from functools import wraps

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.argument_parser import ArgumentParser
from src.utils.config_manager import ConfigManager
from src.utils.ui_manager import ApplicationUI
from src.core.engines.utilities.cleanup_manager import CleanupManager


def require_component(component_name: str) -> Callable:
    """
    Decorator to handle null checks for required components.
    
    This follows the Single Responsibility Principle by separating null checking logic
    from business logic, and the Open/Closed Principle by making error handling extensible.
    
    Args:
        component_name: Name of the component being checked (for error messages)
    
    Returns:
        Decorated function that handles null checks automatically
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> int:
            component = getattr(self, component_name, None)
            if component is None:
                if hasattr(self, 'ui') and self.ui:
                    self.ui.print_error_message(f"{component_name} not available")
                else:
                    logger = logging.getLogger(__name__)
                    logger.error(f"{component_name} not available")
                return ExitCodes.ERROR
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


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
    
    def handle_config_info(self, config_file: Union[str, None]) -> int:
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
        
        # Display detailed results like the script does
        if result and result.get('success'):
            print("✅ Transcription completed successfully!")
            print("-" * 60)
            print("📝 TRANSCRIPTION RESULT:")
            print("=" * 60)
            
            # Display transcription text from the result structure
            transcription_result = result.get('transcription', {})
            if transcription_result.get('success'):
                # Try to get text from different possible locations
                text = None
                
                # First try to get from segments
                segments = transcription_result.get('segments', [])
                if segments and len(segments) > 0:
                    if isinstance(segments[0], dict):
                        text = segments[0].get('text', segments[0].get('transcription', ''))
                    else:
                        text = str(segments[0])
                
                # If no segments, try to get from transcription field directly
                if not text:
                    text = transcription_result.get('text', transcription_result.get('transcription', ''))
                
                # If still no text, try to get from full_text
                if not text:
                    text = transcription_result.get('full_text', '')
                
                if text:
                    print(f"📝 Transcription: {text}")
                else:
                    print("No transcription text found in result structure")
                    print(f"Available keys: {list(transcription_result.keys())}")
            else:
                print("Transcription processing failed")
                if 'error' in transcription_result:
                    print(f"Error: {transcription_result['error']}")
            
            print("=" * 60)
            
            # Show output files
            output_result = result.get('output', {})
            if output_result.get('success'):
                print("\n📁 Output processing completed successfully")
                # You can add more output file details here if needed
            
            # Show performance metrics if available
            if 'processing_time' in result:
                print(f"\n⏱️  Processing time: {result['processing_time']:.2f} seconds")
        
        else:
            print("❌ Transcription failed!")
            if result and 'error' in result:
                print(f"Error: {result['error']}")
            elif result and 'transcription' in result:
                trans_error = result['transcription'].get('error', 'Unknown error')
                print(f"Transcription error: {trans_error}")
        
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
        self.config_manager: Union[ConfigManager, None] = None
        self.app: Union[TranscriptionApplication, None] = None
        self.ui: Union[ApplicationUI, None] = None
        self.command_handler: Union[CommandHandler, None] = None
    
    def initialize(self, config_file: Union[str, None] = None) -> None:
        """Initialize application components with dependency injection"""
        # Initialize configuration manager - only create one instance
        if config_file:
            # Use the directory that contains the config file directly
            config_dir = str(Path(config_file).parent)
            
            # Determine environment based on config file name
            from src.models.environment import Environment
            if 'production' in config_file or 'ivrit_whisper_large_v3_ct2' in config_file:
                environment = Environment.PRODUCTION
            else:
                environment = Environment.BASE
            
            self.config_manager = ConfigManager(config_dir, environment)
        else:
            # Use default config directory
            self.config_manager = ConfigManager()
        
        # Initialize application with dependency injection
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 CONFIG DEBUG: Creating cleanup manager with ConfigManager: {type(self.config_manager)}")
        
        # Debug configuration loading
        self.config_manager.debug_config()
        
        cleanup_manager = CleanupManager(self.config_manager)
        logger.info(f"🔍 CONFIG DEBUG: Created cleanup manager: {type(cleanup_manager)}")
        
        logger.info(f"🔍 CONFIG DEBUG: Creating TranscriptionApplication with ConfigManager: {type(self.config_manager)}")
        self.app = TranscriptionApplication(
            config_manager=self.config_manager,
            cleanup_manager=cleanup_manager
        )
        logger.info(f"🔍 CONFIG DEBUG: Created TranscriptionApplication: {type(self.app)}")
        self.ui = self.app.ui_manager
        self.command_handler = CommandHandler(self.app, self.ui)
        
        # Verify config manager injection chain
        self._verify_config_injection()
    
    def _verify_config_injection(self) -> None:
        """Verify that config manager is properly injected throughout the application"""
        if not self.config_manager or not self.app:
            return
            
        # Verify the injection chain
        assert self.app.config_manager is self.config_manager, "App should use the same config manager"
        assert self.ui.config_manager is self.config_manager, "UI should use the same config manager"
        
        # Log successful injection
        logger = logging.getLogger(__name__)
        logger.debug("✅ Config manager injection verified successfully")
    
    def run(self, args) -> int:
        """Run the application with proper error handling"""
        try:
            if self.app is None:
                raise RuntimeError("Application not initialized")
            
            with self.app:
                # Print banner
                if self.ui:
                    self.ui.print_banner()
                
                # 🧹 EXECUTE COMPREHENSIVE CLEANUP AT THE BEGINNING OF THE PROCESS
                if hasattr(self.app, 'cleanup_manager') and self.app.cleanup_manager:
                    logger = logging.getLogger(__name__)
                    logger.info("🧹 EXECUTING COMPREHENSIVE CLEANUP AT THE BEGINNING OF THE PROCESS")
                    self.app.cleanup_manager.execute_cleanup(
                        clear_console=True,
                        clear_files=True,
                        clear_output=False
                    )
                    logger.info("✅ COMPREHENSIVE CLEANUP COMPLETED SUCCESSFULLY")
                else:
                    logger = logging.getLogger(__name__)
                    logger.warning("⚠️ Cleanup manager not available, skipping comprehensive cleanup")
                
                # Handle special commands first
                if args.help_config:
                    return self._handle_config_info(args.config_file)
                
                if not args.command:
                    return self._handle_help()
                
                # Handle main commands
                if args.command == 'status':
                    return self._handle_status()
                
                elif args.command == 'single':
                    return self._handle_single_file(args)
                
                elif args.command == 'batch':
                    return self._handle_batch(args)
                
                # If we get here, command was not recognized
                if self.ui:
                    self.ui.print_error_message(f"Unknown command: {args.command}")
                return ExitCodes.ERROR
            
        except KeyboardInterrupt:
            return self._handle_interrupt()
        except Exception as e:
            return self._handle_error(e, args.verbose)
    
    @require_component('command_handler')
    def _handle_config_info(self, config_file: Union[str, None]) -> int:
        """Handle config info command with null check"""
        return self.command_handler.handle_config_info(config_file)  # type: ignore
    
    @require_component('command_handler')
    def _handle_help(self) -> int:
        """Handle help command with null check"""
        return self.command_handler.handle_help()  # type: ignore
    
    @require_component('command_handler')
    def _handle_status(self) -> int:
        """Handle status command with null check"""
        return self.command_handler.handle_status()  # type: ignore
    
    @require_component('command_handler')
    def _handle_single_file(self, args) -> int:
        """Handle single file command with null check"""
        return self.command_handler.handle_single_file(args)  # type: ignore
    
    @require_component('command_handler')
    def _handle_batch(self, args) -> int:
        """Handle batch command with null check"""
        return self.command_handler.handle_batch(args)  # type: ignore
    
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