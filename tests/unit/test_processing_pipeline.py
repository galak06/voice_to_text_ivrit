"""
Tests for Processing Pipeline
Tests the new pipeline structure and SOLID principles implementation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from src.core.processors.processing_pipeline import (
    ProcessingPipeline, 
    ProcessingContext, 
    ProcessingResult,
    AudioFileProcessingPipeline,
    BatchProcessingPipeline
)
from src.core.factories.pipeline_factory import PipelineFactory, PipelineType
from src.core.logic.error_handler import ErrorHandler
from src.core.logic.result_builder import ResultBuilder
from src.utils.config_manager import ConfigManager
from src.output_data import OutputManager


class TestProcessingPipeline(unittest.TestCase):
    """Test cases for the ProcessingPipeline base class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = Mock()
        self.config_manager.config.audio = Mock()
        self.config_manager.config.audio.supported_formats = ['.wav', '.mp3', '.m4a']
        self.config_manager.config.audio.sample_rate = 16000
        self.config_manager.config.audio.channels = 1
        self.config_manager.config.system = Mock()
        self.config_manager.config.system.debug = False
        
        self.output_manager = Mock(spec=OutputManager)
        self.output_manager.save_json.return_value = {'success': True, 'file_path': '/test/output.json'}
        self.output_manager.save_text.return_value = {'success': True, 'file_path': '/test/output.txt'}
        
        # Create a concrete test pipeline
        class TestPipeline(ProcessingPipeline):
            def _validate_input(self, context):
                return {'success': True, 'test': 'validation'}
            
            def _preprocess(self, context):
                return {'success': True, 'test': 'preprocessing'}
            
            def _execute_core_processing(self, context):
                return {'success': True, 'test': 'core_processing'}
            
            def _postprocess(self, context, data):
                return {'success': True, 'data': data}
        
        self.test_pipeline = TestPipeline(self.config_manager, self.output_manager)
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization with dependencies"""
        self.assertIsNotNone(self.test_pipeline.config_manager)
        self.assertIsNotNone(self.test_pipeline.output_manager)
        self.assertIsNotNone(self.test_pipeline.error_handler)
        self.assertIsNotNone(self.test_pipeline.result_builder)
    
    def test_successful_processing_flow(self):
        """Test successful processing through the template method"""
        context = ProcessingContext(
            session_id="test_session",
            file_path="/test/audio.wav",
            operation_type="test_processing"
        )
        
        result = self.test_pipeline.process(context)
        
        self.assertTrue(result.success)
        self.assertEqual(result.context.session_id, "test_session")
        self.assertIn('performance_metrics', result.__dict__)
        self.assertIn('processing_time_seconds', result.performance_metrics)
    
    def test_processing_with_validation_failure(self):
        """Test processing when validation fails"""
        class FailingValidationPipeline(ProcessingPipeline):
            def _validate_input(self, context):
                return {'success': False, 'error': 'Validation failed'}
            
            def _preprocess(self, context):
                return {'success': True}
            
            def _execute_core_processing(self, context):
                return {'success': True}
            
            def _postprocess(self, context, data):
                return {'success': True, 'data': data}
        
        pipeline = FailingValidationPipeline(self.config_manager, self.output_manager)
        context = ProcessingContext(session_id="test_session")
        
        result = pipeline.process(context)
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0]['message'], 'Validation failed')
    
    def test_processing_with_exception(self):
        """Test processing when an exception occurs"""
        class ExceptionPipeline(ProcessingPipeline):
            def _validate_input(self, context):
                raise ValueError("Test exception")
            
            def _preprocess(self, context):
                return {'success': True}
            
            def _execute_core_processing(self, context):
                return {'success': True}
            
            def _postprocess(self, context, data):
                return {'success': True, 'data': data}
        
        pipeline = ExceptionPipeline(self.config_manager, self.output_manager)
        context = ProcessingContext(session_id="test_session")
        
        result = pipeline.process(context)
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0]['error_type'], 'ValueError')


class TestAudioFileProcessingPipeline(unittest.TestCase):
    """Test cases for AudioFileProcessingPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = Mock()
        self.config_manager.config.audio = Mock()
        self.config_manager.config.audio.supported_formats = ['.wav', '.mp3', '.m4a']
        self.config_manager.config.audio.sample_rate = 16000
        self.config_manager.config.audio.channels = 1
        self.config_manager.config.system = Mock()
        self.config_manager.config.system.debug = False
        
        self.output_manager = Mock(spec=OutputManager)
        self.output_manager.save_json.return_value = {'success': True, 'file_path': '/test/output.json'}
        self.output_manager.save_text.return_value = {'success': True, 'file_path': '/test/output.txt'}
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_file = Path(self.temp_dir) / "test_audio.wav"
        self.test_audio_file.write_bytes(b"fake audio data")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.core.processors.processing_pipeline.librosa')
    def test_audio_file_validation_success(self, mock_librosa):
        """Test successful audio file validation"""
        pipeline = AudioFileProcessingPipeline(self.config_manager, self.output_manager)
        
        context = ProcessingContext(
            session_id="test_session",
            file_path=str(self.test_audio_file),
            operation_type="audio_transcription"
        )
        
        # Mock librosa for metadata extraction
        mock_librosa.load.return_value = (Mock(), 16000)
        
        result = pipeline._validate_input(context)
        
        self.assertTrue(result['success'])
        self.assertIn('file_size', result)
    
    def test_audio_file_validation_file_not_exists(self):
        """Test audio file validation when file doesn't exist"""
        pipeline = AudioFileProcessingPipeline(self.config_manager, self.output_manager)
        
        context = ProcessingContext(
            session_id="test_session",
            file_path="/nonexistent/file.wav",
            operation_type="audio_transcription"
        )
        
        result = pipeline._validate_input(context)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_audio_file_validation_unsupported_format(self):
        """Test audio file validation with unsupported format"""
        pipeline = AudioFileProcessingPipeline(self.config_manager, self.output_manager)
        
        # Create file with unsupported extension
        unsupported_file = Path(self.temp_dir) / "test.txt"
        unsupported_file.write_text("not audio")
        
        context = ProcessingContext(
            session_id="test_session",
            file_path=str(unsupported_file),
            operation_type="audio_transcription"
        )
        
        result = pipeline._validate_input(context)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('src.core.processors.processing_pipeline.librosa')
    def test_audio_file_preprocessing(self, mock_librosa):
        """Test audio file preprocessing"""
        pipeline = AudioFileProcessingPipeline(self.config_manager, self.output_manager)
        
        context = ProcessingContext(
            session_id="test_session",
            file_path=str(self.test_audio_file),
            operation_type="audio_transcription"
        )
        
        # Mock librosa for metadata extraction
        mock_librosa.load.return_value = (Mock(), 16000)
        
        result = pipeline._preprocess(context)
        
        self.assertTrue(result['success'])
        self.assertIn('metadata', result)
        self.assertIn('processing_params', result)


class TestBatchProcessingPipeline(unittest.TestCase):
    """Test cases for BatchProcessingPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = Mock()
        self.config_manager.config.audio = Mock()
        self.config_manager.config.audio.supported_formats = ['.wav', '.mp3', '.m4a']
        self.config_manager.config.system = Mock()
        self.config_manager.config.system.debug = False
        
        self.output_manager = Mock(spec=OutputManager)
        self.output_manager.save_json.return_value = {'success': True, 'file_path': '/test/output.json'}
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_dir = Path(self.temp_dir) / "audio_files"
        self.test_audio_dir.mkdir()
        
        # Create test audio files
        for i in range(3):
            audio_file = self.test_audio_dir / f"test_audio_{i}.wav"
            audio_file.write_bytes(b"fake audio data")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_batch_validation_success(self):
        """Test successful batch validation"""
        pipeline = BatchProcessingPipeline(self.config_manager, self.output_manager)
        
        context = ProcessingContext(
            session_id="test_session",
            operation_type="batch_processing",
            parameters={'input_directory': str(self.test_audio_dir)}
        )
        
        result = pipeline._validate_input(context)
        
        self.assertTrue(result['success'])
        self.assertIn('files', result)
        self.assertEqual(len(result['files']), 3)
    
    def test_batch_validation_no_directory(self):
        """Test batch validation when no directory is specified"""
        pipeline = BatchProcessingPipeline(self.config_manager, self.output_manager)
        
        context = ProcessingContext(
            session_id="test_session",
            operation_type="batch_processing",
            parameters={}
        )
        
        result = pipeline._validate_input(context)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_batch_validation_nonexistent_directory(self):
        """Test batch validation with nonexistent directory"""
        pipeline = BatchProcessingPipeline(self.config_manager, self.output_manager)
        
        context = ProcessingContext(
            session_id="test_session",
            operation_type="batch_processing",
            parameters={'input_directory': '/nonexistent/directory'}
        )
        
        result = pipeline._validate_input(context)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_batch_preprocessing(self):
        """Test batch preprocessing"""
        pipeline = BatchProcessingPipeline(self.config_manager, self.output_manager)
        
        context = ProcessingContext(
            session_id="test_session",
            operation_type="batch_processing",
            parameters={'files': [str(f) for f in self.test_audio_dir.glob('*.wav')]}
        )
        
        result = pipeline._preprocess(context)
        
        self.assertTrue(result['success'])
        self.assertIn('processing_queue', result)
        self.assertEqual(len(result['processing_queue']), 3)


class TestPipelineFactory(unittest.TestCase):
    """Test cases for PipelineFactory"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=ConfigManager)
        # Ensure mocks expose a .config attribute expected by pipelines/ErrorHandler
        self.config_manager.config = Mock()
        self.config_manager.config.audio = Mock()
        self.config_manager.config.audio.supported_formats = ['.wav', '.mp3', '.m4a']
        self.config_manager.config.system = Mock()
        self.config_manager.config.system.debug = False

        self.output_manager = Mock(spec=OutputManager)
    
    def test_create_audio_file_pipeline(self):
        """Test creating audio file pipeline"""
        pipeline = PipelineFactory.create_pipeline(
            PipelineType.AUDIO_FILE,
            self.config_manager,
            self.output_manager
        )
        
        # Accept either the abstract base or its concrete implementation
        from src.core.processors.audio_file_processor import AudioFileProcessor
        self.assertTrue(isinstance(pipeline, (AudioFileProcessingPipeline, AudioFileProcessor)))
    
    def test_create_batch_pipeline(self):
        """Test creating batch pipeline"""
        pipeline = PipelineFactory.create_pipeline(
            PipelineType.BATCH,
            self.config_manager,
            self.output_manager
        )
        
        self.assertIsInstance(pipeline, BatchProcessingPipeline)
    
    def test_create_pipeline_from_operation(self):
        """Test creating pipeline from operation type"""
        pipeline = PipelineFactory.create_pipeline_from_operation(
            "audio_transcription",
            self.config_manager,
            self.output_manager
        )
        
        from src.core.processors.audio_file_processor import AudioFileProcessor
        self.assertTrue(isinstance(pipeline, (AudioFileProcessingPipeline, AudioFileProcessor)))
    
    def test_create_pipeline_invalid_type(self):
        """Test creating pipeline with invalid type"""
        with self.assertRaises(ValueError):
            PipelineFactory.create_pipeline(
                "invalid_type",
                self.config_manager,
                self.output_manager
            )
    
    def test_get_supported_pipeline_types(self):
        """Test getting supported pipeline types"""
        types = PipelineFactory.get_supported_pipeline_types()
        
        self.assertIsInstance(types, list)
        self.assertIn(PipelineType.AUDIO_FILE, types)
        self.assertIn(PipelineType.BATCH, types)


class TestProcessingContext(unittest.TestCase):
    """Test cases for ProcessingContext"""
    
    def test_processing_context_creation(self):
        """Test creating ProcessingContext"""
        context = ProcessingContext(
            session_id="test_session",
            file_path="/test/file.wav",
            operation_type="test_operation"
        )
        
        self.assertEqual(context.session_id, "test_session")
        self.assertEqual(context.file_path, "/test/file.wav")
        self.assertEqual(context.operation_type, "test_operation")
        self.assertIsInstance(context.timestamp, datetime)
        self.assertIsInstance(context.parameters, dict)
        self.assertIsInstance(context.metadata, dict)
    
    def test_processing_context_defaults(self):
        """Test ProcessingContext with default values"""
        context = ProcessingContext(session_id="test_session")
        
        self.assertEqual(context.session_id, "test_session")
        self.assertIsNone(context.file_path)
        self.assertEqual(context.operation_type, "")
        self.assertIsInstance(context.parameters, dict)
        self.assertIsInstance(context.metadata, dict)


class TestProcessingResult(unittest.TestCase):
    """Test cases for ProcessingResult"""
    
    def test_processing_result_creation(self):
        """Test creating ProcessingResult"""
        context = ProcessingContext(session_id="test_session")
        result = ProcessingResult(
            success=True,
            context=context,
            data={'test': 'data'}
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.context, context)
        self.assertEqual(result.data, {'test': 'data'})
        self.assertIsInstance(result.errors, list)
        self.assertIsInstance(result.warnings, list)
        self.assertIsInstance(result.performance_metrics, dict)
        self.assertIsInstance(result.timestamp, datetime)
    
    def test_processing_result_with_errors(self):
        """Test ProcessingResult with errors"""
        context = ProcessingContext(session_id="test_session")
        errors = [{'error': 'Test error'}]
        
        result = ProcessingResult(
            success=False,
            context=context,
            errors=errors
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.errors, errors)


if __name__ == '__main__':
    unittest.main()
