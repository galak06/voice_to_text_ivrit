#!/usr/bin/env python3
"""
Engine selection strategy protocols
Defines contracts for different engine selection behaviors
"""

from typing import Protocol, Dict, Any


class EngineSelectionStrategyProtocol(Protocol):
    """Protocol for engine selection strategies"""
    
    def select_engine(self, config: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        """Select the appropriate engine based on configuration and arguments"""
        ...


class EngineConfigurationProviderProtocol(Protocol):
    """Protocol for providing engine configuration"""
    
    def get_default_engine(self) -> str:
        """Get the default engine from configuration"""
        ...
    
    def get_supported_engines(self) -> list[str]:
        """Get list of supported engines"""
        ...
