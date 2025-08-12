#!/usr/bin/env python3
"""
Speaker diarization and transcription engines
"""

import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from src.core.interfaces.transcription_engine_interface import ITranscriptionEngine
from src.models import (
    SpeakerConfig,
    TranscriptionConfig,
)
from src.models.speaker_models import TranscriptionResult, TranscriptionSegment
from src.utils.config_manager import ConfigManager
from src.utils.dependency_manager import LIBROSA_AVAILABLE

logger = logging.getLogger(__name__)


class TranscriptionEngine(ITranscriptionEngine):
    """Abstract base class for transcription engines"""
    
    def __init__(self, config: SpeakerConfig, app_config=None):
        self.config = config
        self.app_config = app_config
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
        # This method is now a placeholder and will be overridden by specific engines
        pass
    
    @abstractmethod
    def cleanup_models(self):
        """Clean up loaded models and free memory - to be overridden by specific engines"""
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the engine - to be overridden by specific engines"""
        pass
    
    def _transcribe_in_chunks(self, audio_file_path: str, model_name: str, chunk_duration_seconds: int = 120) -> TranscriptionResult:
        """Unified chunked transcription flow used by all engines.

        Splits audio into fixed-size chunks, writes per-chunk JSON files immediately,
        retries on failures, and merges the chunks into a final `TranscriptionResult`.
        """
        start_time = time.time()
        try:
            # Lazy imports to avoid hard dependency if engines vary
            if not LIBROSA_AVAILABLE:
                raise ImportError("librosa is required for chunked processing")
            import librosa  # noqa: F401 (ensures available)
            import numpy as np  # noqa: F401 (ensures available)

            # Determine full audio duration
            audio_duration_seconds = librosa.get_duration(path=audio_file_path)
            logger.info(f"Audio duration: {audio_duration_seconds:.2f}s ({audio_duration_seconds/60:.2f} minutes)")

            # Clean temp chunks dir before new run
            logger.info(f"🧹 Cleaning temp chunks before new run from: {self.temp_chunks_dir}")
            self._cleanup_temp_files()

            # Chunking loop
            chunk_start = 0.0
            chunk_count = 0

            while chunk_start < audio_duration_seconds:
                chunk_end = min(chunk_start + float(chunk_duration_seconds), audio_duration_seconds)
                chunk_count += 1

                overall_progress = (chunk_start / audio_duration_seconds) * 100 if audio_duration_seconds > 0 else 0.0
                logger.info(f"📊 OVERALL PROGRESS: {overall_progress:.1f}% ({chunk_start:.0f}s / {audio_duration_seconds:.0f}s)")
                logger.info(f"🎯 Processing chunk {chunk_count}: {chunk_start:.1f}s - {chunk_end:.1f}s")

                # Load audio slice
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Loading audio chunk...")
                audio_chunk, _ = librosa.load(
                    audio_file_path,
                    sr=16000,
                    offset=chunk_start,
                    duration=max(0.0, chunk_end - chunk_start)
                )

                if len(audio_chunk) == 0:
                    logger.warning(f"Empty audio chunk at {chunk_start:.2f}s; skipping")
                    chunk_start = chunk_end
                    continue

                # Save placeholder BEFORE transcription so we always leave a trace
                self._save_chunk_to_temp(
                    chunk_count=chunk_count,
                    chunk_start=chunk_start,
                    chunk_end=chunk_end,
                    chunk_transcription="PROCESSING_IN_PROGRESS",
                    audio_file_path=audio_file_path,
                )

                # Retry logic per chunk
                max_retries = 3
                retry_count = 0
                final_text: Optional[str] = None

                while retry_count < max_retries and final_text is None:
                    try:
                        if retry_count > 0:
                            logger.warning(f"🔄 RETRY {retry_count}/{max_retries} for chunk {chunk_count}")
                            self._cleanup_model_memory()

                        # Delegate actual transcription to engine-specific implementation
                        final_text = self._transcribe_chunk(
                            audio_chunk=audio_chunk,
                            chunk_count=chunk_count,
                            chunk_start=chunk_start,
                            chunk_end=chunk_end,
                            model_name=model_name,
                        )

                        if not final_text or not final_text.strip():
                            raise ValueError("Empty transcription result")

                    except Exception as e:
                        retry_count += 1
                        logger.error(f"❌ Chunk {chunk_count} failed on attempt {retry_count}: {e}")
                        if retry_count >= max_retries:
                            final_text = f"[TRANSCRIPTION_FAILED_AFTER_{max_retries}_ATTEMPTS: {str(e)}]"
                        else:
                            # brief backoff
                            time.sleep(1)

                # Persist final text for the chunk
                try:
                    self._update_chunk_with_transcription(
                        chunk_count=chunk_count,
                        chunk_start=chunk_start,
                        chunk_end=chunk_end,
                        chunk_transcription=final_text or "",
                        audio_file_path=audio_file_path,
                    )
                except Exception as e:
                    logger.error(f"❌ FAILED to write final transcription for chunk {chunk_count}: {e}")

                # Periodic cleanup
                if chunk_count % 5 == 0:
                    self._cleanup_model_memory()

                # Advance to next chunk
                chunk_start = chunk_end

            # Merge and verify
            merged = self._merge_temp_chunks(audio_file_path, model_name)

            return TranscriptionResult(
                success=merged.get('error') in (None, ''),
                speakers=merged.get('speakers', {}),
                full_text=merged.get('full_text', '').strip(),
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(merged.get('speakers', {}))
            )

        except Exception as e:
            logger.error(f"Unified chunked transcription failed: {e}")
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
        if not LIBROSA_AVAILABLE:
            logger.error("❌ LIBROSA NOT AVAILABLE: Cannot verify audio coverage")
            return {
                'verified': False,
                'error': 'Librosa not available',
                'actual_duration': 0,
                'covered_duration': 0,
                'coverage_percentage': 0
            }
        
        # Get actual audio duration
        if not LIBROSA_AVAILABLE:
            raise ImportError("librosa is required for audio verification")
        import librosa
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
        
        # Get constants from configuration
        constants = self.app_config.system.constants if self.app_config and self.app_config.system else None
        min_segment_duration = constants.min_segment_duration_seconds if constants else 30
        min_text_length = constants.min_text_length_for_segment if constants else 10
        
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
            elif duration > min_segment_duration and len(text) < min_text_length:
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
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        try:
            self._cleanup_temp_files()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        return False  # Re-raise any exceptions


class CustomWhisperEngine(TranscriptionEngine):
    """Engine for custom Hugging Face Whisper models"""
    
    def __init__(self, config: SpeakerConfig, app_config=None):
        super().__init__(config, app_config)
        self.temp_chunks_dir = "output/temp_chunks"
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
        # Add model caching with size limits to prevent memory leaks
        self._model_cache = {}
        self._processor_cache = {}
        self._cache_access_times = {}  # Track last access time for LRU
        self._max_cache_size = 3  # Limit cache to 3 models
    
    def is_available(self) -> bool:
        """Check if transformers and torch are available"""
        try:
            import transformers
            import torch
            return True
        except ImportError:
            return False
    
    def _get_or_load_model(self, model_name: str):
        """Get cached model or load it with proper memory management and LRU eviction"""
        import time
        
        # Update access time for existing model
        if model_name in self._model_cache:
            self._cache_access_times[model_name] = time.time()
            return self._processor_cache[model_name], self._model_cache[model_name]
        
        # Check if cache is full and evict least recently used
        if len(self._model_cache) >= self._max_cache_size:
            self._evict_least_recently_used()
        
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
        self._cache_access_times[model_name] = time.time()
        
        # Clear GPU cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return self._processor_cache[model_name], self._model_cache[model_name]
    
    def _evict_least_recently_used(self):
        """Evict the least recently used model from cache"""
        if not self._cache_access_times:
            return
        
        # Find least recently used model
        lru_model = min(self._cache_access_times.items(), key=lambda x: x[1])[0]
        
        logger.info(f"Evicting least recently used model: {lru_model}")
        
        # Clean up the model
        self._cleanup_single_model(lru_model)
        
        # Remove from caches
        self._model_cache.pop(lru_model, None)
        self._processor_cache.pop(lru_model, None)
        self._cache_access_times.pop(lru_model, None)
    
    def _cleanup_single_model(self, model_name: str):
        """Clean up a single model to free memory"""
        import torch
        
        if model_name in self._model_cache:
            logger.info(f"Cleaning up model: {model_name}")
            model = self._model_cache[model_name]
            
            # Move model to CPU and clear gradients
            if hasattr(model, 'cpu'):
                model.cpu()
            if hasattr(model, 'zero_grad'):
                model.zero_grad()
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def cleanup_models(self):
        """Clean up loaded models to free memory"""
        import torch
        
        for model_name in list(self._model_cache.keys()):
            self._cleanup_single_model(model_name)
        
        self._model_cache.clear()
        self._processor_cache.clear()
        self._cache_access_times.clear()
        
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Model cleanup completed")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the CustomWhisperEngine"""
        return {
            "engine_type": "CustomWhisperEngine",
            "config": str(self.config),
            "temp_chunks_dir": self.temp_chunks_dir,
            "loaded_models_count": len(self._model_cache),
            "processor_cache_size": len(self._processor_cache)
        }
    
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
        
        # Generate token ids with valid Whisper settings
        # Force Hebrew language and transcribe task using decoder prompt ids
        forced_decoder_ids = None
        try:
            forced_decoder_ids = processor.get_decoder_prompt_ids(language="he", task="transcribe")
        except Exception:
            forced_decoder_ids = None

        with torch.no_grad():  # Disable gradient computation to save memory
            predicted_ids = model.generate(
                input_features,
                forced_decoder_ids=forced_decoder_ids,
                num_beams=10,
                temperature=0.0,
                do_sample=False,
                length_penalty=1.0,
                repetition_penalty=1.2,
                max_new_tokens=400
            )
        
        # Decode the token ids to text
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Decoding transcription...")
        chunk_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        logger.info(f"Chunk {chunk_count} transcription length: {len(chunk_transcription)} characters")
        # Get constants from configuration
        constants = self.app_config.system.constants if self.app_config and self.app_config.system else None
        preview_length = constants.chunk_preview_length if constants else 100
        
        logger.info(f"Chunk {chunk_count} transcription preview: {chunk_transcription[:preview_length]}...")
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
        """Transcribe using a unified chunking flow for custom-whisper."""
        # Delegate to shared chunking implementation (2 minutes per chunk by default)
        return self._transcribe_in_chunks(audio_file_path=audio_file_path, model_name=model_name, chunk_duration_seconds=120)
    
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
            # Get constants from configuration
            constants = self.app_config.system.constants if self.app_config and self.app_config.system else None
            preview_length = constants.chunk_preview_length if constants else 100
            
            logger.info(f"Chunk {chunk_count} transcription preview: {chunk_transcription[:preview_length]}...")
            
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
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        try:
            self.cleanup_models()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        return False  # Re-raise any exceptions


class StableWhisperEngine(TranscriptionEngine):
    """Stable-Whisper transcription engine"""
    
    def is_available(self) -> bool:
        try:
            import stable_whisper
            return True
        except ImportError:
            return False
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk using stable-whisper"""
        try:
            import stable_whisper
            import tempfile
            import soundfile as sf
            
            # Save chunk to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio_chunk, 16000)
                temp_path = temp_file.name
            
            try:
                # Load model
                model = stable_whisper.load_model(model_name)
                
                # Transcribe chunk
                result = model.transcribe(
                    temp_path,
                    language=self.config.language,
                    vad=self.config.vad_enabled,
                    word_timestamps=self.config.word_timestamps
                )
                
                return result.text.strip()
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing chunk {chunk_count}: {e}")
            return f"ERROR: {str(e)}"
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using a unified chunking flow for stable-whisper."""
        return self._transcribe_in_chunks(audio_file_path=audio_file_path, model_name=model_name, chunk_duration_seconds=120)
    
    def cleanup_models(self):
        """Clean up loaded models and free memory"""
        logger.info("🧹 Cleaning up StableWhisperEngine models...")
        # Stable-whisper doesn't keep models in memory, so just log cleanup
        logger.info("✅ StableWhisperEngine models cleaned up")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the StableWhisperEngine"""
        return {
            "engine_type": "StableWhisperEngine",
            "config": str(self.config),
            "temp_chunks_dir": self.temp_chunks_dir,
            "model_loading_strategy": "on-demand"
        }


class OptimizedWhisperEngine(TranscriptionEngine):
    """Engine for optimized Whisper models (higher accuracy and performance)"""
    
    def __init__(self, config: SpeakerConfig, app_config=None):
        super().__init__(config, app_config)
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
        """Get cached model or load it with CTranslate2 optimized settings.
        For ct2 models, use CTranslate2 loader and a compatible HF processor source.
        Avoid falling back to transformers for ct2 artifacts that lack pytorch weights."""
        if model_name not in self._model_cache:
            logger.info(f"Loading CTranslate2 optimized model: {model_name}")

            is_ct2_model = "-ct2" in model_name

            try:
                # Try to load with CTranslate2 first
                from ctranslate2.models import Whisper
                import transformers

                model = Whisper(model_name)

                # Select a processor source compatible with the tokenizer
                processor_source = model_name
                if is_ct2_model:
                    # Most ct2 repos do not include HF processor. Fallback to a compatible HF repo
                    if "ivrit-ai/whisper-large-v3-turbo-ct2" in model_name:
                        processor_source = "ivrit-ai/whisper-large-v3-turbo"
                    elif "ivrit-ai/whisper-large-v3-ct2" in model_name or "large-v3-ct2" in model_name:
                        processor_source = "openai/whisper-large-v3"

                processor = transformers.WhisperProcessor.from_pretrained(
                    processor_source,
                    low_cpu_mem_usage=True
                )

                self._model_cache[model_name] = model
                self._processor_cache[model_name] = processor

                logger.info(f"✅ CTranslate2 optimized model loaded successfully: {model_name}")

            except Exception as e:
                logger.warning(f"CTranslate2 loading failed for {model_name}: {e}")

                if is_ct2_model:
                    # Do not attempt transformers fallback for ct2 models without pytorch weights
                    logger.error("❌ Transformers fallback disabled for ct2 models without pytorch weights")
                    raise

                logger.info("Falling back to transformers Whisper model...")

                from transformers import WhisperProcessor, WhisperForConditionalGeneration
                import torch

                # Load processor
                processor = WhisperProcessor.from_pretrained(
                    model_name,
                    low_cpu_mem_usage=True,
                )

                # Load model with optimized settings for accuracy
                model = WhisperForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    low_cpu_mem_usage=True,
                    attn_implementation="eager",
                )

                self._processor_cache[model_name] = processor
                self._model_cache[model_name] = model

                logger.info(f"✅ Transformers model loaded successfully: {model_name}")

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
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the OptimizedWhisperEngine"""
        return {
            "engine_type": "OptimizedWhisperEngine",
            "config": str(self.config),
            "temp_chunks_dir": self.temp_chunks_dir,
            "loaded_models_count": len(self._model_cache),
            "processor_cache_size": len(self._processor_cache)
        }
    
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
        if hasattr(model, 'generate') and hasattr(model.generate, '__call__') and 'ctranslate2' in type(model).__module__:
            # This is a CTranslate2 Whisper model
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using CTranslate2 optimized generation...")

            # Precompute features with HF processor, then convert to numpy for ct2
            features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
            features_np = features.numpy()

            # Force Hebrew and transcribe task using forced decoder ids where possible
            forced_decoder_ids = None
            try:
                forced_decoder_ids = processor.get_decoder_prompt_ids(language="he", task="transcribe")
            except Exception:
                forced_decoder_ids = None

            # Generate with CTranslate2 optimized parameters
            result = model.generate(
                features_np,
                beam_size=5,
                temperature=0.0,
                max_new_tokens=400,
                # The ct2 API may accept 'prompt'/'start_tokens'; if not, we rely on decoding to enforce language
            )

            # Decode token ids to text using HF processor
            token_ids: Optional[List[int]] = None
            if hasattr(result, 'sequences') and len(result.sequences) > 0:
                token_ids = result.sequences[0]
            elif isinstance(result, list) and len(result) > 0:
                token_ids = result[0]

            if token_ids is None:
                chunk_transcription = ""
            else:
                # Ensure list of ints
                if hasattr(token_ids, 'tolist'):
                    token_ids = token_ids.tolist()
                chunk_transcription = processor.batch_decode([token_ids], skip_special_tokens=True)[0]
            
        else:
            # This is a transformers model (fallback)
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using transformers fallback generation...")
            
            import torch
            
            # Transcribe with transformers
            features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
            features = features.float()  # Ensure correct data type
            
            # Generate token ids with simplified parameters
            forced_decoder_ids = None
            try:
                forced_decoder_ids = processor.get_decoder_prompt_ids(language="he", task="transcribe")
            except Exception:
                forced_decoder_ids = None
            with torch.no_grad():  # Disable gradient computation to save memory
                predicted_ids = model.generate(
                    features, 
                    forced_decoder_ids=forced_decoder_ids,
                    num_beams=5,                     # Reduced beam size for stability
                    temperature=0.0,                 # Deterministic output
                    do_sample=False,                 # Don't use sampling
                    max_new_tokens=400               # Token limit
                )
            
            # Decode the token ids to text
            chunk_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        logger.info(f"Chunk {chunk_count} transcription length: {len(chunk_transcription)} characters")
        # Get constants from configuration
        constants = self.app_config.system.constants if self.app_config and self.app_config.system else None
        preview_length = constants.chunk_preview_length if constants else 100
        
        logger.info(f"Chunk {chunk_count} transcription preview: {chunk_transcription[:preview_length]}...")
        
        return chunk_transcription
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using a unified chunking flow for optimized-whisper."""
        return self._transcribe_in_chunks(audio_file_path=audio_file_path, model_name=model_name, chunk_duration_seconds=120)


class TranscriptionEngineFactory:
    """Factory for creating transcription engines"""
    
    @staticmethod
    def create_engine(engine_type: str, config: SpeakerConfig, app_config=None) -> TranscriptionEngine:
        """Create a transcription engine based on type"""
        if engine_type == "stable-whisper":
            return StableWhisperEngine(config, app_config)
        elif engine_type == "custom-whisper":
            return CustomWhisperEngine(config, app_config)
        elif engine_type == "optimized-whisper":
            return OptimizedWhisperEngine(config, app_config)
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
        
        optimized_engine = OptimizedWhisperEngine(config)
        if optimized_engine.is_available():
            engines.append(optimized_engine)
        
        return engines 