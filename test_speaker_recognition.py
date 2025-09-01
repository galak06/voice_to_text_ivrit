#!/usr/bin/env python3
"""
Test script to verify speaker recognition logic works independently
Enhanced with output processing and JSON validation
"""

import sys
import os
import json
import time
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_manager import ConfigManager
from src.core.factories.speaker_service_factory import SpeakerServiceFactory
from src.output_data.managers.output_manager import OutputManager
from src.output_data.utils.data_utils import DataUtils
from src.output_data.formatters.text_formatter import TextFormatter
from src.models.transcription_results import TranscriptionResult, TranscriptionSegment, TranscriptionMetadata

def create_test_transcription_result(audio_file_path: str, text: str = "This is a test transcription for speaker recognition") -> TranscriptionResult:
    """Create a test transcription result for validation"""
    dummy_segment = TranscriptionSegment(
        start=0.0,
        end=30.0,
        text=text,
        speaker="unknown"
    )
    
    return TranscriptionResult(
        success=True,
        text=text,
        segments=[dummy_segment],
        speakers={"unknown": [dummy_segment]},
        speaker_count=1,
        metadata=TranscriptionMetadata(
            model_name="test_model",
            engine="test_engine",
            language="he",
            processing_time=1.0
        )
    )

def save_test_json_output(audio_file_path: str, transcription_result: TranscriptionResult, speaker_result: TranscriptionResult, output_dir: str = "output/chunk_results") -> str:
    """Save test JSON output with speaker integration for validation"""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract filename and create JSON filename
        audio_filename = Path(audio_file_path).stem
        json_filename = f"test_{audio_filename}.json"
        json_path = os.path.join(output_dir, json_filename)
        
        # Create comprehensive JSON data
        json_data = {
            'test_type': 'speaker_integration_validation',
            'file_name': audio_filename,
            'status': 'test_completed',
            'text': getattr(transcription_result, 'text', ''),
            'processing_completed': time.time(),
            'enhancement_applied': True,
            'enhancement_strategy': 'fast_speaker_service',
            'transcription_length': len(getattr(transcription_result, 'text', '')),
            'words_estimated': len(getattr(transcription_result, 'text', '').split()),
            'progress': {
                'stage': 'test_completed',
                'message': f'Speaker integration test completed successfully with {getattr(speaker_result, "speaker_count", 0)} speakers detected',
                'timestamp': time.time()
            },
            
            # Test transcription data
            'transcription_data': {
                'text': getattr(transcription_result, 'text', ''),
                'segments': [
                    {
                        'start': getattr(seg, 'start', 0.0),
                        'end': getattr(seg, 'end', 0.0),
                        'text': getattr(seg, 'text', ''),
                        'duration': getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                    }
                    for seg in getattr(transcription_result, 'segments', [])
                ],
                'language': 'he',
                'confidence': 0.95
            },
            
            # Speaker recognition data (the main validation point)
            'speaker_recognition': {
                'total_speakers': getattr(speaker_result, 'speaker_count', 0),
                'speaker_names': list(getattr(speaker_result, 'speakers', {}).keys()),
                'speaker_details': {}
            },
            
            # Enhanced segments with speaker info
            'segments': [
                {
                    'start': getattr(seg, 'start', 0.0),
                    'end': getattr(seg, 'end', 0.0),
                    'text': getattr(seg, 'text', ''),
                    'speaker': getattr(seg, 'speaker', 'unknown'),
                    'duration': getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                }
                for seg in getattr(speaker_result, 'segments', [])
            ],
            
            # Test metadata
            'test_metadata': {
                'test_timestamp': time.time(),
                'audio_file': audio_file_path,
                'test_purpose': 'speaker_integration_validation',
                'expected_speakers': 2,  # Based on your audio files
                'validation_status': 'pending'
            }
        }
        
        # Add detailed speaker information
        speakers = getattr(speaker_result, 'speakers', {})
        if speakers:
            for speaker_id, speaker_segments in speakers.items():
                if speaker_segments:
                    total_duration = sum(
                        getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                        for seg in speaker_segments
                    )
                    json_data['speaker_recognition']['speaker_details'][speaker_id] = {
                        'segment_count': len(speaker_segments),
                        'total_duration': total_duration,
                        'segments': [
                            {
                                'start': getattr(seg, 'start', 0.0),
                                'end': getattr(seg, 'end', 0.0),
                                'text': getattr(seg, 'text', ''),
                                'duration': getattr(seg, 'end', 0.0) - getattr(seg, 'start', 0.0)
                            }
                            for seg in speaker_segments
                        ]
                    }
        
        # Save JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"   💾 Test JSON saved: {json_filename}")
        return json_path
        
    except Exception as e:
        print(f"   ❌ Error saving test JSON: {e}")
        return None

def validate_speaker_integration(json_path: str, expected_speakers: int = 2) -> bool:
    """Validate the speaker integration in the test JSON output"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"\n🔍 Validating Speaker Integration in: {Path(json_path).name}")
        print("=" * 60)
        
        # Check basic structure
        validation_results = []
        
        # 1. Check enhancement strategy
        enhancement_strategy = json_data.get('enhancement_strategy')
        validation_results.append(('enhancement_strategy', enhancement_strategy == 'fast_speaker_service', f"Expected 'fast_speaker_service', got '{enhancement_strategy}'"))
        
        # 2. Check enhancement applied
        enhancement_applied = json_data.get('enhancement_applied')
        validation_results.append(('enhancement_applied', enhancement_applied == True, f"Expected True, got {enhancement_applied}"))
        
        # 3. Check speaker recognition data
        speaker_recognition = json_data.get('speaker_recognition', {})
        total_speakers = speaker_recognition.get('total_speakers', 0)
        validation_results.append(('total_speakers', total_speakers == expected_speakers, f"Expected {expected_speakers}, got {total_speakers}"))
        
        # 4. Check speaker names
        speaker_names = speaker_recognition.get('speaker_names', [])
        validation_results.append(('speaker_names', len(speaker_names) == expected_speakers, f"Expected {expected_speakers} speaker names, got {len(speaker_names)}"))
        
        # 5. Check speaker details
        speaker_details = speaker_recognition.get('speaker_details', {})
        validation_results.append(('speaker_details', len(speaker_details) == expected_speakers, f"Expected {expected_speakers} speaker details, got {len(speaker_details)}"))
        
        # 6. Check segments with speaker info
        segments = json_data.get('segments', [])
        segments_with_speakers = [seg for seg in segments if seg.get('speaker') != 'unknown']
        validation_results.append(('segments_with_speakers', len(segments_with_speakers) > 0, f"Expected segments with speaker info, got {len(segments_with_speakers)}"))
        
        # Display validation results
        all_passed = True
        for field, passed, message in validation_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} {field}: {message}")
            if not passed:
                all_passed = False
        
        # Display speaker details
        if speaker_details:
            print(f"\n🎤 Speaker Details:")
            for speaker_id, details in speaker_details.items():
                print(f"   - {speaker_id}: {details['segment_count']} segments, {details['total_duration']:.2f}s total")
        
        # Display segments
        if segments:
            print(f"\n📝 Segments with Speaker Info:")
            for i, seg in enumerate(segments[:5]):  # Show first 5 segments
                print(f"   {i+1}. {seg['start']:.2f}s - {seg['end']:.2f}s: Speaker {seg['speaker']}")
            if len(segments) > 5:
                print(f"   ... and {len(segments) - 5} more segments")
        
        print(f"\n🎯 Overall Validation: {'✅ PASSED' if all_passed else '❌ FAILED'}")
        return all_passed
        
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False

def test_speaker_recognition():
    """Test speaker recognition logic independently with output processing"""
    print("🧪 Testing Speaker Recognition Logic with Output Processing")
    print("=" * 70)
    
    try:
        # 1. Load configuration
        print("1️⃣ Loading configuration...")
        cm = ConfigManager('config/environments')
        print(f"   ✅ Config loaded: Speaker diarization enabled = {cm.config.speaker.enabled}")
        
        # 2. Create output manager
        print("2️⃣ Creating output manager...")
        data_utils = DataUtils()
        from src.core.engines.strategies.output_strategy import MergedOutputStrategy, OverlappingTextDeduplicator
        deduplicator = OverlappingTextDeduplicator(cm)
        output_strategy = MergedOutputStrategy(cm, deduplicator)
        output_manager = OutputManager('output', data_utils, output_strategy)
        print("   ✅ Output manager created")
        
        # 3. Create speaker service
        print("3️⃣ Creating speaker service...")
        speaker_service = SpeakerServiceFactory.create_service(cm, output_manager=output_manager)
        print(f"   ✅ Speaker service created: {type(speaker_service).__name__}")
        
        # 4. Test speaker diarization with output processing
        print("4️⃣ Testing speaker diarization with output processing...")
        
        # Test audio files
        test_audio_files = [
            "/Users/gilcohen/voic_to_text_docker/examples/audio/audio_chunk_001_0s_30s.wav",
            "/Users/gilcohen/voic_to_text_docker/examples/audio/audio_chunk_002_25s_55s.wav"
        ]
        
        print("   🎯 Testing multiple chunks to validate speaker integration")
        print("   📁 Output will be saved to output/chunk_results/ for validation")
        
        test_results = []
        
        for i, test_audio_file in enumerate(test_audio_files, 1):
            if not os.path.exists(test_audio_file):
                print(f"   ❌ Test audio file not found: {test_audio_file}")
                continue
                
            print(f"\n   🎵 Processing chunk {i}: {os.path.basename(test_audio_file)}")
            print(f"   📁 File: {test_audio_file}")
            
            chunk_start_time = time.time()
            try:
                # Create test transcription result
                test_transcription = create_test_transcription_result(test_audio_file)
                
                # Run speaker recognition
                speaker_result = speaker_service.speaker_diarization(test_audio_file)
                chunk_processing_time = time.time() - chunk_start_time
                
                if speaker_result and speaker_result.success:
                    print(f"   ✅ Speaker recognition successful!")
                    print(f"      - Speakers detected: {speaker_result.speaker_count}")
                    print(f"      - Speaker keys: {list(speaker_result.speakers.keys())}")
                    print(f"      - Processing time: {chunk_processing_time:.2f}s")
                    
                    # Save test JSON output
                    json_path = save_test_json_output(test_audio_file, test_transcription, speaker_result)
                    
                    if json_path:
                        # Test full output generation with OutputManager
                        print(f"   📝 Testing full output generation...")
                        try:
                            # Create a combined data structure for output manager
                            output_data = {
                                'file_name': os.path.basename(test_audio_file),
                                'text': getattr(test_transcription, 'text', ''),
                                'segments': getattr(test_transcription, 'segments', []),
                                'speaker_recognition': {
                                    'total_speakers': speaker_result.speaker_count,
                                    'speaker_names': list(speaker_result.speakers.keys()),
                                    'speaker_details': {}
                                }
                            }
                            
                            # Add speaker details
                            for speaker_id, speaker_segments in speaker_result.speakers.items():
                                # speaker_segments is already the list of segments for this speaker
                                output_data['speaker_recognition']['speaker_details'][speaker_id] = {
                                    'segment_count': len(speaker_segments),
                                    'total_duration': sum(seg.duration for seg in speaker_segments),
                                    'segments': [
                                        {
                                            'start': seg.start,
                                            'end': seg.end,
                                            'text': seg.text,
                                            'duration': seg.duration
                                        }
                                        for seg in speaker_segments
                                    ]
                                }
                            
                            # Save using OutputManager to generate all formats
                            output_results = output_manager.save_transcription(
                                output_data, 
                                'output/chunk_results', 
                                'test_model', 
                                'test_engine'
                            )
                            
                            if output_results:
                                print(f"   ✅ Full output generation successful!")
                                for format_type, file_path in output_results.items():
                                    if file_path and os.path.exists(file_path):
                                        file_size = os.path.getsize(file_path)
                                        print(f"      - {format_type.upper()}: {os.path.basename(file_path)} ({file_size} bytes)")
                                    else:
                                        print(f"      - {format_type.upper()}: Failed to create")
                            else:
                                print(f"   ⚠️ Full output generation returned no results")
                                
                        except Exception as e:
                            print(f"   ⚠️ Full output generation test failed: {e}")
                            import traceback
                            traceback.print_exc()
                        
                        # Validate the output
                        validation_passed = validate_speaker_integration(json_path, expected_speakers=2)
                        test_results.append((test_audio_file, True, validation_passed, chunk_processing_time))
                    else:
                        test_results.append((test_audio_file, True, False, chunk_processing_time))
                        
                else:
                    print(f"   ❌ Speaker recognition failed: {getattr(speaker_result, 'error_message', 'Unknown error')}")
                    print(f"      - Processing time: {chunk_processing_time:.2f}s")
                    test_results.append((test_audio_file, False, False, chunk_processing_time))
                
            except Exception as e:
                chunk_processing_time = time.time() - chunk_start_time
                print(f"   ❌ Test failed: {e}")
                print(f"      - Processing time: {chunk_processing_time:.2f}s")
                test_results.append((test_audio_file, False, False, chunk_processing_time))
                continue
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 50)
        
        successful_tests = sum(1 for _, success, _, _ in test_results if success)
        validation_passed = sum(1 for _, _, validation, _ in test_results if validation)
        total_tests = len(test_results)
        
        print(f"   Total tests: {total_tests}")
        print(f"   Successful speaker recognition: {successful_tests}/{total_tests}")
        print(f"   Validation passed: {validation_passed}/{total_tests}")
        
        if test_results:
            avg_processing_time = sum(time for _, _, _, time in test_results) / len(test_results)
            print(f"   Average processing time: {avg_processing_time:.2f}s")
        
        print(f"\n💾 Test JSON files saved to: output/chunk_results/")
        print(f"🔍 Review the JSON files to validate speaker integration structure")
        
        print("\n✅ Enhanced speaker recognition test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_speaker_recognition()
