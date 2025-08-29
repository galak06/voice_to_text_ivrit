#!/usr/bin/env python3
"""
Main Application Entry Point - Skip Transcription Version
Voice-to-Text Transcription Application that skips transcription and processes existing chunks
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from functools import wraps

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.argument_parser import ArgumentParser
from src.utils.config_manager import ConfigManager
from src.models.environment import Environment
from src.utils.ui_manager import ApplicationUI
from src.core.engines.utilities.cleanup_manager import CleanupManager
from src.core.processors.output_processor import OutputProcessor
from src.output_data.managers.output_manager import OutputManager
from src.output_data.utils.data_utils import DataUtils
from src.output_data.formatters.text_formatter import TextFormatter
from src.core.engines.utilities.text_processor import TextProcessor
import json
import os
from datetime import datetime


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
    
    def handle_config_info(self, config_file: Optional[str]) -> int:
        """Handle config info command"""
        self.ui.print_config_info(config_file)
        return ExitCodes.SUCCESS
    
    def handle_process_existing_chunks(self, args) -> int:
        """Handle processing existing chunks without transcription - merge into unified output"""
        print("🔄 Processing existing chunks and merging into unified output...")
        
        # Check if chunk results directory exists
        chunk_results_dir = "output/chunk_results"
        if not os.path.exists(chunk_results_dir):
            print(f"❌ Chunk results directory not found: {chunk_results_dir}")
            return ExitCodes.ERROR
        
        # Load all completed chunks
        chunk_files = [f for f in os.listdir(chunk_results_dir) if f.startswith('chunk_') and f.endswith('.json')]
        chunk_files.sort(key=lambda x: int(x.split('_')[1]))  # Sort by chunk number
        
        if not chunk_files:
            print("❌ No chunk result files found")
            return ExitCodes.ERROR
        
        print(f"📁 Found {len(chunk_files)} chunk result files")
        
        # Load all chunk data
        all_chunks = []
        successful_chunks = 0
        failed_chunks = 0
        
        for chunk_file in chunk_files:
            try:
                chunk_path = os.path.join(chunk_results_dir, chunk_file)
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                # Only process completed chunks
                if chunk_data.get('status') == 'completed' and chunk_data.get('text'):
                    all_chunks.append(chunk_data)
                    successful_chunks += 1
                    print(f"✅ Loaded chunk {chunk_data.get('chunk_number', 0)}: {len(chunk_data.get('text', ''))} chars")
                else:
                    failed_chunks += 1
                    print(f"⏳ Skipping chunk {chunk_data.get('chunk_number', 0)}: status={chunk_data.get('status')}")
                    
            except Exception as e:
                failed_chunks += 1
                print(f"❌ Error loading chunk file {chunk_file}: {e}")
                continue
        
        if not all_chunks:
            print("❌ No completed chunks found to process")
            return ExitCodes.ERROR
        
        print(f"\n📊 Chunk loading completed:")
        print(f"   - Successful chunks: {successful_chunks}")
        print(f"   - Failed chunks: {failed_chunks}")
        print(f"   - Total chunks: {len(chunk_files)}")
        
        # Use the main app's output processor to create unified output
        print("🚀 Using main app output processor to create unified output...")
        
        try:
            # Create a simple transcription result with raw chunks
            # Let the main app's overlapping strategy handle the intelligent merging
            unified_result = {
                'success': True,
                'transcription': {
                    'segments': all_chunks,  # Pass raw chunks, let strategy handle merging
                    'text': '',  # Let strategy create final text
                    'language': 'he',
                    'duration': max([c.get('end_time', 0) for c in all_chunks]) if all_chunks else 0,
                    'metadata': {
                        'total_chunks': len(all_chunks),
                        'chunk_numbers': [c.get('chunk_number', 0) for c in all_chunks],
                        'time_range': {
                            'start': min([c.get('start_time', 0) for c in all_chunks]) if all_chunks else 0,
                            'end': max([c.get('end_time', 0) for c in all_chunks]) if all_chunks else 0
                        },
                        'model_used': all_chunks[0].get('transcription_details', {}).get('model_used', 'unknown') if all_chunks else 'unknown',
                        'engine_used': all_chunks[0].get('transcription_details', {}).get('engine_used', 'unknown') if all_chunks else 'unknown'
                    }
                }
            }
            
            # Use the main app's OutputManager directly to avoid multiple processing runs
            print("🔄 Processing unified output using main app OutputManager...")
            
            # Import the proper Pydantic model
            from src.models.speaker_models import TranscriptionResult, TranscriptionSegment
            
            # Convert chunks to proper TranscriptionSegment objects with overlapping detection
            segments = []
            for chunk in all_chunks:
                # Ensure proper spacing in text - add space at the end if needed
                text = chunk.get('text', '').strip()
                if text and not text.endswith(' '):
                    text += ' '  # Add space at the end for proper separation
                
                # Get timing information from chunk metadata
                start_time = chunk.get('start_time', 0)
                end_time = chunk.get('end_time', 0)
                
                # If timing is not available, estimate from chunk number for overlapping detection
                if start_time == 0 and end_time == 0:
                    chunk_number = chunk.get('chunk_number', 0)
                    # Estimate 30 seconds per chunk (typical chunk duration)
                    start_time = chunk_number * 30
                    end_time = start_time + 30
                
                segment = TranscriptionSegment(
                    text=text,
                    start=start_time,
                    end=end_time,
                    speaker='0',  # Default speaker
                    confidence=chunk.get('transcription_details', {}).get('confidence_score', 0.9),
                    chunk_number=chunk.get('chunk_number', 0),
                    metadata={
                        'model_used': chunk.get('transcription_details', {}).get('model_used', 'unknown'),
                        'engine_used': chunk.get('transcription_details', {}).get('engine_used', 'unknown'),
                        'original_start': chunk.get('start_time', 0),
                        'original_end': chunk.get('end_time', 0),
                        'chunk_file': chunk.get('chunk_file', '')
                    }
                )
                segments.append(segment)
            
            # Sort segments by start time to ensure proper overlapping detection
            segments.sort(key=lambda x: x.start)
            
            print(f"🔄 Created {len(segments)} segments with timing information for overlapping detection")
            if segments:
                print(f"   - First segment: {segments[0].start}s - {segments[0].end}s")
                print(f"   - Last segment: {segments[-1].start}s - {segments[-1].end}s")
                print(f"   - Total estimated duration: {segments[-1].end}s")
            
            # Create proper TranscriptionResult using Pydantic model
            # Use a valid audio file path from the first chunk or create a dummy path
            audio_file_path = all_chunks[0].get('audio_file', 'dummy_audio.wav') if all_chunks else 'dummy_audio.wav'
            
            transcription_result = TranscriptionResult(
                success=True,
                speakers={'0': segments},  # Group all segments under speaker '0'
                full_text='',  # Will be populated by OutputManager
                transcription_time=0.0,  # Not applicable for existing chunks
                model_name='merged',
                audio_file=audio_file_path,
                speaker_count=1
            )
            
            # Use OutputManager to save all formats in a single run FIRST
            result = self.app.output_manager.save_transcription(
                transcription_result,
                audio_file='merged_chunks',
                model='merged',
                engine='merged'
            )
            
            if not result:
                print(f"❌ Unified output processing failed")
                return ExitCodes.ERROR
            
            # NOW use the PROCESSED text from OutputManager directly (no duplication)
            processed_text_file = self._get_processed_text_file_path()
            print(f"📝 Using existing processed text file: {processed_text_file}")
            
            # Create a DOCX directly from the processed text file
            docx_from_text = self._create_docx_from_processed_text(processed_text_file)
            if docx_from_text:
                print(f"📄 DOCX created from processed text: {docx_from_text}")
            
            if result:
                print("🎉 Unified output processing completed successfully!")
                print(f"📁 Output saved using main app's OutputManager")
                print(f"💡 Tip: Copy text from '{processed_text_file}' and paste into Word for perfect formatting!")
                if docx_from_text:
                    print(f"💡 Tip: Or use the generated DOCX: {docx_from_text}")
                return ExitCodes.SUCCESS
            else:
                print(f"❌ Unified output processing failed")
                return ExitCodes.ERROR
                
        except Exception as e:
            print(f"❌ Error creating unified output: {e}")
            return ExitCodes.ERROR
    
    def _generate_word_ready_text(self, chunks: List[Dict[str, Any]]) -> str:
        """Generate a Word-ready text file that's perfect for copy-paste into Word"""
        try:
            # Create output directory if it doesn't exist
            output_dir = "output/word_ready"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"word_ready_transcription_{timestamp}.txt"
            filepath = os.path.join(output_dir, filename)
            
            # Create clean, formatted text perfect for Word
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("🎤 TRANSCRIPTION - READY FOR WORD\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Chunks: {len(chunks)}\n")
                f.write(f"Duration: {self._format_duration(max([c.get('end_time', 0) for c in chunks]) if chunks else 0)}\n\n")
                f.write("=" * 50 + "\n\n")
                
                # Write each chunk with clean formatting
                for i, chunk in enumerate(chunks, 1):
                    chunk_text = chunk.get('text', '').strip()
                    if not chunk_text:
                        continue
                        
                    # Apply basic punctuation improvement
                    improved_text = TextFormatter.improve_hebrew_punctuation(chunk_text)
                    
                    # Format with timestamp and clean spacing
                    start_time = chunk.get('start_time', 0)
                    end_time = chunk.get('end_time', 0)
                    
                    f.write(f"[{self._format_timestamp(start_time)} - {self._format_timestamp(end_time)}]\n")
                    f.write(f"{improved_text}\n\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("End of Transcription\n")
                f.write("Copy this text and paste into Word for perfect formatting!\n")
            
            return filepath
            
        except Exception as e:
            print(f"⚠️ Warning: Could not generate Word-ready text file: {e}")
            return "word_ready_transcription.txt"
    
    def _generate_word_ready_text_from_processed_output(self) -> str:
        """Generate Word-ready text using the PROCESSED text from OutputManager"""
        try:
            # Get the main transcription output directory from ConfigManager
            config_manager = self.app.config_manager
            directory_paths = config_manager.get_directory_paths()
            transcriptions_dir = directory_paths.get('transcriptions_dir', 'output/transcriptions')
            if not os.path.exists(transcriptions_dir):
                raise Exception("Transcriptions directory not found")
            
            # Get the latest run directory
            run_dirs = [d for d in os.listdir(transcriptions_dir) if d.startswith('run_')]
            if not run_dirs:
                raise Exception("No run directories found")
            
            latest_run = sorted(run_dirs)[-1]  # Get the most recent
            latest_run_path = os.path.join(transcriptions_dir, latest_run)
            
            # Find the transcription subdirectory
            transcription_dirs = [d for d in os.listdir(latest_run_path) if d.endswith('_chunks')]
            if not transcription_dirs:
                raise Exception("No transcription directories found")
            
            latest_transcription = transcription_dirs[0]  # Should be only one
            transcription_path = os.path.join(latest_run_path, latest_transcription)
            
            # Read the processed text file
            text_file = os.path.join(transcription_path, "transcription_merged_merged.txt")
            if not os.path.exists(text_file):
                raise Exception(f"Processed text file not found: {text_file}")
            
            # Read the processed text content
            with open(text_file, 'r', encoding='utf-8') as f:
                processed_text = f.read()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"word_ready_transcription_{timestamp}.txt"
            filepath = os.path.join(transcription_path, filename)
            
            # Create clean, formatted text perfect for Word
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("🎤 TRANSCRIPTION - READY FOR WORD\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Source: Processed and merged transcription\n")
                f.write(f"File: {os.path.basename(text_file)}\n\n")
                f.write("=" * 50 + "\n\n")
                
                # Write the processed text with proper formatting
                f.write(processed_text)
                
                f.write("\n\n" + "=" * 50 + "\n")
                f.write("End of Transcription\n")
                f.write("Copy this text and paste into Word for perfect formatting!\n")
                f.write("Note: This text has been processed and merged for optimal quality!\n")
            
            return filepath
            
        except Exception as e:
            print(f"⚠️ Warning: Could not generate Word-ready text from processed output: {e}")
            # Fallback to old method
            return self._generate_word_ready_text([])
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _format_duration(self, seconds: float) -> str:
        """Format total duration to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _get_processed_text_file_path(self) -> str:
        """Get the path to the processed text file from OutputManager - NO DUPLICATION"""
        try:
            # Get the main transcription output directory from ConfigManager
            config_manager = self.app.config_manager
            directory_paths = config_manager.get_directory_paths()
            transcriptions_dir = directory_paths.get('transcriptions_dir', 'output/transcriptions')
            if not os.path.exists(transcriptions_dir):
                raise Exception("Transcriptions directory not found")
            
            # Get the latest run directory
            run_dirs = [d for d in os.listdir(transcriptions_dir) if d.startswith('run_')]
            if not run_dirs:
                raise Exception("No run directories found")
            
            latest_run = sorted(run_dirs)[-1]  # Get the most recent
            latest_run_path = os.path.join(transcriptions_dir, latest_run)
            
            # Find the transcription subdirectory
            transcription_dirs = [d for d in os.listdir(latest_run_path) if d.endswith('_chunks')]
            if not transcription_dirs:
                raise Exception("No transcription directories found")
            
            latest_transcription = transcription_dirs[0]  # Should be only one
            transcription_path = os.path.join(latest_run_path, latest_transcription)
            
            # Get the processed text file path
            text_file = os.path.join(transcription_path, "transcription_merged_merged.txt")
            if not os.path.exists(text_file):
                raise Exception(f"Processed text file not found: {text_file}")
            
            # Verify the file has content
            with open(text_file, 'r', encoding='utf-8') as f:
                processed_text = f.read()
            
            print(f"📝 Found processed text file: {text_file}")
            print(f"   - Text length: {len(processed_text)} characters")
            print(f"   - Word count: {len(processed_text.split())} words")
            
            return text_file
            
        except Exception as e:
            print(f"⚠️ Warning: Could not access processed output: {e}")
            # Fallback to creating a basic word_ready file
            return self._generate_word_ready_text([])
    
    def _create_docx_from_processed_text(self, text_file_path: str) -> Optional[str]:
        """Create a DOCX file directly from the processed text file - NO DUPLICATION"""
        try:
            from src.output_data.formatters.docx_formatter import DocxFormatter
            
            # Get the main transcription output directory from ConfigManager
            config_manager = self.app.config_manager
            directory_paths = config_manager.get_directory_paths()
            transcriptions_dir = directory_paths.get('transcriptions_dir', 'output/transcriptions')
            if not os.path.exists(transcriptions_dir):
                raise Exception("Transcriptions directory not found")
            
            # Get the latest run directory
            run_dirs = [d for d in os.listdir(transcriptions_dir) if d.startswith('run_')]
            if not run_dirs:
                raise Exception("No run directories found")
            
            latest_run = sorted(run_dirs)[-1]  # Get the most recent
            latest_run_path = os.path.join(transcriptions_dir, latest_run)
            
            # Find the transcription subdirectory
            transcription_dirs = [d for d in os.listdir(latest_run_path) if d.endswith('_chunks')]
            if not transcription_dirs:
                raise Exception("No transcription directories found")
            
            latest_transcription = transcription_dirs[0]  # Should be only one
            output_dir = os.path.join(latest_run_path, latest_transcription)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            docx_filename = f"transcription_high_quality_{timestamp}.docx"
            docx_filepath = os.path.join(output_dir, docx_filename)
            
            # Use DocxFormatter to create DOCX directly from the processed text file
            # This eliminates the need for intermediate word_ready files
            success = DocxFormatter.create_docx_from_word_ready_text(
                text_file_path=text_file_path,
                output_docx_path=docx_filepath,
                audio_file="merged_chunks",
                model="merged",
                engine="merged"
            )
            
            if success:
                print(f"✅ DOCX created successfully from processed text: {docx_filepath}")
                print(f"   - Source: {os.path.basename(text_file_path)}")
                print(f"   - No duplicate text files created")
                return docx_filepath
            else:
                print(f"❌ Failed to create DOCX from processed text")
                return None
                
        except Exception as e:
            print(f"❌ Error creating DOCX from processed text: {e}")
            return None
    
    def _create_docx_from_word_ready_text(self, text_file_path: str) -> Optional[str]:
        """Create a DOCX file from the Word-ready text file using DocxFormatter"""
        try:
            from src.output_data.formatters.docx_formatter import DocxFormatter
            
            # Get the main transcription output directory from ConfigManager
            config_manager = self.app.config_manager
            directory_paths = config_manager.get_directory_paths()
            transcriptions_dir = directory_paths.get('transcriptions_dir', 'output/transcriptions')
            if not os.path.exists(transcriptions_dir):
                raise Exception("Transcriptions directory not found")
            
            # Get the latest run directory
            run_dirs = [d for d in os.listdir(transcriptions_dir) if d.startswith('run_')]
            if not run_dirs:
                raise Exception("No run directories found")
            
            latest_run = sorted(run_dirs)[-1]  # Get the most recent
            latest_run_path = os.path.join(transcriptions_dir, latest_run)
            
            # Find the transcription subdirectory
            transcription_dirs = [d for d in os.listdir(latest_run_path) if d.endswith('_chunks')]
            if not transcription_dirs:
                raise Exception("No transcription directories found")
            
            latest_transcription = transcription_dirs[0]  # Should be only one
            output_dir = os.path.join(latest_run_path, latest_transcription)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            docx_filename = f"transcription_high_quality_{timestamp}.docx"
            docx_filepath = os.path.join(output_dir, docx_filename)
            
            # Use DocxFormatter to create DOCX from text
            success = DocxFormatter.create_docx_from_word_ready_text(
                text_file_path=text_file_path,
                output_docx_path=docx_filepath,
                audio_file="merged_chunks",
                model="merged",
                engine="merged"
            )
            
            if success:
                print(f"✅ DOCX created successfully from Word-ready text: {docx_filepath}")
                return docx_filepath
            else:
                print(f"❌ Failed to create DOCX from Word-ready text")
                return None
                
        except Exception as e:
            print(f"⚠️ Warning: Could not create DOCX from Word-ready text: {e}")
            return None
    
    def _create_transcription_result_from_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Convert chunk data to transcription result format expected by OutputProcessor"""
        # Create segments from chunk
        segments = [{
            'start': chunk.get('start_time', 0),
            'end': chunk.get('end_time', 0),
            'text': chunk.get('text', ''),
            'speaker': '0',  # Default speaker
            'confidence': chunk.get('transcription_details', {}).get('confidence_score', 0.9)
        }]
        
        # Create transcription data structure
        transcription_data = {
            'segments': segments,
            'text': chunk.get('text', ''),
            'language': 'he',
            'duration': chunk.get('end_time', 0) - chunk.get('start_time', 0),
            'metadata': {
                'chunk_number': chunk.get('chunk_number', 0),
                'start_time': chunk.get('start_time', 0),
                'end_time': chunk.get('end_time', 0),
                'model_used': chunk.get('transcription_details', {}).get('model_used', 'unknown'),
                'engine_used': chunk.get('transcription_details', {}).get('engine_used', 'unknown'),
                'confidence_score': chunk.get('transcription_details', {}).get('confidence_score', 0.9)
            }
        }
        
        # Create transcription result structure
        transcription_result = {
            'success': True,
            'transcription': transcription_data,
            'model': chunk.get('transcription_details', {}).get('model_used', 'unknown'),
            'engine': chunk.get('transcription_details', {}).get('engine_used', 'unknown'),
            'chunk_number': chunk.get('chunk_number', 0)
        }
        
        return transcription_result
    
    def _create_unified_transcription_result_from_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create unified transcription result from all chunks"""
        # Combine all text from chunks - let the main app's overlapping strategy handle merging
        all_text = ""
        all_segments = []
        total_duration = 0
        
        for chunk in chunks:
            chunk_text = chunk.get('text', '')
            
            # Just apply basic punctuation fixing, let overlapping strategy handle the rest
            improved_text = TextFormatter.improve_hebrew_punctuation(chunk_text)
            
            all_text += improved_text + " "
            
            # Create segment for this chunk
            segment = {
                'start': chunk.get('start_time', 0),
                'end': chunk.get('end_time', 0),
                'text': improved_text,
                'speaker': '0',
                'confidence': chunk.get('transcription_details', {}).get('confidence_score', 0.9)
            }
            all_segments.append(segment)
            
            # Calculate total duration
            chunk_duration = chunk.get('end_time', 0) - chunk.get('start_time', 0)
            total_duration = max(total_duration, chunk.get('end_time', 0))
        
        # Remove trailing space and let the main app's strategy handle the rest
        all_text = all_text.strip()
        
        # Create unified transcription result
        unified_result = {
            'success': True,
            'transcription': {
                'segments': all_segments,
                'text': all_text,
                'language': 'he',
                'duration': total_duration,
                'metadata': {
                    'total_chunks': len(chunks),
                    'chunk_numbers': [c.get('chunk_number', 0) for c in chunks],
                    'time_range': {
                        'start': min([c.get('start_time', 0) for c in chunks]) if chunks else 0,
                        'end': max([c.get('end_time', 0) for c in chunks]) if chunks else 0
                    },
                    'model_used': chunks[0].get('transcription_details', {}).get('model_used', 'unknown') if chunks else 'unknown',
                    'engine_used': chunks[0].get('transcription_details', {}).get('engine_used', 'unknown') if chunks else 'unknown'
                }
            }
        }
        
        return unified_result
    

    
    def _create_input_metadata_from_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Create input metadata for the chunk"""
        return {
            'file_name': f"chunk_{chunk.get('chunk_number', 0)}_{chunk.get('start_time', 0)}s_{chunk.get('end_time', 0)}s",
            'chunk_number': chunk.get('chunk_number', 0),
            'start_time': chunk.get('start_time', 0),
            'end_time': chunk.get('end_time', 0),
            'duration': chunk.get('end_time', 0) - chunk.get('start_time', 0)
        }
    
    def handle_single_file(self, args) -> int:
        """Handle single file processing command - now skips transcription"""
        print("🔄 Processing single file (skipping transcription)...")
        
        # Check if chunk results directory exists
        chunk_results_dir = "output/chunk_results"
        if not os.path.exists(chunk_results_dir):
            print(f"❌ Chunk results directory not found: {chunk_results_dir}")
            return ExitCodes.ERROR
        
        # Load all completed chunks
        chunk_files = [f for f in os.listdir(chunk_results_dir) if f.startswith('chunk_') and f.endswith('.json')]
        if not chunk_files:
            print("❌ No chunk result files found")
            return ExitCodes.ERROR
        
        print(f"📁 Found {len(chunk_files)} chunk result files")
        
        # Process each chunk through output processor
        successful_chunks = 0
        failed_chunks = 0
        
        for chunk_file in chunk_files:
            try:
                chunk_path = os.path.join(chunk_results_dir, chunk_file)
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                # Only process completed chunks
                if chunk_data.get('status') == 'completed' and chunk_data.get('text'):
                    chunk_number = chunk_data.get('chunk_number', 0)
                    print(f"🔄 Processing chunk {chunk_number}...")
                    
                    # Create transcription result format expected by OutputProcessor
                    transcription_result = self._create_transcription_result_from_chunk(chunk_data)
                    
                    # Create input metadata
                    input_metadata = self._create_input_metadata_from_chunk(chunk_data)
                    
                    # Process output using OutputProcessor
                    result = self.app.output_processor.process_output(transcription_result, input_metadata)
                    
                    if result.get('success', False):
                        successful_chunks += 1
                        print(f"✅ Chunk {chunk_number} processed successfully")
                    else:
                        failed_chunks += 1
                        error_msg = result.get('error', 'Unknown error')
                        print(f"❌ Chunk {chunk_number} failed: {error_msg}")
                
                else:
                    print(f"⏳ Skipping chunk {chunk_data.get('chunk_number', 0)}: status={chunk_data.get('status')}")
                    
            except Exception as e:
                failed_chunks += 1
                print(f"❌ Error processing chunk file {chunk_file}: {e}")
                continue
        
        print(f"\n📊 Output processing completed:")
        print(f"   - Successful chunks: {successful_chunks}")
        print(f"   - Failed chunks: {failed_chunks}")
        print(f"   - Total chunks: {len(chunk_files)}")
        
        if successful_chunks > 0:
            print("🎉 Output processing completed successfully!")
            return ExitCodes.SUCCESS
        else:
            print("❌ Output processing failed for all chunks")
            return ExitCodes.ERROR
    
    def handle_batch(self, args) -> int:
        """Handle batch processing command - now skips transcription"""
        print("🔄 Processing batch (skipping transcription)...")
        return self.handle_process_existing_chunks(args)


class ApplicationOrchestrator:
    """Orchestrates the application lifecycle following Single Responsibility Principle"""
    
    def __init__(self):
        self.app: Optional[TranscriptionApplication] = None
        self.ui: Optional[ApplicationUI] = None
        self.command_handler: Optional[CommandHandler] = None
    
    def initialize(self, config_file: Optional[str] = None) -> None:
        """Initialize the application with dependency injection"""
        try:
            # Load configuration - use production environment
            if config_file:
                config_manager = ConfigManager(str(Path(config_file).parent), environment=Environment.PRODUCTION)
            else:
                config_manager = ConfigManager("config/environments", environment=Environment.PRODUCTION)
            
            # Initialize cleanup manager
            cleanup_manager = CleanupManager(config_manager)
            
            # Initialize transcription application with dependency injection
            self.app = TranscriptionApplication(
                config_manager=config_manager,
                cleanup_manager=cleanup_manager
            )
            
            # Initialize UI manager
            self.ui = ApplicationUI(config_manager)
            
            # Initialize command handler
            self.command_handler = CommandHandler(self.app, self.ui)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize application: {e}")
            raise
    
    def run(self, args) -> int:
        """Run the application with the given arguments"""
        try:
            if not self.app:
                raise RuntimeError("Application not initialized")
            
            with self.app:
                # Print banner
                if self.ui:
                    self.ui.print_banner()
                
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
                
                elif args.command == 'process-chunks':
                    return self._handle_process_existing_chunks(args)
                
                # If we get here, command was not recognized
                if self.ui:
                    self.ui.print_error_message(f"Unknown command: {args.command}")
                return ExitCodes.ERROR
            
        except KeyboardInterrupt:
            return self._handle_interrupt()
        except Exception as e:
            return self._handle_error(e, args.verbose)
    
    @require_component('command_handler')
    def _handle_config_info(self, config_file: Optional[str]) -> int:
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
    
    @require_component('command_handler')
    def _handle_process_existing_chunks(self, args) -> int:
        """Handle process existing chunks command with null check"""
        return self.command_handler.handle_process_existing_chunks(args)  # type: ignore
    
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
