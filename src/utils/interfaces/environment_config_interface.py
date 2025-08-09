"""
Environment Config Interface
Defines the contract for environment-specific configuration operations
Following Interface Segregation Principle (ISP) and Liskov Substitution Principle (LSP)
"""

from typing import Protocol, Dict, Any
from abc import ABC, abstractmethod


class EnvironmentConfigInterface(Protocol):
    """Protocol for environment-specific configuration operations"""
    
    def get_environment_name(self) -> str:
        """
        Get the environment name
        
        Returns:
            Environment name (e.g., 'development', 'production')
        """
        ...
    
    def get_environment_specific_config(self) -> Dict[str, Any]:
        """
        Get environment-specific configuration overrides
        
        Returns:
            Environment-specific configuration dictionary
        """
        ...
    
    def apply_environment_overrides(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment-specific overrides to base configuration
        
        Args:
            base_config: Base configuration dictionary
            
        Returns:
            Configuration with environment overrides applied
        """
        ...
    
    def validate_environment_requirements(self) -> bool:
        """
        Validate that environment meets all requirements
        
        Returns:
            True if environment requirements are met, False otherwise
        """
        ...


class BaseEnvironmentConfig(ABC):
    """Abstract base class for environment configurations following LSP"""
    
    @abstractmethod
    def get_environment_name(self) -> str:
        """Get environment name - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_environment_specific_config(self) -> Dict[str, Any]:
        """Get environment-specific config - must be implemented by subclasses"""
        pass
    
    def apply_environment_overrides(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Default implementation for applying environment overrides"""
        env_config = self.get_environment_specific_config()
        return self._merge_configs(base_config, env_config)
    
    def validate_environment_requirements(self) -> bool:
        """Default implementation for environment validation"""
        return True
    
    def _merge_configs(self, base: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method for merging configurations"""
        result = base.copy()
        for key, value in env.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
