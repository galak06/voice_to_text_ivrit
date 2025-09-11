#!/usr/bin/env python3
"""
Factory for creating engine selection strategies
Follows Factory Pattern for creating different strategies
"""

from typing import Dict, Any
from src.core.interfaces.engine_selection_protocols import EngineSelectionStrategyProtocol
from src.core.models.engine_selection_strategies import (
    ConfigurationBasedEngineStrategy,
    ArgumentPriorityEngineStrategy
)


class EngineSelectionStrategyFactory:
    """Factory for creating engine selection strategies"""
    
    @staticmethod
    def create_strategy(strategy_type: str = "configuration_based", config_manager=None) -> EngineSelectionStrategyProtocol:
        """
        Create engine selection strategy based on type
        
        Args:
            strategy_type: Type of strategy to create
            config_manager: ConfigManager instance for strategy initialization
            
        Returns:
            EngineSelectionStrategyProtocol implementation
        """
        strategies = {
            "configuration_based": ConfigurationBasedEngineStrategy,
            "argument_priority": ArgumentPriorityEngineStrategy
        }
        
        strategy_class = strategies.get(strategy_type, ConfigurationBasedEngineStrategy)
        return strategy_class(config_manager)
    
    @staticmethod 
    def create_strategy_from_config(config: Dict[str, Any], config_manager=None) -> EngineSelectionStrategyProtocol:
        """
        Create engine selection strategy based on configuration
        
        Args:
            config: Configuration dictionary
            config_manager: ConfigManager instance for strategy initialization
            
        Returns:
            EngineSelectionStrategyProtocol implementation
        """
        # Check if configuration specifies a strategy preference
        strategy_type = config.get('system', {}).get('engine_selection_strategy', 'configuration_based')
        return EngineSelectionStrategyFactory.create_strategy(strategy_type, config_manager)
