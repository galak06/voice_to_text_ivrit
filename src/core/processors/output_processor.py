"""
Output Processor
Responsible for handling output formatting, saving, and management
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging
from datetime import datetime
from pathlib import Path

from src.utils.config_manager import ConfigManager
from src.core.logic.result_builder import ResultBuilder

if TYPE_CHECKING:
    from src.output_data import OutputManager


class OutputProcessor:
    """
    Handles output processing and formatting
    
    This class follows the Single Responsibility Principle by focusing
    solely on output-related operations.
    """
    
    def __init__(self, config_manager: ConfigManager, output_manager: 'OutputManager'):
        """
        Initialize the output processor
        
        Args:
            config_manager: Configuration manager instance
            output_manager: Output manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.output_manager = output_manager
        self.logger = logging.getLogger('output-processor')
        
        # Output formats supported - can be overridden by config
        if self.config.output and hasattr(self.config.output, 'supported_formats'):
            supported_formats = getattr(self.config.output, 'supported_formats', None)
            if supported_formats and isinstance(supported_formats, (list, tuple)):
                self.supported_formats = list(supported_formats)
            else:
                self.supported_formats = ['json', 'txt', 'docx']
        else:
            self.supported_formats = ['json', 'txt', 'docx']
    
    def process_output(self, transcription_result: Dict[str, Any], 
                      input_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process transcription results into various output formats
        
        Args:
            transcription_result: Results from transcription
            input_metadata: Metadata about the input file
            
        Returns:
            Dictionary containing output processing results
        """
        try:
            self.logger.info("Processing transcription output")
            
            # Debug logging to see what we're receiving
            self.logger.info(f"🔍 Transcription result keys: {list(transcription_result.keys())}")
            self.logger.info(f"🔍 Transcription result type: {type(transcription_result)}")
            self.logger.info(f"🔍 Input metadata keys: {list(input_metadata.keys())}")
            
            # Validate transcription result
            if not transcription_result.get('success', False):
                self.logger.warning(f"🔍 Transcription failed, no output to process")
                return ResultBuilder.create_failure_result('Transcription failed, no output to process', transcription_result)
            
            # Check if output already saved by transcription service
            if self._is_output_already_saved(transcription_result):
                self.logger.info("🔍 Output already saved by transcription service")
                return ResultBuilder.create_already_saved_result()
            
            # Process output formats
            output_results = self._process_output_formats(transcription_result, input_metadata)
            
            self.logger.info(f"🔍 Output processing completed: {len(output_results)} formats")
            return ResultBuilder.create_success_result(output_results)
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Validation error processing output: {e}")
            return (ResultBuilder()
                    .success(False)
                    .error(str(e))
                    .build())
        except (OSError, IOError) as e:
            self.logger.error(f"File system error processing output: {e}")
            return (ResultBuilder()
                    .success(False)
                    .error(str(e))
                    .build())
        except Exception as e:
            self.logger.error(f"Unexpected error processing output: {e}")
            return (ResultBuilder()
                    .success(False)
                    .error(str(e))
                    .build())
    
    def _is_output_already_saved(self, transcription_result: Dict[str, Any]) -> bool:
        """Check if transcription service already saved the output"""
        # The transcription_result should have a 'success' field at the top level
        # The transcription_data inside should contain the actual transcription content
        transcription_data = transcription_result.get('transcription', {})
        
        # Check if the transcription data contains actual content that would indicate it was already saved
        # This should not be checking for a 'success' field in the transcription data
        if isinstance(transcription_data, dict):
            # Check if it contains actual transcription content
            has_text = bool(transcription_data.get('transcription', ''))
            has_segments = bool(transcription_data.get('segments', []))
            has_metadata = bool(transcription_data.get('metadata', {}))
            
            # If it has actual content, it might have been processed already
            # But we should still process it to ensure proper output formatting
            return False  # Always process the output to ensure proper formatting
        
        # If it's not a dict, it's probably raw text that needs processing
        return False
    
    def _create_failure_result(self, error_message: str, transcription_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create failure result"""
        return ResultBuilder.create_failure_result(error_message, transcription_result)
    
    def _create_already_saved_result(self) -> Dict[str, Any]:
        """Create result for already saved output"""
        self.logger.info("Transcription service already saved output, skipping duplicate save")
        return ResultBuilder.create_already_saved_result()
    
    def _process_output_formats(self, transcription_result: Dict[str, Any], 
                              input_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process different output formats"""
        transcription_data = transcription_result.get('transcription', {})
        model = transcription_result.get('model', 'unknown')
        engine = transcription_result.get('engine', 'unknown')
        input_file_path = input_metadata.get('file_name', 'unknown')
        
        output_results = {}
        
        # Check configuration for output format
        use_processed_text = True
        
        if self.config.output:
            use_processed_text = getattr(self.config.output, 'use_processed_text_only', True)
        
        # Process output based on configuration
        if use_processed_text:
            # Try to find enhanced JSON file with speaker information
            enhanced_data = self._get_enhanced_transcription_data(input_file_path, transcription_data)
            
            # Save all formats using enhanced data
            output_results['json'] = self._save_json_output(enhanced_data, input_file_path, model, engine)
            output_results['txt'] = self._save_text_output(enhanced_data, input_file_path, model, engine)
            output_results['docx'] = self._save_docx_output(enhanced_data, input_file_path, model, engine)
            
            self.logger.info("🔄 Using enhanced data with speaker information for all output formats")
        else:
            # Legacy mode - save all formats
            output_results['json'] = self._save_json_output(transcription_data, input_file_path, model, engine)
            output_results['txt'] = self._save_text_output(transcription_data, input_file_path, model, engine)
            output_results['docx'] = self._save_docx_output(transcription_data, input_file_path, model, engine)
        
        return output_results
    
    def _get_enhanced_transcription_data(self, input_file_path: str, fallback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Try to get enhanced transcription data with speaker information from JSON files"""
        try:
            import os
            import json
            from pathlib import Path
            
            # Look for enhanced JSON files in chunk_results directory
            chunk_results_dir = "output/chunk_results"
            if not os.path.exists(chunk_results_dir):
                self.logger.warning(f"Chunk results directory not found: {chunk_results_dir}")
                return fallback_data
            
            # Try to find enhanced JSON file for this input file
            input_filename = Path(input_file_path).stem  # Remove extension
            
            # Look for files that match the input filename pattern
            enhanced_files = []
            for filename in os.listdir(chunk_results_dir):
                if filename.endswith('.json'):
                    # Try multiple matching strategies
                    is_match = False
                    
                    # Strategy 1: Direct filename match (without extension)
                    if input_filename in filename:
                        is_match = True
                    
                    # Strategy 2: Look for chunk_* files that correspond to the input
                    elif 'chunk_' in filename and input_filename.replace('.wav', '').replace('.mp3', '').replace('.m4a', '') in filename:
                        is_match = True
                    
                    # Strategy 3: Look for any enhanced JSON file if we can't find a direct match
                    elif 'enhancement_applied' in filename or 'speaker' in filename.lower():
                        is_match = True
                    
                    if is_match:
                        file_path = os.path.join(chunk_results_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                            # Check if this is an enhanced file with speaker information
                            if (data.get('enhancement_applied', False) and 
                                data.get('enhancement_strategy') != 'basic' and
                                'speaker_recognition' in data):
                                
                                enhanced_files.append((file_path, data))
                                self.logger.info(f"Found enhanced JSON file: {filename}")
                        except Exception as e:
                            self.logger.debug(f"Could not read {filename}: {e}")
                            continue
            
            if enhanced_files:
                # Use the most recent enhanced file
                enhanced_files.sort(key=lambda x: x[1].get('created_at', 0), reverse=True)
                best_file_path, best_data = enhanced_files[0]
                
                self.logger.info(f"Using enhanced data from: {os.path.basename(best_file_path)}")
                self.logger.info(f"Speaker info: {list(best_data.get('speaker_recognition', {}).keys())}")
                
                return best_data
            else:
                self.logger.info("No enhanced JSON files found, using fallback data")
                return fallback_data
                
        except Exception as e:
            self.logger.warning(f"Error getting enhanced transcription data: {e}")
            return fallback_data
    
    def _create_success_result(self, output_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create success result"""
        result = ResultBuilder.create_success_result(output_results)
        self.logger.info(f"Output processing completed: {len(output_results)} formats generated")
        return result
    
    def _save_json_output(self, transcription_data: Any, input_file: str, 
                         model: str, engine: str) -> Dict[str, Any]:
        """
        Save transcription data as JSON
        
        Args:
            transcription_data: Transcription results
            input_file: Input file name
            model: Model used for transcription
            engine: Engine used for transcription
            
        Returns:
            Dictionary containing JSON output results
        """
        try:
            # Use the new unified save_transcription method
            saved_files = self.output_manager.save_transcription(
                transcription_data=transcription_data,
                audio_file=input_file,
                model=model,
                engine=engine
            )
            
            json_file = saved_files.get('json')
            if json_file:
                return {
                    'success': True,
                    'file_path': json_file,
                    'format': 'json'
                }
            else:
                return {
                    'success': False,
                    'error': 'JSON file not created',
                    'format': 'json'
                }
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Validation error saving JSON output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'json'
            }
        except (OSError, IOError) as e:
            self.logger.error(f"File system error saving JSON output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'json'
            }
        except Exception as e:
            self.logger.error(f"Unexpected error saving JSON output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'json'
            }
    
    def _save_text_output(self, transcription_data: Any, input_file: str,
                         model: str, engine: str) -> Dict[str, Any]:
        """
        Save transcription data as plain text
        
        Args:
            transcription_data: Transcription results
            input_file: Input file name
            model: Model used for transcription
            engine: Engine used for transcription
            
        Returns:
            Dictionary containing text output results
        """
        try:
            # Use the new unified save_transcription method
            saved_files = self.output_manager.save_transcription(
                transcription_data=transcription_data,
                audio_file=input_file,
                model=model,
                engine=engine
            )
            
            txt_file = saved_files.get('txt')
            if txt_file:
                return {
                    'success': True,
                    'file_path': txt_file,
                    'format': 'txt'
                }
            else:
                return {
                    'success': False,
                    'error': 'Text file not created',
                    'format': 'txt'
                }
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Validation error saving text output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'txt'
            }
        except (OSError, IOError) as e:
            self.logger.error(f"File system error saving text output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'txt'
            }
        except Exception as e:
            self.logger.error(f"Unexpected error saving text output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'txt'
            }
    
    def _save_docx_output(self, transcription_data: Any, input_file: str,
                         model: str, engine: str) -> Dict[str, Any]:
        """
        Save transcription data as DOCX document
        
        Args:
            transcription_data: Transcription results
            input_file: Input file name
            model: Model used for transcription
            engine: Engine used for transcription
            
        Returns:
            Dictionary containing DOCX output results
        """
        try:
            # Use the new unified save_transcription method
            saved_files = self.output_manager.save_transcription(
                transcription_data=transcription_data,
                audio_file=input_file,
                model=model,
                engine=engine
            )
            
            docx_file = saved_files.get('docx')
            if docx_file:
                return {
                    'success': True,
                    'file_path': docx_file,
                    'format': 'docx'
                }
            else:
                return {
                    'success': False,
                    'error': 'DOCX file not created',
                    'format': 'docx'
                }
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Validation error saving DOCX output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'docx'
            }
        except (OSError, IOError) as e:
            self.logger.error(f"File system error saving DOCX output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'docx'
            }
        except Exception as e:
            self.logger.error(f"Unexpected error saving DOCX output: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': 'docx'
            }
    
    def _extract_text_content(self, transcription_data: Any) -> str:
        """
        Extract plain text content from transcription data
        
        Args:
            transcription_data: Transcription results
            
        Returns:
            Plain text content
        """
        if isinstance(transcription_data, str):
            return transcription_data
        
        if isinstance(transcription_data, list):
            # Handle list of segments
            text_parts = []
            for segment in transcription_data:
                if isinstance(segment, dict):
                    text = segment.get('text', '')
                    if text:
                        text_parts.append(text)
                elif isinstance(segment, str):
                    text_parts.append(segment)
            return '\n'.join(text_parts)
        
        if isinstance(transcription_data, dict):
            # Handle dictionary format
            if 'text' in transcription_data:
                return str(transcription_data['text'])
            elif 'transcription' in transcription_data:
                return self._extract_text_content(transcription_data['transcription'])
        
        # Fallback: convert to string
        return str(transcription_data)
    
    def _convert_to_docx_format(self, transcription_data: Any) -> List[Dict[str, Any]]:
        """
        Convert transcription data to format suitable for DOCX
        
        Args:
            transcription_data: Transcription results
            
        Returns:
            List of dictionaries in DOCX format
        """
        if isinstance(transcription_data, list):
            # Already in list format
            return transcription_data
        
        if isinstance(transcription_data, dict):
            # Convert dictionary to list format
            if 'transcription' in transcription_data:
                return self._convert_to_docx_format(transcription_data['transcription'])
            elif 'text' in transcription_data:
                return [{
                    'text': transcription_data['text'],
                    'start': transcription_data.get('start', 0),
                    'end': transcription_data.get('end', 0),
                    'speaker': transcription_data.get('speaker', 'Unknown')
                }]
        
        # Fallback: create single segment
        return [{
            'text': str(transcription_data),
            'start': 0,
            'end': 0,
            'speaker': 'Unknown'
        }]
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats
        
        Returns:
            List of supported output formats
        """
        return self.supported_formats.copy()
    
    def add_supported_format(self, format_name: str):
        """
        Add a new supported output format
        
        Args:
            format_name: Format name to add (e.g., 'pdf')
        """
        if format_name not in self.supported_formats:
            self.supported_formats.append(format_name)
            self.logger.info(f"Added supported output format: {format_name}")
        else:
            self.logger.warning(f"Format already supported: {format_name}")
    
    def remove_supported_format(self, format_name: str):
        """
        Remove a supported output format
        
        Args:
            format_name: Format name to remove
        """
        if format_name in self.supported_formats:
            self.supported_formats.remove(format_name)
            self.logger.info(f"Removed supported output format: {format_name}")
        else:
            self.logger.warning(f"Format not in supported list: {format_name}")
    
    def get_output_summary(self, output_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of output processing results
        
        Args:
            output_results: Results from output processing
            
        Returns:
            Dictionary containing output summary
        """
        if not output_results.get('success', False):
            return {
                'success': False,
                'error': output_results.get('error', 'Unknown error'),
                'files_generated': 0
            }
        
        output_files = output_results.get('output_files', {})
        successful_formats = [
            format_name for format_name, result in output_files.items()
            if result.get('success', False)
        ]
        
        return {
            'success': True,
            'files_generated': len(successful_formats),
            'formats': successful_formats,
            'total_formats_attempted': len(output_files)
        } 