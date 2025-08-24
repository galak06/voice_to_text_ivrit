#!/usr/bin/env python3
"""
Integration test for the stable-whisper engine.
Verifies availability and optionally runs a small smoke transcription
if TEST_ENGINE_SMOKE=1 and EXAMPLE_AUDIO exists.
"""

import os
import unittest
import json
from datetime import datetime

from src.core.factories.engine_factory import create_engine
from src.models.speaker_models import SpeakerConfig


class TestStableWhisperEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.config = SpeakerConfig(
            min_speakers=1,
            max_speakers=2,
            silence_threshold=0.5,
            vad_enabled=True,
            chunk_duration=30.0,
            overlap_duration=2.0,
            language="en",
        )
        self.engine = create_engine("stable-whisper", self.config)

    def test_engine_available(self):
        self.assertTrue(self.engine.is_available())

    def test_smoke_transcription_optional(self):
        if os.environ.get("TEST_ENGINE_SMOKE") != "1":
            self.skipTest("Smoke test disabled. Set TEST_ENGINE_SMOKE=1 to enable.")

        audio_path = os.environ.get("EXAMPLE_AUDIO", "examples/audio/voice/meeting_2.wav")
        if not os.path.exists(audio_path):
            self.skipTest(f"Example audio not found: {audio_path}")

        # Use a standard Whisper model id for stable-whisper
        result = self.engine.transcribe(audio_path, "large-v3")
        self.assertIsNotNone(result)
        self.assertTrue(result.transcription_time >= 0)
        
        # Debug output to see result structure
        print(f"\n🔍 DEBUG: Result object type: {type(result)}")
        print(f"🔍 DEBUG: Result attributes: {dir(result)}")
        
        # Check for the correct attribute names
        if hasattr(result, 'full_text'):
            print(f"🔍 DEBUG: Result.full_text exists: {result.full_text}")
            print(f"🔍 DEBUG: Result.full_text length: {len(result.full_text)}")
        else:
            print(f"🔍 DEBUG: Result.full_text does not exist")
        
        if hasattr(result, 'speakers'):
            print(f"🔍 DEBUG: Result.speakers exists: {result.speakers}")
        else:
            print(f"🔍 DEBUG: Result.speakers does not exist")
        
        # Save results to output folder for verification
        if result and hasattr(result, 'full_text') and result.full_text:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"output/transcriptions/test_run_{timestamp}"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save as text
            text_file = os.path.join(output_dir, "transcription_result.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"Test Transcription Results\n")
                f.write(f"========================\n")
                f.write(f"Audio: {audio_path}\n")
                f.write(f"Engine: stable-whisper\n")
                f.write(f"Model: large-v3\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Duration: {result.transcription_time:.1f}s\n")
                f.write(f"Characters: {len(result.full_text)}\n")
                f.write(f"Success: {result.success}\n")
                f.write(f"Audio File: {result.audio_file}\n")
                f.write(f"\nTranscribed Text:\n")
                f.write(f"================\n")
                f.write(result.full_text)
                f.write(f"\n\nResult Details:\n")
                f.write(f"===============\n")
                f.write(f"Success: {result.success}\n")
                f.write(f"Audio File: {result.audio_file}\n")
                f.write(f"Transcription Time: {result.transcription_time:.1f}s\n")
                if hasattr(result, 'speakers') and result.speakers:
                    f.write(f"Speakers: {result.speakers}\n")
            
            # Save as JSON
            json_file = os.path.join(output_dir, "transcription_result.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "audio_file": audio_path,
                    "engine": "stable-whisper",
                    "model": "large-v3",
                    "timestamp": timestamp,
                    "transcription_time": result.transcription_time,
                    "text": result.full_text,
                    "characters": len(result.full_text),
                    "success": result.success,
                    "result_audio_file": result.audio_file,
                    "available_attributes": [attr for attr in dir(result) if not attr.startswith('_')]
                }, f, indent=2, ensure_ascii=False)
            
            # Save as DOCX (Word document)
            try:
                from src.output_data.formatters.docx_formatter import DocxFormatter
                docx_file = os.path.join(output_dir, "transcription_result.docx")
                
                # Create DOCX document
                doc = DocxFormatter.create_transcription_document(
                    [{
                        "text": result.full_text,
                        "start": 0.0,
                        "end": 60.0,
                        "speaker": "0"
                    }],
                    audio_path,
                    "large-v3",
                    "stable-whisper"
                )
                
                if doc:
                    doc.save(docx_file)
                    print(f"\n💾 Test results saved to: {output_dir}")
                    print(f"   📄 Text: {text_file}")
                    print(f"   📊 JSON: {json_file}")
                    print(f"   📝 Word: {docx_file}")
                else:
                    print(f"\n⚠️  Failed to create DOCX document")
                    print(f"\n💾 Test results saved to: {output_dir}")
                    print(f"   📄 Text: {text_file}")
                    print(f"   📊 JSON: {json_file}")
                
            except ImportError:
                print(f"\n⚠️  python-docx not available - skipping DOCX generation")
                print(f"\n💾 Test results saved to: {output_dir}")
                print(f"   📄 Text: {text_file}")
                print(f"   📊 JSON: {json_file}")
            except Exception as e:
                print(f"\n⚠️  Failed to create DOCX: {e}")
                print(f"\n💾 Test results saved to: {output_dir}")
                print(f"   📄 Text: {text_file}")
                print(f"   📊 JSON: {json_file}")
        else:
            print(f"\n⚠️  Result object does not have full_text or full_text is empty, skipping output save")
            # Try to save what we can
            if result:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = f"output/transcriptions/test_run_{timestamp}"
                os.makedirs(output_dir, exist_ok=True)
                
                # Save debug info
                debug_file = os.path.join(output_dir, "debug_info.txt")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"Debug Information\n")
                    f.write(f"================\n")
                    f.write(f"Result Type: {type(result)}\n")
                    f.write(f"Available Attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}\n")
                    f.write(f"Transcription Time: {getattr(result, 'transcription_time', 'N/A')}\n")
                    f.write(f"Success: {getattr(result, 'success', 'N/A')}\n")
                    f.write(f"Audio File: {getattr(result, 'audio_file', 'N/A')}\n")
                
                print(f"\n💾 Debug info saved to: {debug_file}")


if __name__ == "__main__":
    unittest.main()


