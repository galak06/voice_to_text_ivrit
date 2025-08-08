#!/usr/bin/env python3
"""
Transcription engines for speaker diarization
Implements Strategy Pattern for different transcription engines
"""

import logging
import time
import os
import json
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from ..models.speaker_models import SpeakerConfig, TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class TranscriptionEngine(ABC):
    """Abstract base class for transcription engines"""
    
    def __init__(self, config: SpeakerConfig):
        self.config = config
        self.temp_chunks_dir = "output/temp_chunks"
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
    
    @abstractmethod
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe audio file with speaker diarization"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available"""
        pass
    
    @abstractmethod
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk - to be implemented by each engine"""
        pass
    
    def _cleanup_model_memory(self):
        """Clean up model memory - to be overridden by engines that need it"""
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("🧹 Base memory cleanup completed")
    
    def _save_chunk_to_temp(self, chunk_count: int, chunk_start: float, chunk_end: float, 
                           chunk_transcription: str, audio_file_path: str) -> str:
        """Save chunk information to temporary file"""
        filename = f"chunk_{chunk_count:03d}_{chunk_start:.0f}s_{chunk_end:.0f}s.json"
        filepath = os.path.join(self.temp_chunks_dir, filename)
        
        chunk_data = {
            'chunk_number': chunk_count,
            'start_time': chunk_start,
            'end_time': chunk_end,
            'text': chunk_transcription,
            'word_count': len(chunk_transcription.split()),
            'status': 'processing' if chunk_transcription == "PROCESSING_IN_PROGRESS" else 'completed',
            'audio_file': audio_file_path,
            'timestamp': time.time()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 IMMEDIATE SAVE: chunk {chunk_count} written to: {filename}")
        return filepath
    
    def _update_chunk_with_transcription(self, chunk_count: int, chunk_start: float, chunk_end: float,
                                        chunk_transcription: str, audio_file_path: str) -> str:
        """Update chunk file with final transcription"""
        filename = f"chunk_{chunk_count:03d}_{chunk_start:.0f}s_{chunk_end:.0f}s.json"
        filepath = os.path.join(self.temp_chunks_dir, filename)
        
        chunk_data = {
            'chunk_number': chunk_count,
            'start_time': chunk_start,
            'end_time': chunk_end,
            'text': chunk_transcription,
            'word_count': len(chunk_transcription.split()),
            'status': 'completed',
            'audio_file': audio_file_path,
            'timestamp': time.time()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def _get_existing_chunks(self) -> List[str]:
        """Get list of existing chunk files"""
        if not os.path.exists(self.temp_chunks_dir):
            return []
        
        chunk_files = [f for f in os.listdir(self.temp_chunks_dir) if f.startswith("chunk_") and f.endswith(".json")]
        return sorted(chunk_files)
    
    def _get_last_processed_chunk(self) -> int:
        """Get the last processed chunk number"""
        chunk_files = self._get_existing_chunks()
        if not chunk_files:
            return 0
        
        # Extract chunk numbers and find the highest
        chunk_numbers = []
        for chunk_file in chunk_files:
            try:
                chunk_number = int(chunk_file.split('_')[1])
                chunk_numbers.append(chunk_number)
            except (IndexError, ValueError):
                continue
        
        return max(chunk_numbers) if chunk_numbers else 0
    
    def _merge_temp_chunks(self, audio_file_path: str, model_name: str) -> Dict[str, Any]:
        """Merge all temporary chunks into final result with 99.9% coverage verification"""
        logger.info(f"🔄 Merging {len(self._get_existing_chunks())} temporary chunks...")
        
        # CRITICAL: Verify audio coverage before merging (99.9% required)
        logger.info(f"🔍 CRITICAL VERIFICATION: Ensuring 99.9%+ coverage - no voice parts can be missed!")
        coverage_verification = self._verify_audio_coverage(audio_file_path)
        
        if not coverage_verification['verified']:
            logger.error("❌ CRITICAL ERROR: Audio coverage incomplete! Missing voice parts detected!")
            logger.error(f"❌ COVERAGE: {coverage_verification['coverage_percentage']:.3f}% < 99.9% required!")
            logger.error(f"❌ MISSING: {coverage_verification.get('missing_duration', 0):.3f}s of audio!")
            
            # Log detailed gap information
            if coverage_verification['gaps']:
                logger.error("❌ DETAILED GAPS:")
                for gap in coverage_verification['gaps']:
                    logger.error(f"   - {gap['duration']:.3f}s gap at {gap['start']:.3f}s - {gap['end']:.3f}s")
            
            # Return error with detailed information
            return {
                'speakers': {},
                'full_text': f"TRANSCRIPTION INCOMPLETE - Coverage: {coverage_verification['coverage_percentage']:.3f}% < 99.9%",
                'total_words': 0,
                'total_chunks': coverage_verification['total_chunks'],
                'merged_chunks': 0,
                'error': 'Audio coverage incomplete - 99.9% required',
                'verification': coverage_verification,
                'missing_ranges': coverage_verification['missing_ranges'],
                'missing_duration': coverage_verification.get('missing_duration', 0)
            }
        
        # Continue with normal merge process
        speakers = {}
        full_text = ""
        total_words = 0
        total_chunks = len(self._get_existing_chunks())
        merged_chunks = 0
        skipped_chunks = 0
        error_chunks = 0
        
        # Sort chunks by chunk number to ensure proper order
        chunk_files_with_numbers = []
        for chunk_file in self._get_existing_chunks():
            try:
                chunk_number = int(chunk_file.split('_')[1])
                chunk_files_with_numbers.append((chunk_number, chunk_file))
            except (IndexError, ValueError) as e:
                logger.error(f"❌ Error parsing chunk number from {chunk_file}: {e}")
                error_chunks += 1
        
        # Sort by chunk number
        chunk_files_with_numbers.sort(key=lambda x: x[0])
        
        logger.info(f"📊 Processing {len(chunk_files_with_numbers)} chunks in order...")
        
        for chunk_number, chunk_file in chunk_files_with_numbers:
            chunk_path = os.path.join(self.temp_chunks_dir, chunk_file)
            
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                chunk_text = chunk_data['text']
                chunk_start = chunk_data['start_time']
                chunk_end = chunk_data['end_time']
                chunk_words = chunk_data['word_count']
                chunk_status = chunk_data.get('status', 'completed')
                
                logger.info(f"📄 Processing chunk {chunk_number}: {chunk_file}")
                logger.info(f"   - Time: {chunk_start:.1f}s - {chunk_end:.1f}s")
                logger.info(f"   - Status: {chunk_status}")
                logger.info(f"   - Text length: {len(chunk_text)} chars")
                logger.info(f"   - Word count: {chunk_words}")
                
                if chunk_text.strip() and chunk_text != "PROCESSING_IN_PROGRESS":
                    # Create segment for this chunk
                    segment = TranscriptionSegment(
                        text=chunk_text,
                        start=chunk_start,
                        end=chunk_end,
                        speaker="Speaker 1",
                        words=None
                    )
        
                    if "Speaker 1" not in speakers:
                        speakers["Speaker 1"] = []
        
                    speakers["Speaker 1"].append(segment)
                    full_text += f"\n🎤 Speaker 1 ({chunk_start:.1f}s - {chunk_end:.1f}s):\n{chunk_text}\n"
                    total_words += chunk_words
                    merged_chunks += 1
                    
                    logger.info(f"✅ Successfully merged chunk {chunk_number}: {chunk_words} words, {len(chunk_text)} chars")
                elif chunk_status == 'processing':
                    logger.warning(f"⚠️  Chunk {chunk_number} still processing (text: {chunk_text})")
                    skipped_chunks += 1
                else:
                    logger.warning(f"⚠️  Chunk {chunk_number} has no text content (text: {chunk_text})")
                    skipped_chunks += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing chunk {chunk_number} ({chunk_file}): {e}")
                error_chunks += 1
        
        logger.info(f"📊 MERGE COMPLETE:")
        logger.info(f"   - Total chunks found: {total_chunks}")
        logger.info(f"   - Successfully merged: {merged_chunks}")
        logger.info(f"   - Skipped (processing/empty): {skipped_chunks}")
        logger.info(f"   - Errors: {error_chunks}")
        logger.info(f"   - Total segments created: {sum(len(segments) for segments in speakers.values())}")
        logger.info(f"   - Total text length: {len(full_text)} characters")
        logger.info(f"   - Total word count: {total_words} words")
        
        # Validate that we have content
        if merged_chunks == 0:
            logger.error("❌ No chunks were successfully merged!")
            return {
                'speakers': {},
                'full_text': "No transcription content available",
                'total_words': 0,
                'total_chunks': total_chunks,
                'merged_chunks': 0,
                'error': 'No chunks were successfully merged'
            }
        
        # Check for missing chunks
        if merged_chunks < total_chunks:
            logger.warning(f"⚠️  Only {merged_chunks}/{total_chunks} chunks were merged successfully")
        
        # FINAL VERIFICATION: Ensure 99.9% completeness
        merged_data = {
            'speakers': speakers,
            'full_text': full_text.strip(),
            'total_words': total_words,
            'total_chunks': total_chunks,
            'merged_chunks': merged_chunks,
            'error': None
        }
        
        final_verification = self._verify_final_completeness(audio_file_path, merged_data)
        
        if not final_verification['verified']:
            logger.error("❌ FINAL VERIFICATION FAILED: Transcription incomplete!")
            merged_data['error'] = final_verification.get('error', 'Final verification failed')
            merged_data['verification'] = final_verification
        
        merged_data['verification'] = final_verification
        
        return merged_data
    
    def _verify_audio_coverage(self, audio_file_path: str) -> Dict[str, Any]:
        """Verify that all audio is covered by chunks - CRITICAL VERIFICATION (99.9% coverage required)"""
        import librosa
        
        # Get actual audio duration
        actual_duration = librosa.get_duration(path=audio_file_path)
        logger.info(f"🔍 VERIFICATION: Audio duration = {actual_duration:.2f}s ({actual_duration/60:.1f} minutes)")
        
        # Get all chunks
        chunk_files = self._get_existing_chunks()
        if not chunk_files:
            logger.error("❌ VERIFICATION FAILED: No chunks found!")
            return {
                'verified': False,
                'error': 'No chunks found',
                'actual_duration': actual_duration,
                'covered_duration': 0,
                'coverage_percentage': 0,
                'gaps': [],
                'missing_ranges': [(0, actual_duration)]
            }
        
        # Parse chunk data
        chunks_data = []
        for chunk_file in chunk_files:
            try:
                chunk_path = os.path.join(self.temp_chunks_dir, chunk_file)
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                chunks_data.append(data)
            except Exception as e:
                logger.error(f"❌ Error reading chunk {chunk_file}: {e}")
        
        # Sort by start time
        chunks_data.sort(key=lambda x: x['start_time'])
        
        # Calculate coverage
        covered_duration = 0
        gaps = []
        missing_ranges = []
        
        # Check for gaps and calculate coverage
        for i, chunk in enumerate(chunks_data):
            chunk_duration = chunk['end_time'] - chunk['start_time']
            covered_duration += chunk_duration
            
            # Check for gaps between chunks
            if i > 0:
                prev_end = chunks_data[i-1]['end_time']
                curr_start = chunk['start_time']
                gap = curr_start - prev_end
                
                if gap > 0.1:  # Gap larger than 0.1 seconds (stricter for 99.9% coverage)
                    gaps.append({
                        'start': prev_end,
                        'end': curr_start,
                        'duration': gap,
                        'between_chunks': f"{chunks_data[i-1]['chunk_number']} and {chunk['chunk_number']}"
                    })
                    missing_ranges.append((prev_end, curr_start))
        
        # Check for missing parts at the beginning
        if chunks_data and chunks_data[0]['start_time'] > 0:
            missing_ranges.insert(0, (0, chunks_data[0]['start_time']))
            gaps.insert(0, {
                'start': 0,
                'end': chunks_data[0]['start_time'],
                'duration': chunks_data[0]['start_time'],
                'between_chunks': 'start and first chunk'
            })
        
        # Check for missing parts at the end
        if chunks_data and chunks_data[-1]['end_time'] < actual_duration:
            missing_ranges.append((chunks_data[-1]['end_time'], actual_duration))
            gaps.append({
                'start': chunks_data[-1]['end_time'],
                'end': actual_duration,
                'duration': actual_duration - chunks_data[-1]['end_time'],
                'between_chunks': 'last chunk and end'
            })
        
        coverage_percentage = (covered_duration / actual_duration) * 100
        
        # Log verification results
        logger.info(f"🔍 VERIFICATION RESULTS:")
        logger.info(f"   - Audio duration: {actual_duration:.2f}s")
        logger.info(f"   - Covered duration: {covered_duration:.2f}s")
        logger.info(f"   - Coverage: {coverage_percentage:.3f}%")
        logger.info(f"   - Total chunks: {len(chunks_data)}")
        logger.info(f"   - Gaps found: {len(gaps)}")
        
        if gaps:
            logger.warning(f"⚠️  VERIFICATION WARNING: Found {len(gaps)} gaps!")
            for gap in gaps:
                logger.warning(f"   - Gap {gap['duration']:.3f}s at {gap['start']:.3f}s - {gap['end']:.3f}s")
        
        # CRITICAL: 99.9% coverage required (much stricter)
        verified = coverage_percentage >= 99.9 and len(gaps) == 0
        
        if not verified:
            logger.error(f"❌ VERIFICATION FAILED: Coverage {coverage_percentage:.3f}% < 99.9% or gaps found!")
            logger.error(f"❌ CRITICAL: Missing {actual_duration - covered_duration:.3f}s of audio!")
        else:
            logger.info(f"✅ VERIFICATION PASSED: 99.9%+ coverage achieved!")
        
        return {
            'verified': verified,
            'actual_duration': actual_duration,
            'covered_duration': covered_duration,
            'coverage_percentage': coverage_percentage,
            'total_chunks': len(chunks_data),
            'gaps': gaps,
            'missing_ranges': missing_ranges,
            'chunks_data': chunks_data,
            'missing_duration': actual_duration - covered_duration
        }
    
    def _verify_chunk_quality(self, chunks_data: List[Dict]) -> Dict[str, Any]:
        """Verify quality of individual chunks"""
        logger.info(f"🔍 VERIFYING CHUNK QUALITY...")
        
        issues = []
        empty_chunks = []
        short_chunks = []
        processing_chunks = []
        
        for chunk in chunks_data:
            chunk_number = chunk['chunk_number']
            text = chunk['text'].strip()
            duration = chunk['end_time'] - chunk['start_time']
            status = chunk.get('status', 'unknown')
            
            # Check for empty or problematic chunks
            if not text or text == "PROCESSING_IN_PROGRESS":
                empty_chunks.append(chunk)
                issues.append(f"Chunk {chunk_number}: Empty or processing")
            
            # Check for long chunks with very little text (potential issues)
            elif duration > 30 and len(text) < 10:
                short_chunks.append(chunk)
                issues.append(f"Chunk {chunk_number}: Long duration ({duration:.1f}s) but very little text ({len(text)} chars)")
            
            # Check for still processing chunks
            elif status == 'processing':
                processing_chunks.append(chunk)
                issues.append(f"Chunk {chunk_number}: Still processing")
        
        quality_verified = len(issues) == 0
        
        logger.info(f"🔍 QUALITY VERIFICATION RESULTS:")
        logger.info(f"   - Total chunks checked: {len(chunks_data)}")
        logger.info(f"   - Empty/problematic chunks: {len(empty_chunks)}")
        logger.info(f"   - Short text chunks: {len(short_chunks)}")
        logger.info(f"   - Still processing chunks: {len(processing_chunks)}")
        logger.info(f"   - Issues found: {len(issues)}")
        
        if issues:
            logger.warning(f"⚠️  QUALITY ISSUES FOUND:")
            for issue in issues:
                logger.warning(f"   - {issue}")
        else:
            logger.info(f"✅ QUALITY VERIFICATION PASSED: All chunks have proper content!")
        
        return {
            'verified': quality_verified,
            'issues': issues,
            'empty_chunks': empty_chunks,
            'short_chunks': short_chunks,
            'processing_chunks': processing_chunks,
            'total_chunks': len(chunks_data)
        }
    
    def _verify_final_completeness(self, audio_file_path: str, merged_data: Dict) -> Dict[str, Any]:
        """Final comprehensive verification of transcription completeness (99.9% coverage required)"""
        logger.info(f"🔍 FINAL COMPLETENESS VERIFICATION (99.9% coverage required)...")
        
        # Get verification results
        coverage_verification = self._verify_audio_coverage(audio_file_path)
        
        if not coverage_verification['verified']:
            logger.error("❌ FINAL VERIFICATION FAILED: Audio coverage incomplete!")
            logger.error(f"❌ CRITICAL: Only {coverage_verification['coverage_percentage']:.3f}% coverage achieved!")
            return {
                'verified': False,
                'error': 'Audio coverage incomplete',
                'coverage_verification': coverage_verification,
                'quality_verification': None,
                'merged_data': merged_data
            }
        
        # Verify chunk quality
        quality_verification = self._verify_chunk_quality(coverage_verification['chunks_data'])
        
        if not quality_verification['verified']:
            logger.error("❌ FINAL VERIFICATION FAILED: Chunk quality issues found!")
            return {
                'verified': False,
                'error': 'Chunk quality issues',
                'coverage_verification': coverage_verification,
                'quality_verification': quality_verification,
                'merged_data': merged_data
            }
        
        # Verify merged data has content
        full_text = merged_data.get('full_text', '').strip()
        total_words = merged_data.get('total_words', 0)
        speakers = merged_data.get('speakers', {})
        
        if not full_text or total_words == 0:
            logger.error("❌ FINAL VERIFICATION FAILED: No text content in merged data!")
            return {
                'verified': False,
                'error': 'No text content in merged data',
                'coverage_verification': coverage_verification,
                'quality_verification': quality_verification,
                'merged_data': merged_data
            }
        
        # Log final verification summary
        logger.info(f"✅ FINAL VERIFICATION PASSED!")
        logger.info(f"   - Audio coverage: {coverage_verification['coverage_percentage']:.3f}% (99.9%+ required)")
        logger.info(f"   - Total chunks: {coverage_verification['total_chunks']}")
        logger.info(f"   - Total words: {total_words}")
        logger.info(f"   - Text length: {len(full_text)} characters")
        logger.info(f"   - Speakers: {len(speakers)}")
        logger.info(f"   - Missing duration: {coverage_verification.get('missing_duration', 0):.3f}s")
        
        return {
            'verified': True,
            'coverage_verification': coverage_verification,
            'quality_verification': quality_verification,
            'merged_data': merged_data,
            'summary': {
                'coverage_percentage': coverage_verification['coverage_percentage'],
                'total_chunks': coverage_verification['total_chunks'],
                'total_words': total_words,
                'text_length': len(full_text),
                'speakers_count': len(speakers),
                'missing_duration': coverage_verification.get('missing_duration', 0)
            }
        }
    
    def _cleanup_temp_files(self):
        """Clean up temporary chunk files"""
        try:
            if os.path.exists(self.temp_chunks_dir):
                for filename in os.listdir(self.temp_chunks_dir):
                    if filename.startswith("chunk_") and filename.endswith(".json"):
                        os.remove(os.path.join(self.temp_chunks_dir, filename))
                logger.info(f"Cleaned up temporary chunk files from: {self.temp_chunks_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    def __del__(self):
        """Cleanup when engine is destroyed"""
        try:
            self._cleanup_temp_files()
        except:
            pass


class CustomWhisperEngine(TranscriptionEngine):
    """Engine for custom Hugging Face Whisper models"""
    
    def __init__(self, config: SpeakerConfig):
        super().__init__(config)
        self.temp_chunks_dir = "output/temp_chunks"
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
        # Add model caching to prevent reloading
        self._model_cache = {}
        self._processor_cache = {}
    
    def is_available(self) -> bool:
        """Check if transformers and torch are available"""
        try:
            import transformers
            import torch
            return True
        except ImportError:
            return False
    
    def _get_or_load_model(self, model_name: str):
        """Get cached model or load it with proper memory management"""
        if model_name not in self._model_cache:
            logger.info(f"Loading model into cache: {model_name}")
            import torch
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            
            # Load with memory optimization
            processor = WhisperProcessor.from_pretrained(
                model_name,
                low_cpu_mem_usage=True
            )
            model = WhisperForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # Use float32 for CPU compatibility
                low_cpu_mem_usage=True,
                device_map="cpu"  # Force CPU-only processing
            )
            
            self._processor_cache[model_name] = processor
            self._model_cache[model_name] = model
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        return self._processor_cache[model_name], self._model_cache[model_name]
    
    def cleanup_models(self):
        """Clean up loaded models to free memory"""
        import torch
        
        for model_name in list(self._model_cache.keys()):
            logger.info(f"Cleaning up model: {model_name}")
            if hasattr(self._model_cache[model_name], 'cpu'):
                self._model_cache[model_name].cpu()
            del self._model_cache[model_name]
            del self._processor_cache[model_name]
        
        self._model_cache.clear()
        self._processor_cache.clear()
        
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Model cleanup completed")
    
    def _cleanup_model_memory(self):
        """Enhanced memory cleanup for custom whisper engine"""
        import torch
        import gc
        
        logger.info("🧹 Custom Whisper Engine memory cleanup...")
        
        # Force garbage collection
        gc.collect()
        
        # Clear GPU cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("🧹 GPU cache cleared")
        
        # Clear CPU cache
        if hasattr(torch, 'cpu') and torch.cuda.is_available():
            torch.cuda.synchronize()
            logger.info("🧹 CPU-GPU synchronization completed")
        
        # Log memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.info(f"🧹 Current memory usage: {memory_mb:.1f} MB")
        except ImportError:
            logger.info("🧹 Memory cleanup completed (psutil not available)")
        
        logger.info("✅ Custom Whisper Engine memory cleanup completed")
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk using custom whisper engine"""
        import torch
        
        # Get cached model
        processor, model = self._get_or_load_model(model_name)
        
        # Process audio chunk with the model
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Processing input features...")
        input_features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
        # Ensure input features are float32 for CPU compatibility
        input_features = input_features.float()
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Input features processed successfully")
        
        # Generate token ids with high-accuracy parameters
        with torch.no_grad():  # Disable gradient computation to save memory
            predicted_ids = model.generate(
                input_features, 
                language="he", 
                task="transcribe",
                num_beams=10,                    # Increased beam size for better accuracy
                temperature=0.0,                 # Deterministic output
                do_sample=False,                 # Don't use sampling
                length_penalty=1.0,              # Balanced length penalty
                repetition_penalty=1.2,          # Prevent repetition
                no_speech_threshold=0.6,         # Better speech detection
                logprob_threshold=-1.0,          # Accept lower confidence tokens
                compression_ratio_threshold=2.4, # Better compression detection
                condition_on_previous_text=True, # Use context from previous chunks
                prompt_reset_on_timestamp=True,  # Reset prompt on timestamps
                return_timestamps=True,          # Get timestamps for better segmentation
                return_segments=True,            # Return detailed segments
                return_language=True,            # Return language detection
                suppress_tokens=[-1],            # Suppress end token
                suppress_blank=True,             # Suppress blank tokens
                without_timestamps=False,        # Include timestamps
                max_initial_timestamp=1.0,       # Maximum initial timestamp
                max_new_tokens=400               # Reduced token limit to fit model constraints
            )
        
        # Decode the token ids to text
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Decoding transcription...")
        chunk_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        logger.info(f"Chunk {chunk_count} transcription length: {len(chunk_transcription)} characters")
        logger.info(f"Chunk {chunk_count} transcription preview: {chunk_transcription[:100]}...")
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Transcription decoded successfully")
        
        return chunk_transcription
    
    def _save_chunk_to_temp(self, chunk_count: int, chunk_start: float, chunk_end: float, 
                           chunk_transcription: str, audio_file_path: str) -> str:
        """Save chunk data to temporary file IMMEDIATELY"""
        try:
            chunk_data = {
                'chunk_number': chunk_count,
                'start_time': chunk_start,
                'end_time': chunk_end,
                'text': chunk_transcription.strip(),
                'word_count': len(chunk_transcription.strip().split()),
                'audio_file': audio_file_path,
                'timestamp': time.time(),
                'status': 'completed' if chunk_transcription.strip() != "PROCESSING_IN_PROGRESS" else 'processing'
            }
            
            temp_filename = f"chunk_{chunk_count:03d}_{chunk_start:.0f}s_{chunk_end:.0f}s.json"
            temp_filepath = os.path.join(self.temp_chunks_dir, temp_filename)
            
            # IMMEDIATE write with flush to ensure data is on disk
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                f.flush()  # Force write to disk
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            logger.info(f"💾 IMMEDIATE SAVE: chunk {chunk_count} written to: {temp_filename}")
            return temp_filepath
            
        except Exception as e:
            logger.error(f"❌ FAILED to save chunk {chunk_count}: {e}")
            raise
    
    def _update_chunk_with_transcription(self, chunk_count: int, chunk_start: float, chunk_end: float,
                                        chunk_transcription: str, audio_file_path: str) -> str:
        """Update existing chunk file with final transcription"""
        try:
            temp_filename = f"chunk_{chunk_count:03d}_{chunk_start:.0f}s_{chunk_end:.0f}s.json"
            temp_filepath = os.path.join(self.temp_chunks_dir, temp_filename)
            
            if os.path.exists(temp_filepath):
                # Read existing data
                with open(temp_filepath, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                # Update with final transcription
                chunk_data['text'] = chunk_transcription.strip()
                chunk_data['word_count'] = len(chunk_transcription.strip().split())
                chunk_data['status'] = 'completed'
                chunk_data['transcription_timestamp'] = time.time()
                
                # Write updated data
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                
                logger.info(f"✅ UPDATED chunk {chunk_count} with final transcription")
                return temp_filepath
            else:
                # If file doesn't exist, create new one
                return self._save_chunk_to_temp(chunk_count, chunk_start, chunk_end, chunk_transcription, audio_file_path)
                
        except Exception as e:
            logger.error(f"❌ FAILED to update chunk {chunk_count}: {e}")
            raise
    
    def _get_existing_chunks(self) -> List[str]:
        """Get list of existing chunk files"""
        chunk_files = []
        if os.path.exists(self.temp_chunks_dir):
            for filename in os.listdir(self.temp_chunks_dir):
                if filename.startswith("chunk_") and filename.endswith(".json"):
                    chunk_files.append(filename)
        return sorted(chunk_files)
    
    def _get_last_processed_chunk(self) -> int:
        """Get the number of the last processed chunk"""
        chunk_files = self._get_existing_chunks()
        if not chunk_files:
            return 0
        
        # Extract chunk number from filename (chunk_001_0s_600s.json -> 1)
        try:
            last_chunk_file = chunk_files[-1]
            chunk_number = int(last_chunk_file.split('_')[1])
            return chunk_number
        except (IndexError, ValueError):
            return 0
    
    def _merge_temp_chunks(self, audio_file_path: str, model_name: str) -> Dict[str, Any]:
        """Merge all temporary chunk files into final result with 99.9% coverage verification"""
        logger.info(f"🔄 Merging temporary chunks from: {self.temp_chunks_dir}")
        
        # CRITICAL: Verify audio coverage before merging (99.9% required)
        logger.info(f"🔍 CRITICAL VERIFICATION: Ensuring 99.9%+ coverage - no voice parts can be missed!")
        coverage_verification = self._verify_audio_coverage(audio_file_path)
        
        if not coverage_verification['verified']:
            logger.error("❌ CRITICAL ERROR: Audio coverage incomplete! Missing voice parts detected!")
            logger.error(f"❌ COVERAGE: {coverage_verification['coverage_percentage']:.3f}% < 99.9% required!")
            logger.error(f"❌ MISSING: {coverage_verification.get('missing_duration', 0):.3f}s of audio!")
            
            # Log detailed gap information
            if coverage_verification['gaps']:
                logger.error("❌ DETAILED GAPS:")
                for gap in coverage_verification['gaps']:
                    logger.error(f"   - {gap['duration']:.3f}s gap at {gap['start']:.3f}s - {gap['end']:.3f}s")
            
            # Return error with detailed information
            return {
                'speakers': {},
                'full_text': f"TRANSCRIPTION INCOMPLETE - Coverage: {coverage_verification['coverage_percentage']:.3f}% < 99.9%",
                'total_words': 0,
                'total_chunks': coverage_verification['total_chunks'],
                'merged_chunks': 0,
                'error': 'Audio coverage incomplete - 99.9% required',
                'verification': coverage_verification,
                'missing_ranges': coverage_verification['missing_ranges'],
                'missing_duration': coverage_verification.get('missing_duration', 0)
            }
        
        # Get all chunk files
        chunk_files = self._get_existing_chunks()
        
        logger.info(f"📁 Found {len(chunk_files)} chunk files to merge")
        
        # Log all chunk files for debugging
        for i, chunk_file in enumerate(chunk_files):
            logger.info(f"   {i+1:2d}. {chunk_file}")
        
        speakers: Dict[str, List[TranscriptionSegment]] = {}
        full_text = ""
        total_words = 0
        total_chunks = len(chunk_files)
        merged_chunks = 0
        skipped_chunks = 0
        error_chunks = 0
        
        # Sort chunks by chunk number to ensure proper order
        chunk_files_with_numbers = []
        for chunk_file in chunk_files:
            try:
                chunk_number = int(chunk_file.split('_')[1])
                chunk_files_with_numbers.append((chunk_number, chunk_file))
            except (IndexError, ValueError) as e:
                logger.error(f"❌ Error parsing chunk number from {chunk_file}: {e}")
                error_chunks += 1
        
        # Sort by chunk number
        chunk_files_with_numbers.sort(key=lambda x: x[0])
        
        logger.info(f"📊 Processing {len(chunk_files_with_numbers)} chunks in order...")
        
        for chunk_number, chunk_file in chunk_files_with_numbers:
            chunk_path = os.path.join(self.temp_chunks_dir, chunk_file)
            
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                chunk_text = chunk_data['text']
                chunk_start = chunk_data['start_time']
                chunk_end = chunk_data['end_time']
                chunk_words = chunk_data['word_count']
                chunk_status = chunk_data.get('status', 'completed')
                
                logger.info(f"📄 Processing chunk {chunk_number}: {chunk_file}")
                logger.info(f"   - Time: {chunk_start:.1f}s - {chunk_end:.1f}s")
                logger.info(f"   - Status: {chunk_status}")
                logger.info(f"   - Text length: {len(chunk_text)} chars")
                logger.info(f"   - Word count: {chunk_words}")
                
                if chunk_text.strip() and chunk_text != "PROCESSING_IN_PROGRESS":
                    # Create segment for this chunk
                    segment = TranscriptionSegment(
                        text=chunk_text,
                        start=chunk_start,
                        end=chunk_end,
                        speaker="Speaker 1",
                        words=None
                    )

                    if "Speaker 1" not in speakers:
                        speakers["Speaker 1"] = []

                    speakers["Speaker 1"].append(segment)
                    full_text += f"\n🎤 Speaker 1 ({chunk_start:.1f}s - {chunk_end:.1f}s):\n{chunk_text}\n"
                    total_words += chunk_words
                    merged_chunks += 1
                    
                    logger.info(f"✅ Successfully merged chunk {chunk_number}: {chunk_words} words, {len(chunk_text)} chars")
                elif chunk_status == 'processing':
                    logger.warning(f"⚠️  Chunk {chunk_number} still processing (text: {chunk_text})")
                    skipped_chunks += 1
                else:
                    logger.warning(f"⚠️  Chunk {chunk_number} has no text content (text: {chunk_text})")
                    skipped_chunks += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing chunk {chunk_number} ({chunk_file}): {e}")
                error_chunks += 1
        
        logger.info(f"📊 MERGE COMPLETE:")
        logger.info(f"   - Total chunks found: {total_chunks}")
        logger.info(f"   - Successfully merged: {merged_chunks}")
        logger.info(f"   - Skipped (processing/empty): {skipped_chunks}")
        logger.info(f"   - Errors: {error_chunks}")
        logger.info(f"   - Total segments created: {sum(len(segments) for segments in speakers.values())}")
        logger.info(f"   - Total text length: {len(full_text)} characters")
        logger.info(f"   - Total word count: {total_words} words")
        
        # Validate that we have content
        if merged_chunks == 0:
            logger.error("❌ No chunks were successfully merged!")
            return {
                'speakers': {},
                'full_text': "No transcription content available",
                'total_words': 0,
                'total_chunks': total_chunks,
                'merged_chunks': 0,
                'error': 'No chunks were successfully merged',
                'verification': coverage_verification
            }
        
        # Check for missing chunks
        if merged_chunks < total_chunks:
            logger.warning(f"⚠️  Only {merged_chunks}/{total_chunks} chunks were merged successfully")
        
        # FINAL VERIFICATION: Ensure 99.9% completeness
        merged_data = {
            'speakers': speakers,
            'full_text': full_text.strip(),
            'total_words': total_words,
            'total_chunks': total_chunks,
            'merged_chunks': merged_chunks,
            'skipped_chunks': skipped_chunks,
            'error_chunks': error_chunks
        }
        
        final_verification = self._verify_final_completeness(audio_file_path, merged_data)
        
        if not final_verification['verified']:
            logger.error("❌ FINAL VERIFICATION FAILED: Transcription incomplete!")
            merged_data['error'] = final_verification.get('error', 'Final verification failed')
            merged_data['verification'] = final_verification
        
        merged_data['verification'] = final_verification
        
        return merged_data
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using custom Hugging Face Whisper model with chunked processing for large files"""
        start_time = time.time()
        
        try:
            import torch
            import librosa
            import numpy as np
            
            logger.info(f"Loading custom Hugging Face model: {model_name}")
            
            # Use cached model loading
            processor, model = self._get_or_load_model(model_name)
            
            # Get audio duration first
            audio_info = librosa.get_duration(path=audio_file_path)
            logger.info(f"Audio duration: {audio_info:.2f} seconds ({audio_info/60:.2f} minutes)")
            
            # For very long files, we need to process in chunks
            chunk_duration = 2 * 60  # 2 minutes per chunk (much smaller for testing)
            chunk_samples = int(chunk_duration * 16000)  # 16kHz sample rate
            
            # Always clean temp chunks before starting a new run
            logger.info(f"🧹 Cleaning temp chunks before new run from: {self.temp_chunks_dir}")
            self._cleanup_temp_files()
            
            # Process audio in chunks (always start fresh)
            chunk_start = 0
            chunk_count = 0
            
            while chunk_start < audio_info:
                    chunk_end = min(chunk_start + chunk_duration, audio_info)
                    chunk_count += 1
                    
                    # Calculate overall progress
                    overall_progress = (chunk_start / audio_info) * 100
                    logger.info(f"📊 OVERALL PROGRESS: {overall_progress:.1f}% ({chunk_start:.0f}s / {audio_info:.0f}s)")
                    logger.info(f"🎯 Processing chunk {chunk_count}: {chunk_start:.1f}s - {chunk_end:.1f}s")
                    logger.info(f"⏰ Chunk {chunk_count} started at: {time.strftime('%H:%M:%S')}")
                    
                    # Load audio chunk
                    logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Loading audio chunk...")
                    audio_chunk, _ = librosa.load(
                        audio_file_path, 
                        sr=16000, 
                        offset=chunk_start, 
                        duration=chunk_end - chunk_start
                    )
                    
                    logger.info(f"Chunk {chunk_count} audio length: {len(audio_chunk)} samples ({len(audio_chunk)/16000:.1f}s)")
                    logger.info(f"Chunk {chunk_count} audio RMS: {np.sqrt(np.mean(audio_chunk**2)):.4f}")
                    logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Audio chunk loaded successfully")
                    
                    if len(audio_chunk) == 0:
                        logger.warning(f"Empty audio chunk at {chunk_start}s")
                        chunk_start = chunk_end
                        continue
                    
                    # Process audio chunk with retry mechanism
                    max_retries = 3
                    retry_count = 0
                    chunk_transcription = None
                    
                    logger.info(f"🔄 Starting chunk {chunk_count} processing with retry mechanism (max {max_retries} attempts)")
                    
                    while retry_count < max_retries and chunk_transcription is None:
                        try:
                            if retry_count > 0:
                                logger.warning(f"🔄 RETRY {retry_count}/{max_retries} for chunk {chunk_count}")
                                logger.info(f"🧹 Cleaning model memory before retry...")
                                self._cleanup_model_memory()
                                logger.info(f"🔄 Reloading model for retry attempt {retry_count + 1}...")
                                # Reload model for retry
                                processor, model = self._get_or_load_model(model_name)
                                logger.info(f"✅ Model reloaded successfully for retry")
                            else:
                                logger.info(f"🎯 First attempt for chunk {chunk_count}")
                            
                            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Processing input features...")
                            input_features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
                            # Ensure input features are float32 for CPU compatibility
                            input_features = input_features.float()
                            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Input features processed successfully")
                            
                            # Save chunk info BEFORE model generation (in case it fails)
                            logger.info(f"💾 Saving chunk {chunk_count} info BEFORE model generation...")
                            pre_generation_file = self._save_chunk_to_temp(
                                chunk_count, chunk_start, chunk_end, 
                                "PROCESSING_IN_PROGRESS", audio_file_path
                            )
                            logger.info(f"✅ Chunk {chunk_count} info saved before generation: {os.path.basename(pre_generation_file)}")
                            
                            logger.info(f"🔄 Starting model generation for chunk {chunk_count}...")
                            logger.info(f"⏱️  This may take 2-3 minutes for 10-minute audio chunks...")
                            
                            # Add progress monitoring during model generation
                            start_gen_time = time.time()
                            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Starting model generation at {time.strftime('%H:%M:%S')}")
                            
                            # Generate token ids with more detailed parameters
                            with torch.no_grad():  # Disable gradient computation to save memory
                                predicted_ids = model.generate(
                                    input_features, 
                                    language="he", 
                                    task="transcribe",
                                    num_beams=5,     # Use beam search for better quality
                                    temperature=0.0,  # Deterministic output
                                    do_sample=False,  # Don't use sampling
                                    return_timestamps=True  # Get timestamps for better segmentation
                                )
                            
                            gen_duration = time.time() - start_gen_time
                            logger.info(f"✅ Model generation completed for chunk {chunk_count}")
                            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Model generation took {gen_duration:.1f} seconds")
                            
                            # Decode the token ids to text
                            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Decoding transcription...")
                            chunk_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
                            
                            # Validate transcription result
                            if not chunk_transcription or chunk_transcription.strip() == "":
                                raise ValueError("Empty transcription result")
                            
                            logger.info(f"✅ Chunk {chunk_count} transcription successful on attempt {retry_count + 1}")
                            logger.info(f"📊 Chunk {chunk_count} retry summary: {retry_count + 1} attempt(s) needed")
                            break
                            
                        except Exception as e:
                            retry_count += 1
                            logger.error(f"❌ Chunk {chunk_count} failed on attempt {retry_count}: {e}")
                            logger.error(f"📊 Chunk {chunk_count} error details: {type(e).__name__}: {str(e)}")
                            
                            if retry_count >= max_retries:
                                logger.error(f"❌ Chunk {chunk_count} failed after {max_retries} attempts. Using fallback transcription.")
                                logger.error(f"📊 Chunk {chunk_count} final status: FAILED - using error placeholder")
                                chunk_transcription = f"[TRANSCRIPTION_FAILED_AFTER_{max_retries}_ATTEMPTS: {str(e)}]"
                            else:
                                logger.info(f"🔄 Will retry chunk {chunk_count} in 5 seconds...")
                                logger.info(f"📊 Chunk {chunk_count} retry progress: {retry_count}/{max_retries} attempts used")
                                time.sleep(5)  # Wait before retry
                    
                    logger.info(f"Chunk {chunk_count} transcription length: {len(chunk_transcription)} characters")
                    logger.info(f"Chunk {chunk_count} transcription preview: {chunk_transcription[:100]}...")
                    logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Transcription decoded successfully")
                    
                    # Log retry statistics for this chunk
                    if retry_count > 0:
                        logger.info(f"📊 CHUNK {chunk_count} RETRY STATS: {retry_count} retry attempts used")
                    else:
                        logger.info(f"📊 CHUNK {chunk_count} RETRY STATS: Completed on first attempt")
                    
                    # Update chunk file with final transcription
                    logger.info(f"💾 Updating chunk {chunk_count} with final transcription...")
                    temp_file = self._update_chunk_with_transcription(
                        chunk_count, chunk_start, chunk_end, 
                        chunk_transcription, audio_file_path
                    )
                    
                    # Verify file was written immediately
                    if os.path.exists(temp_file):
                        file_size = os.path.getsize(temp_file)
                        logger.info(f"✅ Chunk {chunk_count} FINAL transcription saved to disk:")
                        logger.info(f"   - File: {os.path.basename(temp_file)}")
                        logger.info(f"   - Size: {file_size} bytes")
                        logger.info(f"   - Segment: {chunk_start:.1f}s - {chunk_end:.1f}s")
                        logger.info(f"   - Text length: {len(chunk_transcription.strip())} characters")
                        logger.info(f"   - Word count: {len(chunk_transcription.strip().split())} words")
                    else:
                        logger.error(f"❌ FAILED to write chunk {chunk_count} to temp file!")
                    
                    # Show progress and current temp files status
                    progress_percent = (chunk_end / audio_info) * 100
                    logger.info(f"📊 Progress: {progress_percent:.1f}% ({chunk_end:.0f}s / {audio_info:.0f}s)")
                    
                    # Show current temp files status
                    current_temp_files = self._get_existing_chunks()
                    logger.info(f"📁 Current temp files: {len(current_temp_files)} chunks saved")
                    
                    # Final chunk completion log
                    chunk_duration = time.time() - start_gen_time
                    logger.info(f"🎯 CHUNK {chunk_count} COMPLETED!")
                    logger.info(f"📊 CHUNK {chunk_count} SUMMARY:")
                    logger.info(f"   - Duration: {chunk_duration:.1f} seconds")
                    logger.info(f"   - Text length: {len(chunk_transcription.strip())} characters")
                    logger.info(f"   - Word count: {len(chunk_transcription.strip().split())} words")
                    logger.info(f"   - Status: SAVED to {os.path.basename(temp_file)}")
                    logger.info(f"⏰ Chunk {chunk_count} completed at: {time.strftime('%H:%M:%S')}")
                    logger.info(f"🎯 Chunk {chunk_count} COMPLETED and SAVED!")
                    
                    chunk_start = chunk_end
                    
                    # Clear intermediate variables to free memory
                    del audio_chunk, input_features, predicted_ids, chunk_transcription
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    # Clean model memory every 5 chunks to prevent accumulation
                    if chunk_count % 5 == 0:
                        logger.info(f"🧹 Cleaning model memory after {chunk_count} chunks...")
                        self._cleanup_model_memory()
                        logger.info(f"✅ Model memory cleaned after chunk {chunk_count}")
            
            logger.info(f"Custom model transcription completed successfully - processed {chunk_count} chunks")
            
            # Merge all temporary chunks
            merged_data = self._merge_temp_chunks(audio_file_path, model_name)
            speakers = merged_data['speakers']
            full_text = merged_data['full_text']
            
            return TranscriptionResult(
                success=True,
                speakers=speakers,
                full_text=full_text.strip(),
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(speakers)
            )
            
        except Exception as e:
            logger.error(f"Custom Whisper transcription failed: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=str(e)
            )
    
    def _cleanup_model_memory(self):
        """Memory cleanup for stable whisper engine"""
        import torch
        import gc
        
        logger.info("🧹 Stable Whisper Engine memory cleanup...")
        
        # Force garbage collection
        gc.collect()
        
        # Clear GPU cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("🧹 GPU cache cleared")
        
        # Log memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.info(f"🧹 Current memory usage: {memory_mb:.1f} MB")
        except ImportError:
            logger.info("🧹 Memory cleanup completed (psutil not available)")
        
        logger.info("✅ Stable Whisper Engine memory cleanup completed")
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk using stable whisper engine"""
        import stable_whisper
        import tempfile
        import os
        
        # Create a temporary file for the audio chunk
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            import librosa
            import soundfile as sf
            
            # Save the audio chunk to temporary file
            sf.write(temp_file.name, audio_chunk, 16000)
            
            # Load model
            model = stable_whisper.load_model(model_name)
            
            # Transcribe the chunk
            result = model.transcribe(
                temp_file.name,
                language=self.config.language,
                vad=self.config.vad_enabled,
                word_timestamps=self.config.word_timestamps
            )
            
            # Clean up temporary file
            os.unlink(temp_file.name)
            
            # Extract text from result
            chunk_transcription = result.text if hasattr(result, 'text') else ""
            
            logger.info(f"Chunk {chunk_count} transcription length: {len(chunk_transcription)} characters")
            logger.info(f"Chunk {chunk_count} transcription preview: {chunk_transcription[:100]}...")
            
            return chunk_transcription
    
    def _cleanup_temp_files(self):
        """Clean up temporary chunk files"""
        try:
            if os.path.exists(self.temp_chunks_dir):
                for filename in os.listdir(self.temp_chunks_dir):
                    if filename.startswith("chunk_") and filename.endswith(".json"):
                        file_path = os.path.join(self.temp_chunks_dir, filename)
                        os.remove(file_path)
                logger.info(f"Cleaned up temporary chunk files from: {self.temp_chunks_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup_models()
        except:
            pass  # Ignore errors during cleanup


class StableWhisperEngine(TranscriptionEngine):
    """Stable-Whisper transcription engine"""
    
    def is_available(self) -> bool:
        try:
            import stable_whisper
            return True
        except ImportError:
            return False
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using stable-whisper with speaker diarization"""
        start_time = time.time()
        
        try:
            import stable_whisper
            
            # Check if model name is compatible with stable-whisper
            compatible_models = ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 
                               'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 
                               'large-v3-turbo', 'turbo']
            
            # Custom Hugging Face models (including ivrit-ai models)
            custom_models = ['ivrit-ai/whisper-large-v3']
            
            # If model name is a custom Hugging Face model, raise error to use custom engine
            if model_name in custom_models:
                raise ValueError(f"Model {model_name} requires custom-whisper engine. Use --engine custom-whisper")
            # If model name is not compatible, use a fallback
            elif model_name not in compatible_models:
                logger.warning(f"Model {model_name} not compatible with stable-whisper, using 'large-v3' as fallback")
                model_name = 'large-v3'
                model = stable_whisper.load_model(model_name)
            else:
                # Load standard stable-whisper model
                model = stable_whisper.load_model(model_name)
            
            # Transcribe with basic parameters (no speaker_labels - not supported)
            result = model.transcribe(
                audio_file_path,
                language=self.config.language,
                vad=self.config.vad_enabled,
                word_timestamps=self.config.word_timestamps
            )
            
            # Process results
            speakers: Dict[str, List[TranscriptionSegment]] = {}
            full_text = ""
            
            for idx, segment in enumerate(result.segments):
                if idx % 10 == 0:
                    logger.info(f"[PROGRESS] stable-whisper processed {idx+1} segments...")
                
                # Validate segment timing
                if segment.end <= segment.start:
                    logger.warning(f"Skipping segment {idx} with invalid timing: start={segment.start}, end={segment.end}")
                    continue
                
                # Since stable-whisper doesn't support speaker diarization, use alternating speakers
                speaker = f"Speaker {idx % 2 + 1}"  # Alternate between Speaker 1 and 2
                
                if speaker not in speakers:
                    speakers[speaker] = []
                
                # Convert words to proper format for Pydantic
                words_data = None
                if hasattr(segment, 'words') and segment.words:
                    words_data = []
                    for word in segment.words:
                        # Validate word timing
                        word_start = getattr(word, 'start', 0)
                        word_end = getattr(word, 'end', 0)
                        if word_end <= word_start:
                            logger.warning(f"Skipping word with invalid timing: start={word_start}, end={word_end}")
                            continue
                            
                        if hasattr(word, '__dict__'):
                            words_data.append(word.__dict__)
                        elif isinstance(word, dict):
                            words_data.append(word)
                        else:
                            # Convert to dict if it's a simple object
                            words_data.append({
                                'start': word_start,
                                'end': word_end,
                                'word': getattr(word, 'word', str(word))
                            })
                
                try:
                    # Create TranscriptionSegment
                    segment_data = TranscriptionSegment(
                        text=segment.text.strip(),
                        start=segment.start,
                        end=segment.end,
                        speaker=speaker,
                        words=words_data
                    )
                    
                    speakers[speaker].append(segment_data)
                    full_text += f"\n🎤 {speaker}:\n{segment.text.strip()}\n"
                except Exception as e:
                    logger.warning(f"Failed to create segment {idx}: {e}")
                    continue
            
            logger.info(f"[PROGRESS] stable-whisper finished all {len(result.segments)} segments.")
            
            return TranscriptionResult(
                success=True,
                speakers=speakers,
                full_text=full_text.strip(),
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(speakers)
            )
            
        except ImportError:
            logger.warning("stable-whisper not available")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message="stable-whisper not available"
            )
        except Exception as e:
            logger.error(f"stable-whisper error: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=str(e)
            )


class CTranslate2WhisperEngine(TranscriptionEngine):
    """Engine for CTranslate2 optimized Whisper models (higher accuracy and performance)"""
    
    def __init__(self, config: SpeakerConfig):
        super().__init__(config)
        self.temp_chunks_dir = "output/temp_chunks"
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
        # Add model caching to prevent reloading
        self._model_cache = {}
        self._processor_cache = {}
    
    def is_available(self) -> bool:
        """Check if CTranslate2 and transformers are available"""
        try:
            import ctranslate2
            import transformers
            return True
        except ImportError:
            return False
    
    def _get_or_load_model(self, model_name: str):
        """Get cached model or load it with CTranslate2 optimized settings"""
        if model_name not in self._model_cache:
            logger.info(f"Loading CTranslate2 optimized model: {model_name}")
            
            try:
                # Try to load with CTranslate2 first
                from ctranslate2.models import Whisper
                import transformers
                
                # Load the CTranslate2 optimized model
                model = Whisper(model_name)
                
                # Load the processor from transformers for audio processing
                processor = transformers.WhisperProcessor.from_pretrained(
                    model_name,
                    low_cpu_mem_usage=True
                )
                
                self._model_cache[model_name] = model
                self._processor_cache[model_name] = processor
                
                logger.info(f"✅ CTranslate2 optimized model loaded successfully: {model_name}")
                
            except Exception as e:
                logger.warning(f"CTranslate2 loading failed for {model_name}: {e}")
                logger.info("Falling back to transformers Whisper model...")
                
                # For models with model.bin instead of pytorch_model.bin, try loading with trust_remote_code
                try:
                    from transformers import WhisperProcessor, WhisperForConditionalGeneration
                    import torch
                    
                    # Load processor
                    processor = WhisperProcessor.from_pretrained(
                        model_name,
                        low_cpu_mem_usage=True,
                        trust_remote_code=True
                    )
                    
                    # Load model with optimized settings for accuracy
                    model = WhisperForConditionalGeneration.from_pretrained(
                        model_name,
                        torch_dtype=torch.float32,  # Use float32 for maximum accuracy
                        device_map="cpu",  # Force CPU usage
                        low_cpu_mem_usage=True,
                        attn_implementation="eager",  # Use eager attention for stability
                        trust_remote_code=True
                    )
                    
                    self._processor_cache[model_name] = processor
                    self._model_cache[model_name] = model
                    
                    logger.info(f"✅ Transformers model loaded successfully with trust_remote_code: {model_name}")
                    
                except Exception as e2:
                    logger.error(f"Transformers loading also failed for {model_name}: {e2}")
                    raise e2
        
        return self._processor_cache[model_name], self._model_cache[model_name]
    
    def cleanup_models(self):
        """Clean up loaded models to free memory"""
        for model_name in list(self._model_cache.keys()):
            logger.info(f"Cleaning up CTranslate2 model: {model_name}")
            model = self._model_cache[model_name]
            
            # Handle CTranslate2 models
            if hasattr(model, 'unload_model'):
                model.unload_model()
            
            del self._model_cache[model_name]
            del self._processor_cache[model_name]
        
        self._model_cache.clear()
        self._processor_cache.clear()
        logger.info("CTranslate2 model cleanup completed")
    
    def _cleanup_model_memory(self):
        """Enhanced memory cleanup for CTranslate2 engine"""
        import gc
        
        logger.info("🧹 CTranslate2 Engine memory cleanup...")
        
        # Force garbage collection
        gc.collect()
        logger.info("✅ CTranslate2 memory cleanup completed")
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk using CTranslate2 optimized settings"""
        import numpy as np
        
        # Get cached model
        processor, model = self._get_or_load_model(model_name)
        
        # Process audio chunk with the model
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Processing with CTranslate2 optimized settings...")
        
        # Convert audio to the format expected by the model
        if len(audio_chunk.shape) > 1:
            audio_chunk = np.mean(audio_chunk, axis=1)  # Convert stereo to mono
        
        # Ensure audio is float32 and normalized
        audio_chunk = audio_chunk.astype(np.float32)
        if np.max(np.abs(audio_chunk)) > 0:
            audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))
        
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Audio preprocessed successfully")
        
        # Check if this is a CTranslate2 model or transformers model
        if hasattr(model, 'generate') and hasattr(model.generate, '__call__'):
            # This is a CTranslate2 Whisper model
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using CTranslate2 optimized generation...")
            
            # Use CTranslate2 generation
            features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
            
            # Convert to numpy for CTranslate2
            features = features.numpy()
            
            # Generate with CTranslate2 optimized parameters
            result = model.generate(
                features,
                language="he",
                task="transcribe",
                beam_size=5,  # Optimized beam size
                temperature=0.0,  # Deterministic output
                max_new_tokens=400,  # Token limit
                return_scores=False,
                return_no_speech_prob=False
            )
            
            # Extract transcription from CTranslate2 result
            if hasattr(result, 'sequences') and len(result.sequences) > 0:
                chunk_transcription = result.sequences[0]
            elif isinstance(result, list) and len(result) > 0:
                chunk_transcription = result[0]
            else:
                # Fallback: try to decode the result directly
                chunk_transcription = str(result)
            
        else:
            # This is a transformers model (fallback)
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using transformers fallback generation...")
            
            import torch
            
            # Transcribe with transformers
            features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
            features = features.float()  # Ensure correct data type
            
            # Generate token ids with simplified parameters
            with torch.no_grad():  # Disable gradient computation to save memory
                predicted_ids = model.generate(
                    features, 
                    language="he", 
                    task="transcribe",
                    num_beams=5,                     # Reduced beam size for stability
                    temperature=0.0,                 # Deterministic output
                    do_sample=False,                 # Don't use sampling
                    max_new_tokens=400               # Token limit
                )
            
            # Decode the token ids to text
            chunk_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        logger.info(f"Chunk {chunk_count} transcription length: {len(chunk_transcription)} characters")
        logger.info(f"Chunk {chunk_count} transcription preview: {chunk_transcription[:100]}...")
        
        return chunk_transcription
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using CTranslate2 optimized Whisper model with chunked processing for large files"""
        start_time = time.time()
        
        try:
            import librosa
            import numpy as np
            
            logger.info(f"Loading CTranslate2 optimized model: {model_name}")
            
            # Use cached model loading
            processor, model = self._get_or_load_model(model_name)
            
            # Get audio duration first
            audio_info = librosa.get_duration(path=audio_file_path)
            logger.info(f"Audio duration: {audio_info:.2f} seconds ({audio_info/60:.1f} minutes)")
            
            # For very long files, we need to process in chunks
            chunk_duration = 2 * 60  # 2 minutes per chunk
            chunk_samples = int(chunk_duration * 16000)  # 16kHz sample rate
            
            # Always clean temp chunks before starting a new run
            logger.info(f"🧹 Cleaning temp chunks before new run from: {self.temp_chunks_dir}")
            self._cleanup_temp_files()
            
            # Process audio in chunks (always start fresh)
            chunk_start = 0
            chunk_count = 0
            
            while chunk_start < audio_info:
                chunk_end = min(chunk_start + chunk_duration, audio_info)
                chunk_count += 1
                
                # Calculate overall progress
                overall_progress = (chunk_start / audio_info) * 100
                logger.info(f"📊 OVERALL PROGRESS: {overall_progress:.1f}% ({chunk_start:.0f}s / {audio_info:.0f}s)")
                logger.info(f"🎯 Processing chunk {chunk_count}: {chunk_start:.1f}s - {chunk_end:.1f}s")
                logger.info(f"⏰ Chunk {chunk_count} started at: {time.strftime('%H:%M:%S')}")
                
                # Load audio chunk
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Loading audio chunk...")
                audio_chunk, _ = librosa.load(
                    audio_file_path, 
                    sr=16000, 
                    offset=chunk_start, 
                    duration=chunk_end - chunk_start
                )
                
                logger.info(f"Chunk {chunk_count} audio length: {len(audio_chunk)} samples ({len(audio_chunk)/16000:.1f}s)")
                logger.info(f"Chunk {chunk_count} audio RMS: {np.sqrt(np.mean(audio_chunk**2)):.4f}")
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Audio chunk loaded successfully")
                
                if len(audio_chunk) == 0:
                    logger.warning(f"Empty audio chunk at {chunk_start}s")
                    chunk_start = chunk_end
                    continue
                
                # Process audio chunk with retry mechanism
                max_retries = 3
                retry_count = 0
                chunk_transcription = None
                
                logger.info(f"🔄 Starting chunk {chunk_count} processing with retry mechanism (max {max_retries} attempts)")
                
                while retry_count < max_retries and chunk_transcription is None:
                    try:
                        if retry_count > 0:
                            logger.warning(f"🔄 RETRY {retry_count}/{max_retries} for chunk {chunk_count}")
                            logger.info(f"🧹 Cleaning model memory before retry...")
                            self._cleanup_model_memory()
                            logger.info(f"🔄 Reloading model for retry attempt {retry_count + 1}...")
                            # Reload model for retry
                            processor, model = self._get_or_load_model(model_name)
                            logger.info(f"✅ Model reloaded successfully for retry")
                        
                        # Save initial chunk placeholder
                        self._save_chunk_to_temp(chunk_count, chunk_start, chunk_end, "PROCESSING_IN_PROGRESS", audio_file_path)
                        
                        # Transcribe chunk
                        chunk_transcription = self._transcribe_chunk(audio_chunk, chunk_count, chunk_start, chunk_end, model_name)
                        
                        # Update chunk with final transcription
                        self._update_chunk_with_transcription(chunk_count, chunk_start, chunk_end, chunk_transcription, audio_file_path)
                        
                        logger.info(f"✅ Chunk {chunk_count} transcription completed successfully")
                        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Transcription saved to temp file")
                        
                    except Exception as e:
                        retry_count += 1
                        logger.error(f"❌ Chunk {chunk_count} transcription failed (attempt {retry_count}/{max_retries}): {e}")
                        
                        if retry_count >= max_retries:
                            logger.error(f"❌ Chunk {chunk_count} failed after {max_retries} attempts")
                            # Save error information
                            self._update_chunk_with_transcription(chunk_count, chunk_start, chunk_end, f"ERROR: {str(e)}", audio_file_path)
                        else:
                            logger.info(f"🔄 Retrying chunk {chunk_count} in 2 seconds...")
                            time.sleep(2)
                
                # Clean model memory every 5 chunks
                if chunk_count % 5 == 0:
                    logger.info(f"🧹 Periodic memory cleanup after {chunk_count} chunks")
                    self._cleanup_model_memory()
                
                chunk_start = chunk_end
            
            logger.info(f"🎉 All chunks processed! Merging results...")
            
            # Merge all chunks into final result
            merged_result = self._merge_temp_chunks(audio_file_path, model_name)
            
            # Create final transcription result
            return TranscriptionResult(
                success=True,
                speakers=merged_result.get('speakers', {}),
                full_text=merged_result.get('full_text', ''),
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(merged_result.get('speakers', {})),
                metadata={
                    'total_chunks': merged_result.get('total_chunks', 0),
                    'merged_chunks': merged_result.get('merged_chunks', 0),
                    'verification': merged_result.get('verification', {}),
                    'engine': 'ctranslate2-whisper'
                }
            )
            
        except Exception as e:
            logger.error(f"CTranslate2 transcription failed: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=str(e)
            )


class TranscriptionEngineFactory:
    """Factory for creating transcription engines"""
    
    @staticmethod
    def create_engine(engine_type: str, config: SpeakerConfig) -> TranscriptionEngine:
        """Create a transcription engine based on type"""
        if engine_type == "stable-whisper":
            return StableWhisperEngine(config)
        elif engine_type == "custom-whisper":
            return CustomWhisperEngine(config)
        elif engine_type == "ctranslate2-whisper":
            return CTranslate2WhisperEngine(config)
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
    
    @staticmethod
    def get_available_engines(config: SpeakerConfig) -> List[TranscriptionEngine]:
        """Get list of available engines"""
        engines = []
        
        stable_engine = StableWhisperEngine(config)
        if stable_engine.is_available():
            engines.append(stable_engine)
        
        custom_engine = CustomWhisperEngine(config)
        if custom_engine.is_available():
            engines.append(custom_engine)
        
        ctranslate2_engine = CTranslate2WhisperEngine(config)
        if ctranslate2_engine.is_available():
            engines.append(ctranslate2_engine)
        
        return engines 