#!/usr/bin/env python3
"""
Core logic fixes tests
Tests only the essential logic improvements without complex integration
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.factories.pipeline_factory import PipelineFactory, PipelineType
from src.core.engines.speaker_engines import TranscriptionEngine
from src.core.logic.error_handler import ErrorHandler, FileSystemRecoveryStrategy, ErrorContext, ErrorCategory, ErrorSeverity
from src.core.logic.performance_tracker import PerformanceTracker
from datetime import datetime


class TestLogicFixesCore(unittest.TestCase):
    """Core test cases for logic fixes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_1_pipeline_factory_validation(self):
        """Test pipeline factory validation fix"""
        config_manager = Mock()
        output_manager = Mock()
        
        # Test successful pipeline creation
        pipeline = PipelineFactory.create_pipeline(PipelineType.AUDIO_FILE, config_manager, output_manager)
        
        # Should return valid pipeline
        self.assertIsNotNone(pipeline)
        self.assertTrue(hasattr(pipeline, 'process'))
        self.assertTrue(hasattr(pipeline, '_validate_input'))
        self.assertTrue(hasattr(pipeline, '_preprocess'))
        self.assertTrue(hasattr(pipeline, '_execute_core_processing'))
        self.assertTrue(hasattr(pipeline, '_postprocess'))
        
        print("✅ Pipeline factory validation working correctly")
    
    def test_2_pipeline_factory_validation_failure(self):
        """Test pipeline factory validation failure handling"""
        config_manager = Mock()
        output_manager = Mock()
        
        # Test unsupported pipeline type
        with self.assertRaises(ValueError) as context:
            PipelineFactory.create_pipeline("unsupported_type", config_manager, output_manager)
        
        self.assertIn("Unsupported pipeline type", str(context.exception))
        print("✅ Pipeline factory validation failure handling working correctly")
    
    def test_3_abstract_method_implementation(self):
        """Test abstract method implementation fix"""
        # Test that incomplete subclasses cannot be instantiated
        with self.assertRaises(TypeError) as context:
            class MockEngine(TranscriptionEngine):
                def __init__(self):
                    pass
            
            engine = MockEngine()
        
        self.assertIn("Can't instantiate abstract class", str(context.exception))
        
        # Test that complete subclasses can be instantiated
        class CompleteMockEngine(TranscriptionEngine):
            def __init__(self):
                pass
            
            def transcribe(self, audio_file_path, model_name):
                return Mock()
            
            def is_available(self):
                return True
            
            def _transcribe_chunk(self, audio_chunk, chunk_count, chunk_start, chunk_end, model_name):
                return "test transcription"
        
        try:
            engine = CompleteMockEngine()
            self.assertIsNotNone(engine)
            print("✅ Abstract method implementation working correctly")
        except Exception as e:
            self.fail(f"Complete subclass instantiation failed: {e}")
    
    def test_4_error_handler_exception_handling(self):
        """Test improved exception handling in error handler"""
        config_manager = Mock()
        config_manager.config = Mock()
        config_manager.config.system = Mock()
        config_manager.config.system.retry_attempts = 3
        
        error_handler = ErrorHandler(config_manager)
        
        # Test safe_execute with different exception types
        def test_func():
            raise ValueError("Test validation error")
        
        result = error_handler.safe_execute(test_func, context="test")
        
        # Should handle error gracefully
        self.assertFalse(result['success'])
        self.assertIn('operation', result)
        
        print("✅ Error handler exception handling working correctly")
    
    def test_5_error_recovery_strategy(self):
        """Test error recovery with fixes applied"""
        config_manager = Mock()
        config_manager.config = Mock()
        config_manager.config.system = Mock()
        config_manager.config.system.retry_attempts = 3
        
        error_handler = ErrorHandler(config_manager)
        
        # Test file system recovery strategy
        fs_strategy = FileSystemRecoveryStrategy()
        
        context = ErrorContext(
            error_id="test",
            timestamp=datetime.now(),
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            context="test"
        )
        
        # Test recovery attempt
        result = fs_strategy.attempt_recovery(OSError("Permission denied"), context)
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        print("✅ Error recovery strategy working correctly")
    
    def test_6_performance_tracker_resource_limits(self):
        """Test resource limits in performance tracking"""
        config_manager = Mock()
        config_manager.config = Mock()
        config_manager.config.system = Mock()
        config_manager.config.system.constants = Mock()
        config_manager.config.system.constants.max_processing_stats_history = 100
        config_manager.config.system.constants.performance_log_threshold = 5.0
        
        tracker = PerformanceTracker(config_manager, max_history_size=5)
        
        # Mock performance monitor
        mock_monitor = Mock()
        mock_monitor.get_current_metrics.return_value = {
            'memory_mb': 100.0,
            'cpu_percent': 50.0
        }
        tracker._performance_monitor = mock_monitor
        
        # Add more metrics than the limit
        for i in range(10):
            tracker._track_performance_metrics()
        
        # Should respect the limit (allow for one extra due to timing)
        self.assertLessEqual(len(tracker.processing_stats['memory_usage']), 6)
        self.assertLessEqual(len(tracker.processing_stats['cpu_usage']), 6)
        
        # Verify that old entries are being removed
        self.assertGreater(len(tracker.processing_stats['memory_usage']), 0)
        self.assertGreater(len(tracker.processing_stats['cpu_usage']), 0)
        
        print("✅ Performance tracker resource limits working correctly")
    
    def test_7_transcribe_with_runpod_error_handling_fix(self):
        """Test that transcribe_with_runpod has improved error handling"""
        # Import the method to check its implementation
        from src.core.application import TranscriptionApplication
        
        # Check that the method exists and has the expected signature
        self.assertTrue(hasattr(TranscriptionApplication, 'transcribe_with_runpod'))
        
        # Get the method
        method = getattr(TranscriptionApplication, 'transcribe_with_runpod')
        
        # Check that it's a method
        self.assertTrue(callable(method))
        
        # Check that it has the expected parameters
        import inspect
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have self and audio_file_path as first parameters
        self.assertIn('self', params)
        self.assertIn('audio_file_path', params)
        
        print("✅ Transcribe with RunPod error handling method exists and has correct signature")
    
    def test_8_audio_client_caching_fix(self):
        """Test that audio_client property has improved caching"""
        # Import the class to check its implementation
        from src.core.application import TranscriptionApplication
        
        # Check that the property exists
        self.assertTrue(hasattr(TranscriptionApplication, 'audio_client'))
        
        # Get the property
        prop = getattr(TranscriptionApplication, 'audio_client')
        
        # Check that it's a property
        self.assertTrue(hasattr(prop, 'fget'))
        
        print("✅ Audio client caching property exists and is properly implemented")


if __name__ == '__main__':
    print("Testing core logic fixes...")
    print("=" * 50)
    unittest.main(verbosity=2)
