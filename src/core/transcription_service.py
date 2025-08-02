#!/usr/bin/env python3
"""
Core transcription service
Handles the main transcription logic and orchestration
"""

from typing import Dict, Any, Generator
from src.engines.transcription_engine_factory import TranscriptionEngineFactory
from src.core.job_validator import JobValidator
from src.core.audio_file_processor import AudioFileProcessor
from src.utils.output_manager import OutputManager

class TranscriptionService:
    """Core transcription service that orchestrates the transcription process"""
    
    def __init__(self, max_payload_size: int = 200 * 1024 * 1024):
        """Initialize transcription service"""
        self.validator = JobValidator()
        self.audio_processor = AudioFileProcessor(max_payload_size)
        self.engine_factory = TranscriptionEngineFactory()
        self.output_manager = OutputManager()
    
    def transcribe(self, job: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Main transcription function following Single Responsibility Principle.
        Orchestrates the transcription process by delegating to specialized functions.
        
        Args:
            job: The job dictionary containing input parameters
            
        Yields:
            Transcription segments or error messages
        """
        # Validate input parameters
        validation_error = self.validator.validate_job_input(job)
        if validation_error:
            yield {"error": validation_error}
            return
        
        # Extract parameters
        engine = job['input'].get('engine', 'faster-whisper')
        model_name = job['input'].get('model', 'large-v2')
        is_streaming = job['input'].get('streaming', False)
        save_output = job['input'].get('save_output', True)
        
        # Prepare audio file
        temp_dir, audio_file = self.audio_processor.prepare_audio_file(job)
        if temp_dir is None:
            yield {"error": audio_file}  # audio_file contains error message
            return
        
        # Ensure audio_file is not None before proceeding
        if audio_file is None:
            yield {"error": "Failed to prepare audio file"}
            return
        
        # Perform transcription
        try:
            stream_gen = self.transcribe_core(engine, model_name, audio_file)
            
            if is_streaming:
                for entry in stream_gen:
                    yield entry
            else:
                result = [entry for entry in stream_gen]
                
                # Save output if requested
                if save_output and result:
                    try:
                        # Save as JSON
                        json_file = self.output_manager.save_transcription(
                            audio_file, result, model_name, engine
                        )
                        
                        # Save as text
                        text_content = "\n".join([seg.get('text', '') for seg in result if 'text' in seg])
                        if text_content.strip():
                            text_file = self.output_manager.save_transcription_text(
                                audio_file, text_content, model_name, engine
                            )
                        
                        # Save as Word document
                        docx_file = self.output_manager.save_transcription_docx(
                            audio_file, result, model_name, engine
                        )
                        
                        self.output_manager.log_info(f"Transcription completed and saved for {audio_file}")
                    except Exception as e:
                        self.output_manager.log_error(f"Failed to save output: {e}")
                
                yield {'result': result}
        finally:
            # Clean up temporary files
            self.audio_processor.cleanup_temp_files(temp_dir)
    
    def transcribe_core(self, engine: str, model_name: str, audio_file: str) -> Generator[Dict[str, Any], None, None]:
        """
        Core transcription function using Strategy Pattern for engine selection.
        Follows Open/Closed Principle - open for extension, closed for modification.
        
        Args:
            engine: The transcription engine to use
            model_name: The model name to use
            audio_file: Path to the audio file
            
        Yields:
            Transcription segments
        """
        print('Transcribing...')
        
        try:
            # Use Strategy Pattern to get the appropriate engine
            transcription_engine = self.engine_factory.get_engine(engine, model_name)
            
            # Perform transcription using the selected engine
            if engine == 'faster-whisper':
                segs, _ = transcription_engine.transcribe(audio_file, language='he', word_timestamps=True)
            elif engine == 'stable-whisper':
                segs = transcription_engine.transcribe(audio_file, language='he', word_timestamps=True)
            else:
                raise ValueError(f"Unsupported engine: {engine}")
            
            # Process segments
            for s in segs:
                words = []
                for w in s.words:
                    words.append({
                        'start': w.start,
                        'end': w.end,
                        'word': w.word,
                        'probability': w.probability
                    })
                
                seg = {
                    'id': s.id,
                    'seek': s.seek,
                    'start': s.start,
                    'end': s.end,
                    'text': s.text,
                    'avg_logprob': s.avg_logprob,
                    'compression_ratio': s.compression_ratio,
                    'no_speech_prob': s.no_speech_prob,
                    'words': words
                }
                
                yield seg
                
        except Exception as e:
            print(f"Error during transcription: {e}")
            yield {"error": f"Transcription failed: {e}"} 