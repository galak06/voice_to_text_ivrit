#!/usr/bin/env python3
"""
Integration test for the custom-whisper engine.
Verifies availability and optionally runs a small smoke transcription
if TEST_ENGINE_SMOKE=1 and EXAMPLE_AUDIO exists.
"""

import os
import unittest
import signal
from contextlib import contextmanager

from src.core.factories.engine_factory import create_engine
from src.models.speaker_models import SpeakerConfig


class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds):
    """Context manager to timeout operations"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class TestCustomWhisperEngineIntegration(unittest.TestCase):
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
        self.engine = create_engine("custom-whisper", self.config)

    def test_engine_available(self):
        if not self.engine.is_available():
            self.skipTest("custom-whisper engine dependencies not available in this environment")
        self.assertTrue(True)

    def test_smoke_transcription_optional(self):
        if os.environ.get("TEST_ENGINE_SMOKE") != "1":
            self.skipTest("Smoke test disabled. Set TEST_ENGINE_SMOKE=1 to enable.")

        # Use a much shorter audio file for smoke testing (1.8MB instead of 5MB+)
        audio_path = os.environ.get("EXAMPLE_AUDIO", "examples/audio/test/test_1min.wav")
        if not os.path.exists(audio_path):
            self.skipTest(f"Example audio not found: {audio_path}")

        # Use ivrit model id for custom-whisper
        # Add timeout to prevent long-running tests
        try:
            with timeout(120):  # 2 minute timeout for smoke test
                result = self.engine.transcribe(audio_path, "ivrit-ai/whisper-large-v3-ct2")
                self.assertIsNotNone(result)
                self.assertTrue(result.transcription_time >= 0)
        except TimeoutError:
            self.fail("Smoke test timed out after 2 minutes - audio file may be too long")


if __name__ == "__main__":
    unittest.main()


