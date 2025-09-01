"""
Conversation Service
Main service that orchestrates chunk merging and conversation formatting
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from src.utils.config_manager import ConfigManager
from .chunk_merger import ChunkMerger
from .conversation_formatter import ConversationFormatter, ConversationOutputGenerator


class ConversationService:
    """
    Main service that orchestrates the conversation generation process.
    
    This service follows the Facade pattern by providing a simple interface
    to the complex process of merging chunks and formatting conversations.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the conversation service.
        
        Args:
            config_manager: Configuration manager for dependency injection
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize sub-services with dependency injection
        self.chunk_merger = ChunkMerger(config_manager)
        self.conversation_formatter = ConversationFormatter(config_manager)
        
        # Get output directory from config
        self.output_dir = self._get_output_directory()
    
    def _get_output_directory(self) -> Path:
        """Get the output directory from configuration."""
        try:
            if hasattr(self.config_manager.config, 'output') and hasattr(self.config_manager.config.output, 'output_dir'):
                output_path = Path(self.config_manager.config.output.output_dir)
            else:
                output_path = Path("output/transcriptions")
            
            # Ensure directory exists
            output_path.mkdir(parents=True, exist_ok=True)
            return output_path
            
        except Exception as e:
            self.logger.warning(f"Could not get output directory from config: {e}, using default")
            default_path = Path("output/transcriptions")
            default_path.mkdir(parents=True, exist_ok=True)
            return default_path
    
    def generate_conversation_from_chunks(self, chunk_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate conversation output from chunk results.
        
        Args:
            chunk_dir: Directory containing chunk JSON files (optional, uses config default)
            
        Returns:
            Dictionary containing generated output file paths and metadata
        """
        try:
            self.logger.info("🚀 Starting conversation generation from chunks...")
            
            # Use provided chunk directory or default from config
            if chunk_dir is None:
                chunk_dir = self._get_chunk_directory()
            
            # Step 1: Merge chunks
            self.logger.info("📊 Step 1: Merging chunks...")
            merged_data = self.chunk_merger.merge_chunks_from_directory(chunk_dir)
            
            # Step 2: Validate merged data
            self.logger.info("✅ Step 2: Validating merged data...")
            validation_result = self.chunk_merger.validate_merged_data(merged_data)
            
            if not validation_result['is_valid']:
                self.logger.warning("⚠️ Validation warnings:")
                for warning in validation_result['warnings']:
                    self.logger.warning(f"  - {warning}")
            
            if validation_result['errors']:
                self.logger.error("❌ Validation errors:")
                for error in validation_result['errors']:
                    self.logger.error(f"  - {error}")
                raise ValueError("Merged data validation failed")
            
            # Step 3: Format as conversation
            self.logger.info("💬 Step 3: Formatting as conversation...")
            formatted_data = self.conversation_formatter.format_as_conversation(merged_data)
            
            # Log the mode being used
            mode = formatted_data.get('mode', 'unknown')
            if mode == 'single_speaker':
                self.logger.info("📝 Using single speaker mode (speaker recognition disabled)")
            else:
                self.logger.info("🎤 Using multi-speaker mode (speaker recognition enabled)")
            
            # Step 4: Generate output files
            self.logger.info("📝 Step 4: Generating output files...")
            output_generator = ConversationOutputGenerator(self.config_manager, self.output_dir)
            output_files = output_generator.generate_all_outputs(formatted_data)
            
            # Step 5: Prepare result
            result = {
                'success': True,
                'output_files': output_files,
                'metadata': {
                    'chunks_processed': merged_data.get('total_chunks', 0),
                    'total_duration': merged_data.get('total_duration', 0),
                    'conversation_turns': formatted_data['metadata']['total_turns'],
                    'speakers': list(merged_data.get('speakers', {}).keys()),
                    'validation_result': validation_result
                },
                'formatted_data': formatted_data
            }
            
            self.logger.info("🎉 Conversation generation completed successfully!")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error generating conversation: {e}")
            return {
                'success': False,
                'error': str(e),
                'output_files': {},
                'metadata': {}
            }
    
    def _get_chunk_directory(self) -> Path:
        """Get the chunk directory from configuration."""
        try:
            if hasattr(self.config_manager.config, 'output') and hasattr(self.config_manager.config.output, 'chunk_results_dir'):
                chunk_path = Path(self.config_manager.config.output.chunk_results_dir)
            else:
                chunk_path = Path("output/chunk_results")
            
            if not chunk_path.exists():
                raise FileNotFoundError(f"Chunk directory not found: {chunk_path}")
            
            return chunk_path
            
        except Exception as e:
            self.logger.warning(f"Could not get chunk directory from config: {e}, using default")
            default_path = Path("output/chunk_results")
            if not default_path.exists():
                raise FileNotFoundError(f"Default chunk directory not found: {default_path}")
            return default_path
    
    def get_conversation_statistics(self, chunk_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Get statistics about the conversation without generating output files.
        
        Args:
            chunk_dir: Directory containing chunk JSON files (optional)
            
        Returns:
            Dictionary containing conversation statistics
        """
        try:
            # Use provided chunk directory or default from config
            if chunk_dir is None:
                chunk_dir = self._get_chunk_directory()
            
            # Merge chunks
            merged_data = self.chunk_merger.merge_chunks_from_directory(chunk_dir)
            
            # Format as conversation
            formatted_data = self.conversation_formatter.format_as_conversation(merged_data)
            
            # Return statistics
            mode = formatted_data.get('mode', 'unknown')
            if mode == 'single_speaker':
                return {
                    'chunks_processed': merged_data.get('total_chunks', 0),
                    'total_duration': merged_data.get('total_duration', 0),
                    'conversation_turns': formatted_data['metadata']['total_turns'],
                    'speakers': ['SINGLE_SPEAKER'],
                    'speaker_summary': formatted_data['speaker_summary'],
                    'formatting_config': formatted_data['metadata']['formatting_config'],
                    'mode': 'single_speaker'
                }
            else:
                return {
                    'chunks_processed': merged_data.get('total_chunks', 0),
                    'total_duration': merged_data.get('total_duration', 0),
                    'conversation_turns': formatted_data['metadata']['total_turns'],
                    'speakers': list(merged_data.get('speakers', {}).keys()),
                    'speaker_summary': formatted_data['speaker_summary'],
                    'formatting_config': formatted_data['metadata']['formatting_config'],
                    'mode': 'multi_speaker'
                }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting conversation statistics: {e}")
            return {
                'error': str(e),
                'chunks_processed': 0,
                'total_duration': 0,
                'conversation_turns': 0,
                'speakers': [],
                'speaker_summary': {},
                'formatting_config': {}
            }
    
    def validate_chunk_directory(self, chunk_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Validate that a chunk directory contains valid chunk files.
        
        Args:
            chunk_dir: Directory to validate (optional, uses config default)
            
        Returns:
            Validation results
        """
        try:
            # Use provided chunk directory or default from config
            if chunk_dir is None:
                chunk_dir = self._get_chunk_directory()
            
            # Check if directory exists
            if not chunk_dir.exists():
                return {
                    'is_valid': False,
                    'errors': [f"Directory does not exist: {chunk_dir}"],
                    'warnings': [],
                    'statistics': {}
                }
            
            # Find chunk files
            chunk_files = list(chunk_dir.glob("chunk_*.json"))
            
            if not chunk_files:
                return {
                    'is_valid': False,
                    'errors': [f"No chunk files found in directory: {chunk_dir}"],
                    'warnings': [],
                    'statistics': {'chunk_files': 0}
                }
            
            # Validate chunk files
            valid_chunks = 0
            invalid_chunks = 0
            
            for chunk_file in chunk_files:
                try:
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                    
                    # Basic validation
                    if chunk_data.get('status') == 'completed' and chunk_data.get('text'):
                        valid_chunks += 1
                    else:
                        invalid_chunks += 1
                        
                except Exception as e:
                    invalid_chunks += 1
            
            return {
                'is_valid': valid_chunks > 0,
                'errors': [],
                'warnings': [f"{invalid_chunks} invalid chunks found"] if invalid_chunks > 0 else [],
                'statistics': {
                    'total_chunk_files': len(chunk_files),
                    'valid_chunks': valid_chunks,
                    'invalid_chunks': invalid_chunks
                }
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f"Validation error: {e}"],
                'warnings': [],
                'statistics': {}
            }
