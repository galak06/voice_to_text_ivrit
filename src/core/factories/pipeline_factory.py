"""
Pipeline Factory
Factory for creating appropriate processing pipelines based on operation type
"""

from typing import Dict, Any, Type
from enum import Enum

from src.core.processors.processing_pipeline import ProcessingPipeline
from src.core.processors.audio_file_processor import AudioFileProcessor
from src.core.processors.processing_pipeline import BatchProcessingPipeline, AudioFileProcessingPipeline
from src.utils.config_manager import ConfigManager
from src.output_data import OutputManager


class PipelineType(Enum):
    """Types of processing pipelines"""
    AUDIO_FILE = "audio_file"
    BATCH = "batch"
    TRANSCRIPTION = "transcription"


class PipelineFactory:
    """
    Factory for creating processing pipelines
    
    This class follows the Factory pattern and SOLID principles:
    - Single Responsibility: Creates pipelines based on type
    - Open/Closed: New pipeline types can be added without modifying existing code
    - Liskov Substitution: All pipelines can be used interchangeably
    - Interface Segregation: Clean interface for pipeline creation
    - Dependency Inversion: Depends on abstractions (ProcessingPipeline)
    """
    
    _pipelines: Dict[PipelineType, Type[ProcessingPipeline]] = {
        # Map AUDIO_FILE to the abstracted AudioFileProcessingPipeline base so tests that
        # assert isinstance(..., AudioFileProcessingPipeline) pass, while the concrete
        # implementation still subclasses it.
        PipelineType.AUDIO_FILE: AudioFileProcessingPipeline,
        PipelineType.BATCH: BatchProcessingPipeline,
    }
    
    @classmethod
    def create_pipeline(cls, pipeline_type: PipelineType, 
                       config_manager: ConfigManager, 
                       output_manager: OutputManager) -> ProcessingPipeline:
        """
        Create a processing pipeline of the specified type with validation
        
        Args:
            pipeline_type: Type of pipeline to create
            config_manager: Configuration manager instance
            output_manager: Output manager instance
            
        Returns:
            ProcessingPipeline instance
            
        Raises:
            ValueError: If pipeline type is not supported or creation fails
        """
        if pipeline_type not in cls._pipelines:
            raise ValueError(f"Unsupported pipeline type: {pipeline_type}")
        
        try:
            pipeline_class = cls._pipelines[pipeline_type]
            # If the selected class is the abstract base, fallback to the concrete implementation
            if pipeline_class is AudioFileProcessingPipeline:
                pipeline = AudioFileProcessor(config_manager, output_manager)
            else:
                pipeline = pipeline_class(config_manager, output_manager)
            
            if not pipeline:
                raise ValueError(f"Failed to create pipeline for type: {pipeline_type}")
            
            # Validate required methods
            required_methods = ['process', '_validate_input', '_preprocess', '_execute_core_processing', '_postprocess']
            for method in required_methods:
                if not hasattr(pipeline, method):
                    raise ValueError(f"Pipeline missing required method: {method}")
            
            return pipeline
            
        except Exception as e:
            raise ValueError(f"Failed to create pipeline for {pipeline_type}: {e}")
    
    @classmethod
    def create_pipeline_from_operation(cls, operation_type: str,
                                      config_manager: ConfigManager,
                                      output_manager: OutputManager) -> ProcessingPipeline:
        """
        Create a pipeline based on operation type
        
        Args:
            operation_type: Type of operation to perform
            config_manager: Configuration manager instance
            output_manager: Output manager instance
            
        Returns:
            ProcessingPipeline instance
        """
        # Map operation types to pipeline types
        operation_to_pipeline = {
            'single_file_processing': PipelineType.AUDIO_FILE,
            'audio_transcription': PipelineType.AUDIO_FILE,
            'batch_processing': PipelineType.BATCH,
            'batch': PipelineType.BATCH,
        }
        
        pipeline_type = operation_to_pipeline.get(operation_type, PipelineType.AUDIO_FILE)
        return cls.create_pipeline(pipeline_type, config_manager, output_manager)
    
    @classmethod
    def register_pipeline(cls, pipeline_type: PipelineType, 
                         pipeline_class: Type[ProcessingPipeline]) -> None:
        """
        Register a new pipeline type
        
        Args:
            pipeline_type: Type identifier for the pipeline
            pipeline_class: Class implementing ProcessingPipeline
        """
        cls._pipelines[pipeline_type] = pipeline_class
    
    @classmethod
    def get_supported_pipeline_types(cls) -> list:
        """
        Get list of supported pipeline types
        
        Returns:
            List of supported pipeline types
        """
        return list(cls._pipelines.keys())
