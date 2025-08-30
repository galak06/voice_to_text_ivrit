#!/usr/bin/env python3
"""
Full File Test
Processes the complete WAV file with pyannote.audio - no chunking, no overlap
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_full_file_processing():
    """Process the complete WAV file with pyannote.audio"""
    logger.info("🎯 Full File Test: Process Complete WAV File")
    logger.info("💡 No chunking, no overlap - direct processing")
    
    try:
        start_time = time.time()
        logger.info(f"🚀 Test started at: {datetime.now().strftime('%H:%M:%S')}")
        
        # Full audio file path
        audio_file = "examples/audio/voice/פגישה שלישית.wav"
        
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Get file info
        file_size = os.path.getsize(audio_file)
        file_size_mb = file_size / (1024 * 1024)
        
        logger.info(f"📁 Audio file: {audio_file}")
        logger.info(f"📊 File size: {file_size_mb:.1f} MB")
        
        # Process with pyannote.audio
        hf_token = os.getenv('HF_TOKEN')
        if not hf_token:
            raise ValueError("HF_TOKEN not found - cannot run pyannote.audio")
        
        logger.info("🔑 HF_TOKEN found, creating pipeline...")
        
        from pyannote.audio import Pipeline
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        logger.info("✅ Pipeline created successfully")
        
        # Process the full file with timeout
        logger.info(f"🔄 Processing full audio file...")
        logger.info("⏱️ This will take several minutes for a large file...")
        logger.info("⏰ Timeout set to 5 minutes to prevent hanging")
        logger.info("💡 Progress will be shown as processing continues")
        
        # Set up timeout mechanism
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Processing timed out after 5 minutes")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(300)  # 5 minutes = 300 seconds
        
        try:
            # Start processing with timeout
            logger.info("🔄 Starting audio processing...")
            start_processing = time.time()
            
            # Show progress updates every 30 seconds
            def show_progress():
                while True:
                    time.sleep(30)  # Update every 30 seconds
                    elapsed = time.time() - start_processing
                    remaining = 300 - elapsed  # 5 minutes = 300 seconds
                    
                    if remaining <= 0:
                        break
                    
                    logger.info(f"⏱️ Processing... {elapsed:.0f}s elapsed, {remaining:.0f}s remaining")
            
            # Start progress thread
            import threading
            progress_thread = threading.Thread(target=show_progress, daemon=True)
            progress_thread.start()
            
            diarization = pipeline(audio_file)
            signal.alarm(0)  # Cancel timeout
            logger.info("✅ Processing completed within timeout")
        except TimeoutError:
            signal.alarm(0)
            raise TimeoutError("Processing timed out after 5 minutes - file may be too large")
        
        processing_time = time.time() - start_time
        
        # Extract speaker information
        speakers = {}
        total_segments = 0
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if speaker not in speakers:
                speakers[speaker] = []
            
            segment_info = {
                'start': turn.start,
                'end': turn.end,
                'duration': turn.end - turn.start
            }
            speakers[speaker].append(segment_info)
            total_segments += 1
        
        # Show results
        logger.info(f"✅ Full file processing completed in {processing_time:.2f} seconds!")
        logger.info(f"🎤 Detected {len(speakers)} speakers:")
        logger.info(f"📊 Total segments: {total_segments}")
        
        for speaker, segments in speakers.items():
            total_duration = sum(seg['duration'] for seg in segments)
            total_minutes = total_duration / 60
            logger.info(f"   {speaker}: {len(segments)} segments, {total_minutes:.1f} minutes total")
        
        # Save results
        output_file = f"full_file_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'test_name': 'Full File Processing',
                'audio_file': audio_file,
                'file_size_mb': file_size_mb,
                'speakers_detected': len(speakers),
                'total_segments': total_segments,
                'speaker_details': speakers,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"💾 Results saved to: {output_file}")
        logger.info("✅ Full file processing test passed!")
        logger.info("🎯 Complete file processed - no chunking, no overlap")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Full file processing failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Full File Test Starting")
    logger.info("=" * 60)
    
    success = test_full_file_processing()
    
    if success:
        logger.info("🎉 SUCCESS! Full file processing completed")
        return 0
    else:
        logger.error("❌ FAILED! Full file processing failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
