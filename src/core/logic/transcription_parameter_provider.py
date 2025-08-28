"""
Transcription parameter provider implementations
Refactored to use dependency injection and remove duplicate code
"""

from typing import Dict, Any
from src.models import AppConfig
from src.core.interfaces.engine_selection_protocols import EngineSelectionStrategyProtocol
from src.core.factories.engine_selection_factory import EngineSelectionStrategyFactory


class TranscriptionParameterProvider:
    """Provider for transcription parameters using dependency injection"""
    
    def __init__(self, config: AppConfig, engine_selection_strategy: EngineSelectionStrategyProtocol = None):
        """
        Initialize parameter provider with injected dependencies
        
        Args:
            config: Application configuration
            engine_selection_strategy: Engine selection strategy (follows DIP)
        """
        self.config = config
        
        # Use injected strategy or create default one
        if engine_selection_strategy:
            self.engine_selection_strategy = engine_selection_strategy
        else:
            self.engine_selection_strategy = EngineSelectionStrategyFactory.create_strategy_from_config(
                config.dict() if hasattr(config, 'dict') else {}
            )
    
    def get_parameters(self, model: str = None, engine: str = None) -> Dict[str, Any]:
        """
        Get transcription parameters using injected strategy
        
        Args:
            model: Explicit model parameter
            engine: Explicit engine parameter
            
        Returns:
            Dictionary of transcription parameters
        """
        params = {}
        
        # Get model parameters
        if model:
            params['model'] = model
        elif hasattr(self.config, 'transcription') and self.config.transcription:
            params['model'] = getattr(self.config.transcription, 'default_model', 'whisper-large-v3')
        
        # Get engine parameters using injected strategy
        if engine:
            params['engine'] = engine
        else:
            # Use strategy to select engine from configuration
            kwargs = {'engine': None}  # No explicit engine in kwargs
            params['engine'] = self.engine_selection_strategy.select_engine(
                self.config.dict() if hasattr(self.config, 'dict') else {},
                kwargs
            )
        
        # Get streaming configuration
        if hasattr(self.config, 'transcription') and self.config.transcription:
            params['streaming'] = getattr(self.config.transcription, 'streaming_enabled', False)
        
        return params
