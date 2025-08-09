#!/usr/bin/env python3
"""
Integration test for the optimized-whisper (CTranslate2) engine.
Verifies availability and optionally runs a small smoke transcription
if TEST_ENGINE_SMOKE=1 and EXAMPLE_AUDIO exists.
"""

import os
import unittest

from src.core.engines.speaker_engines import TranscriptionEngineFactory
from src.models.speaker_models import SpeakerConfig


class TestOptimizedWhisperEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.config = SpeakerConfig(
            min_speakers=1,
            max_speakers=2,
            silence_threshold=0.5,
            vad_enabled=True,
            chunk_duration=30.0,
            overlap_duration=2.0,
            language="he",
        )
        self.engine = TranscriptionEngineFactory.create_engine("optimized-whisper", self.config)

    def test_engine_available(self):
        if not self.engine.is_available():
            self.skipTest("optimized-whisper (ct2) engine dependencies not available in this environment")
        self.assertTrue(True)

    def test_smoke_transcription_optional(self):
        if os.environ.get("TEST_ENGINE_SMOKE") != "1":
            self.skipTest("Smoke test disabled. Set TEST_ENGINE_SMOKE=1 to enable.")

        audio_path = os.environ.get("EXAMPLE_AUDIO", "examples/audio/voice/meeting_2.wav")
        if not os.path.exists(audio_path):
            self.skipTest(f"Example audio not found: {audio_path}")

        # Use ct2 model id for optimized-whisper
        result = self.engine.transcribe(audio_path, "ivrit-ai/whisper-large-v3-turbo-ct2")
        self.assertIsNotNone(result)
        self.assertTrue(result.transcription_time >= 0)


if __name__ == "__main__":
    unittest.main()


