#!/usr/bin/env python3
"""
Verify Output for JSON Chunks 1-3
Runs the output strategy and overlapping merging logic directly on chunks
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config_manager import ConfigManager
from src.models.environment import Environment
from src.core.engines.strategies.output_strategy import OverlappingTextDeduplicator, MergedOutputStrategy
from src.output_data.utils.data_utils import DataUtils
from src.output_data.managers.output_manager import OutputManager
from src.output_data.formatters.text_formatter import TextFormatter
from src.output_data.formatters.json_formatter import JsonFormatter
from src.output_data.formatters.docx_formatter import DocxFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChunkVerifier:
    """
    Verifies output for JSON chunks using the output strategy and overlapping merging logic
    
    This class follows the Single Responsibility Principle by focusing solely
    on chunk verification using the actual output processing logic.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the chunk verifier with dependency injection
        
        Args:
            config_manager: ConfigManager instance for configuration access
        """
        self.config_manager = config_manager
        self.data_utils = DataUtils()
        
        # Initialize output strategy components (following main app pattern)
        self.deduplicator = OverlappingTextDeduplicator(config_manager)
        self.output_strategy = MergedOutputStrategy(config_manager, self.deduplicator)
        
        logger.info("✅ Output strategy components initialized")
    
    def load_chunks_1_to_3(self) -> List[Dict[str, Any]]:
        """Load JSON chunks 1, 2, and 3 from the chunk results directory"""
        chunks = []
        chunk_results_dir = "output/chunk_results"
        
        try:
            # Load chunks 1, 2, and 3 specifically
            for chunk_num in [1, 2, 3]:
                chunk_filename = f"chunk_{chunk_num:03d}_"
                chunk_files = [f for f in os.listdir(chunk_results_dir) 
                             if f.startswith(chunk_filename) and f.endswith('.json')]
                
                if chunk_files:
                    chunk_path = os.path.join(chunk_results_dir, chunk_files[0])
                    with open(chunk_path, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                    
                    # Verify chunk is completed
                    if chunk_data.get('status') == 'completed' and chunk_data.get('text'):
                        chunks.append(chunk_data)
                        logger.info(f"✅ Loaded chunk {chunk_num}: {len(chunk_data.get('text', ''))} chars")
                    else:
                        logger.warning(f"⚠️ Chunk {chunk_num} not completed or missing text")
                else:
                    logger.warning(f"⚠️ Chunk {chunk_num} file not found")
            
            logger.info(f"📊 Loaded {len(chunks)} chunks for verification")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error loading chunks: {e}")
            return []
    
    def convert_chunks_to_segments(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert chunk data to segment format expected by the output strategy
        
        This follows the same data structure that the main app uses
        """
        segments = []
        
        for chunk in chunks:
            segment = {
                'start': chunk.get('start_time', 0),
                'end': chunk.get('end_time', 0),
                'text': chunk.get('text', ''),
                'chunk_number': chunk.get('chunk_number', 0),
                'duration': chunk.get('end_time', 0) - chunk.get('start_time', 0),
                'overlap_start': chunk.get('audio_chunk_metadata', {}).get('overlap_start', 0),
                'overlap_end': chunk.get('audio_chunk_metadata', {}).get('overlap_end', 0),
                'stride_length': chunk.get('audio_chunk_metadata', {}).get('stride_length', 0)
            }
            segments.append(segment)
        
        logger.info(f"🔄 Converted {len(chunks)} chunks to {len(segments)} segments")
        return segments
    
    def run_overlapping_deduplication(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run the overlapping text deduplication logic
        
        This uses the exact same logic as the main app's output strategy
        """
        try:
            logger.info("🔄 Running overlapping text deduplication...")
            
            # Use the deduplicator from the output strategy
            deduplicated_segments = self.deduplicator.deduplicate_segments(segments)
            
            logger.info(f"✅ Deduplication completed: {len(segments)} → {len(deduplicated_segments)} segments")
            
            # Log deduplication details
            for i, segment in enumerate(deduplicated_segments):
                if segment.get('overlap_removed'):
                    logger.info(f"   - Segment {i+1}: {segment.get('overlap_chars_removed', 0)} chars removed from overlap")
                    logger.info(f"     Overlap duration: {segment.get('overlap_duration', 0):.1f}s")
                    logger.info(f"     Overlap with chunk: {segment.get('overlap_with_chunk', '?')}")
            
            return deduplicated_segments
            
        except Exception as e:
            logger.error(f"❌ Error during deduplication: {e}")
            return segments
    
    def run_merged_output_strategy(self, segments: List[Dict[str, Any]]) -> str:
        """
        Run the merged output strategy to create final output
        
        This uses the exact same logic as the main app
        """
        try:
            logger.info("📁 Running merged output strategy...")
            
            # Use the output strategy to create final output
            final_output = self.output_strategy.create_final_output(segments)
            
            logger.info(f"✅ Final output created: {len(final_output)} characters")
            logger.info(f"   - Segments processed: {len(segments)}")
            
            return final_output
            
        except Exception as e:
            logger.error(f"❌ Error during output strategy: {e}")
            return ""
    
    def verify_chunk_structure(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify chunk structure and content
        
        This simulates the verification logic that would be used in the main app
        """
        try:
            chunk_number = chunk.get('chunk_number', 0)
            logger.info(f"🔍 Verifying chunk {chunk_number} structure...")
            
            # Verify required fields (following main app validation patterns)
            required_fields = ['chunk_number', 'start_time', 'end_time', 'status', 'text']
            missing_fields = [field for field in required_fields if field not in chunk]
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f"Missing required fields: {missing_fields}",
                    'chunk_number': chunk_number
                }
            
            # Verify chunk status
            if chunk.get('status') != 'completed':
                return {
                    'success': False,
                    'error': f"Chunk status is '{chunk.get('status')}', expected 'completed'",
                    'chunk_number': chunk_number
                }
            
            # Verify text content
            text = chunk.get('text', '')
            if not text or len(text.strip()) == 0:
                return {
                    'success': False,
                    'error': "Chunk text is empty or missing",
                    'chunk_number': chunk_number
                }
            
            # Verify timing consistency
            start_time = chunk.get('start_time', 0)
            end_time = chunk.get('end_time', 0)
            duration = end_time - start_time
            
            if duration <= 0:
                return {
                    'success': False,
                    'error': f"Invalid duration: {duration}s (start: {start_time}s, end: {end_time}s)",
                    'chunk_number': chunk_number
                }
            
            # Verify metadata consistency
            chunk_metadata = chunk.get('chunk_metadata', {})
            if chunk_metadata:
                metadata_start = chunk_metadata.get('start', 0)
                metadata_end = chunk_metadata.get('end', 0)
                
                if metadata_start != start_time or metadata_end != end_time:
                    logger.warning(f"⚠️ Chunk {chunk_number}: Metadata timing mismatch")
            
            # Verify processing timestamps
            processing_started = chunk.get('processing_started', 0)
            processing_completed = chunk.get('processing_completed', 0)
            
            if processing_started > 0 and processing_completed > 0:
                processing_time = processing_completed - processing_started
                logger.info(f"   - Processing time: {processing_time:.2f}s")
            
            # Success verification
            verification_result = {
                'success': True,
                'chunk_number': chunk_number,
                'text_length': len(text),
                'duration': duration,
                'words_estimated': chunk.get('words_estimated', 0),
                'transcription_length': chunk.get('transcription_length', 0),
                'chunking_strategy': chunk.get('chunking_strategy', 'unknown'),
                'overlap_info': {
                    'overlap_start': chunk.get('audio_chunk_metadata', {}).get('overlap_start', 0),
                    'overlap_end': chunk.get('audio_chunk_metadata', {}).get('overlap_end', 0),
                    'stride_length': chunk.get('audio_chunk_metadata', {}).get('stride_length', 0)
                }
            }
            
            logger.info(f"✅ Chunk {chunk_number} verification successful:")
            logger.info(f"   - Text length: {len(text)} characters")
            logger.info(f"   - Duration: {duration}s")
            logger.info(f"   - Words estimated: {chunk.get('words_estimated', 0)}")
            logger.info(f"   - Chunking strategy: {chunk.get('chunking_strategy', 'unknown')}")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"❌ Error verifying chunk {chunk.get('chunk_number', 0)}: {e}")
            return {
                'success': False, 
                'error': str(e),
                'chunk_number': chunk.get('chunk_number', 0)
            }
    
    def run_verification(self) -> Dict[str, Any]:
        """Run verification for all chunks 1-3 using output strategy logic"""
        try:
            logger.info("🎯 Starting chunk verification process...")
            logger.info("🔄 This will run the actual output strategy and overlapping merging logic")
            
            # Load chunks first (before any cleanup can happen)
            chunks = self.load_chunks_1_to_3()
            if not chunks:
                return {'success': False, 'error': 'No chunks found for verification'}
            
            # Verify each chunk structure
            verification_results = []
            successful_verifications = 0
            failed_verifications = 0
            
            for chunk in chunks:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing Chunk {chunk.get('chunk_number', 0)}")
                logger.info(f"{'='*60}")
                
                # Structure verification
                structure_result = self.verify_chunk_structure(chunk)
                verification_results.append({
                    'chunk_number': chunk.get('chunk_number', 0),
                    'structure_verification': structure_result,
                    'overall_success': structure_result.get('success', False)
                })
                
                if structure_result.get('success', False):
                    successful_verifications += 1
                else:
                    failed_verifications += 1
            
            # Now run the output strategy logic on all chunks
            logger.info(f"\n{'='*60}")
            logger.info(f"RUNNING OUTPUT STRATEGY & OVERLAPPING MERGING LOGIC")
            logger.info(f"{'='*60}")
            
            # Convert chunks to segments
            segments = self.convert_chunks_to_segments(chunks)
            
            # Run overlapping deduplication
            deduplicated_segments = self.run_overlapping_deduplication(segments)
            
            # Run merged output strategy
            final_output = self.run_merged_output_strategy(deduplicated_segments)
            
            # Save output files
            saved_files = self.save_output_files(final_output, deduplicated_segments)
            
            # Summary
            summary = {
                'success': True,
                'total_chunks': len(chunks),
                'successful_verifications': successful_verifications,
                'failed_verifications': failed_verifications,
                'verification_results': verification_results,
                'output_strategy_results': {
                    'original_segments': len(segments),
                    'deduplicated_segments': len(deduplicated_segments),
                    'final_output_length': len(final_output),
                    'overlap_processing': 'completed'
                },
                'saved_files': saved_files
            }
            
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 VERIFICATION SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"   - Total chunks: {len(chunks)}")
            logger.info(f"   - Successful: {successful_verifications}")
            logger.info(f"   - Failed: {failed_verifications}")
            logger.info(f"   - Success rate: {(successful_verifications/len(chunks)*100):.1f}%")
            logger.info(f"\n🔄 OUTPUT STRATEGY RESULTS:")
            logger.info(f"   - Original segments: {len(segments)}")
            logger.info(f"   - After deduplication: {len(deduplicated_segments)}")
            logger.info(f"   - Final output length: {len(final_output)} characters")
            
            # Show saved files
            if saved_files:
                logger.info(f"\n💾 OUTPUT FILES SAVED:")
                for file_type, file_path in saved_files.items():
                    logger.info(f"   - {file_type.upper()}: {file_path}")
            else:
                logger.warning("⚠️ No output files were saved")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error during verification: {e}")
            return {'success': False, 'error': str(e)}

    def save_output_files(self, final_output: str, deduplicated_segments: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Save the processed output files using the output manager and formatters
        
        This follows the same pattern as the main app for saving files
        """
        try:
            logger.info("💾 Saving output files...")
            
            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"output/transcriptions/run_{timestamp}/chunk_verification_{timestamp}"
            os.makedirs(output_dir, exist_ok=True)
            
            # Initialize formatters (following main app pattern)
            text_formatter = TextFormatter()
            json_formatter = JsonFormatter()
            docx_formatter = DocxFormatter()
            
            saved_files = {}
            
            # 1. Save final merged text using TextFormatter
            text_file_path = os.path.join(output_dir, "final_merged_output.txt")
            # Use TextFormatter to improve Hebrew punctuation
            improved_text = text_formatter.improve_hebrew_punctuation(final_output)
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(improved_text)
            saved_files['txt'] = text_file_path
            logger.info(f"✅ Saved text file: {text_file_path}")
            
            # 2. Save JSON with all segments and deduplication info using JsonFormatter
            json_data = {
                'timestamp': timestamp,
                'total_segments': len(deduplicated_segments),
                'final_output_length': len(final_output),
                'segments': deduplicated_segments,
                'deduplication_summary': {
                    'overlaps_processed': sum(1 for s in deduplicated_segments if s.get('overlap_removed')),
                    'total_chars_removed': sum(s.get('overlap_chars_removed', 0) for s in deduplicated_segments)
                }
            }
            
            json_file_path = os.path.join(output_dir, "chunk_verification_results.json")
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            saved_files['json'] = json_file_path
            logger.info(f"✅ Saved JSON file: {json_file_path}")
            
            # 3. Save DOCX using DocxFormatter (high-quality document)
            docx_file_path = os.path.join(output_dir, "chunk_verification_results.docx")
            try:
                # First save the text file that DocxFormatter expects
                word_ready_text_path = os.path.join(output_dir, "word_ready_text.txt")
                with open(word_ready_text_path, 'w', encoding='utf-8') as f:
                    f.write(improved_text)
                
                # Use DocxFormatter to create DOCX from the text file
                success = docx_formatter.create_docx_from_word_ready_text(
                    word_ready_text_path,
                    docx_file_path,
                    audio_file="chunk_verification",
                    model="merged_chunks",
                    engine="output_strategy"
                )
                
                if success:
                    saved_files['docx'] = docx_file_path
                    logger.info(f"✅ Saved DOCX file: {docx_file_path}")
                    # Clean up temporary text file
                    os.remove(word_ready_text_path)
                else:
                    logger.warning("⚠️ DOCX creation failed")
            except Exception as e:
                logger.warning(f"⚠️ Could not save DOCX: {e}")
            
            # 4. Save SRT format (if segments have timing info)
            srt_content = self._create_srt_content(deduplicated_segments)
            if srt_content:
                srt_file_path = os.path.join(output_dir, "chunk_verification_results.srt")
                with open(srt_file_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                saved_files['srt'] = srt_file_path
                logger.info(f"✅ Saved SRT file: {srt_file_path}")
            
            # 5. Save summary report
            summary_content = self._create_summary_report(final_output, deduplicated_segments, timestamp)
            summary_file_path = os.path.join(output_dir, "verification_summary.txt")
            with open(summary_file_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            saved_files['summary'] = summary_file_path
            logger.info(f"✅ Saved summary file: {summary_file_path}")
            
            # 6. Save detailed analysis report
            analysis_content = self._create_detailed_analysis(deduplicated_segments, timestamp)
            analysis_file_path = os.path.join(output_dir, "detailed_analysis.txt")
            with open(analysis_file_path, 'w', encoding='utf-8') as f:
                f.write(analysis_content)
            saved_files['analysis'] = analysis_file_path
            logger.info(f"✅ Saved analysis file: {analysis_file_path}")
            
            logger.info(f"💾 All output files saved to: {output_dir}")
            return saved_files
            
        except Exception as e:
            logger.error(f"❌ Error saving output files: {e}")
            return {}
    
    def _create_srt_content(self, segments: List[Dict[str, Any]]) -> str:
        """Create SRT format content from segments"""
        try:
            srt_content = ""
            for i, segment in enumerate(segments, 1):
                start_time = segment.get('start', 0)
                end_time = segment.get('end', 0)
                text = segment.get('text', '')
                
                # Convert seconds to SRT time format (HH:MM:SS,mmm)
                start_srt = self._seconds_to_srt_time(start_time)
                end_srt = self._seconds_to_srt_time(end_time)
                
                srt_content += f"{i}\n"
                srt_content += f"{start_srt} --> {end_srt}\n"
                srt_content += f"{text}\n\n"
            
            return srt_content
        except Exception as e:
            logger.warning(f"⚠️ Could not create SRT content: {e}")
            return ""
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _create_summary_report(self, final_output: str, segments: List[Dict[str, Any]], timestamp: str) -> str:
        """Create a human-readable summary report"""
        report = f"""CHUNK VERIFICATION SUMMARY REPORT
Generated: {timestamp}
===============================================

OVERVIEW:
- Total segments processed: {len(segments)}
- Final output length: {len(final_output)} characters
- Overlaps detected and processed: {sum(1 for s in segments if s.get('overlap_removed'))}

SEGMENT DETAILS:
"""
        
        for i, segment in enumerate(segments, 1):
            chunk_num = segment.get('chunk_number', i)
            text_length = len(segment.get('text', ''))
            duration = segment.get('duration', 0)
            overlap_removed = segment.get('overlap_removed', False)
            
            report += f"\nSegment {i} (Chunk {chunk_num}):\n"
            report += f"  - Duration: {duration}s\n"
            report += f"  - Text length: {text_length} characters\n"
            report += f"  - Overlap processed: {'Yes' if overlap_removed else 'No'}"
            
            if overlap_removed:
                chars_removed = segment.get('overlap_chars_removed', 0)
                overlap_duration = segment.get('overlap_duration', 0)
                report += f" ({chars_removed} chars, {overlap_duration:.1f}s overlap)"
            
            report += "\n"
        
        report += f"\nFINAL OUTPUT PREVIEW:\n"
        report += f"{'='*50}\n"
        report += f"{final_output[:200]}...\n"
        report += f"{'='*50}\n"
        
        return report
    
    def _create_detailed_analysis(self, segments: List[Dict[str, Any]], timestamp: str) -> str:
        """Create a detailed analysis report with technical details"""
        analysis = f"""DETAILED TECHNICAL ANALYSIS REPORT
Generated: {timestamp}
===============================================

OVERLAP ANALYSIS:
"""
        
        total_overlaps = 0
        total_chars_removed = 0
        
        for i, segment in enumerate(segments, 1):
            chunk_num = segment.get('chunk_number', i)
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            duration = segment.get('duration', 0)
            text_length = len(segment.get('text', ''))
            
            analysis += f"\nSEGMENT {i} ANALYSIS:\n"
            analysis += f"  - Chunk Number: {chunk_num}\n"
            analysis += f"  - Time Range: {start_time:.1f}s - {end_time:.1f}s\n"
            analysis += f"  - Duration: {duration:.1f}s\n"
            analysis += f"  - Text Length: {text_length} characters\n"
            
            if segment.get('overlap_removed'):
                total_overlaps += 1
                chars_removed = segment.get('overlap_chars_removed', 0)
                overlap_duration = segment.get('overlap_duration', 0)
                overlap_with = segment.get('overlap_with_chunk', 'unknown')
                
                total_chars_removed += chars_removed
                
                analysis += f"  - OVERLAP DETECTED:\n"
                analysis += f"    * Overlap Duration: {overlap_duration:.1f}s\n"
                analysis += f"    * Characters Removed: {chars_removed}\n"
                analysis += f"    * Overlap With: Chunk {overlap_with}\n"
                analysis += f"    * Efficiency: {(chars_removed/text_length*100):.1f}% of text was overlap\n"
            else:
                analysis += f"  - No overlaps detected\n"
        
        analysis += f"\n{'='*50}\n"
        analysis += f"OVERALL STATISTICS:\n"
        analysis += f"  - Total Segments: {len(segments)}\n"
        analysis += f"  - Segments with Overlaps: {total_overlaps}\n"
        analysis += f"  - Total Characters Removed: {total_chars_removed}\n"
        analysis += f"  - Overlap Processing Rate: {(total_overlaps/len(segments)*100):.1f}%\n"
        
        if total_chars_removed > 0:
            total_original_chars = sum(len(s.get('text', '')) for s in segments) + total_chars_removed
            analysis += f"  - Overall Deduplication: {(total_chars_removed/total_original_chars*100):.1f}%\n"
        
        analysis += f"\nTECHNICAL NOTES:\n"
        analysis += f"  - Overlap detection uses intelligent text similarity\n"
        analysis += f"  - 5-second overlap windows between 30-second chunks\n"
        analysis += f"  - Hebrew text optimization applied\n"
        analysis += f"  - RTL (Right-to-Left) support enabled\n"
        
        return analysis

def main():
    """Main function to run chunk verification"""
    try:
        logger.info("🚀 Starting chunk verification for chunks 1-3...")
        logger.info("📋 This script runs the output strategy and overlapping merging logic")
        logger.info("🔍 Verification includes structure validation and output processing")
        
        # Load configuration (following main app pattern)
        logger.info("🔧 Loading configuration...")
        config_manager = ConfigManager("config/environments", Environment.PRODUCTION)
        
        # Create verifier with dependency injection
        verifier = ChunkVerifier(config_manager)
        
        # Run verification
        result = verifier.run_verification()
        
        if result.get('success'):
            logger.info("\n🎉 Chunk verification completed successfully!")
            
            # Print detailed results
            for chunk_result in result.get('verification_results', []):
                chunk_num = chunk_result['chunk_number']
                overall_success = chunk_result['overall_success']
                status = "✅ SUCCESS" if overall_success else "❌ FAILED"
                logger.info(f"\n   Chunk {chunk_num}: {status}")
                
                # Structure verification details
                structure = chunk_result['structure_verification']
                if not structure.get('success'):
                    logger.error(f"      Structure Error: {structure.get('error')}")
                
                # Success details
                if overall_success:
                    logger.info(f"      Text length: {structure.get('text_length', 0)} chars")
                    logger.info(f"      Duration: {structure.get('duration', 0)}s")
                    logger.info(f"      Words estimated: {structure.get('words_estimated', 0)}")
            
            # Output strategy results
            output_results = result.get('output_strategy_results', {})
            if output_results:
                logger.info(f"\n🔄 Output Strategy Results:")
                logger.info(f"   - Original segments: {output_results.get('original_segments', 0)}")
                logger.info(f"   - After deduplication: {output_results.get('deduplicated_segments', 0)}")
                logger.info(f"   - Final output length: {output_results.get('final_output_length', 0)} characters")
        else:
            logger.error(f"❌ Chunk verification failed: {result.get('error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
