"""
Config Loader Interface
Defines the contract for configuration loading operations
Following Interface Segregation Principle (ISP)
"""

from typing import Protocol, Dict, Any
from pathlib import Path


class ConfigLoaderInterface(Protocol):
    """Protocol for configuration loading operations"""
    
    def load_base_config(self) -> Dict[str, Any]:
        """
        Load base configuration file
        
        Returns:
            Base configuration dictionary
            
        Raises:
            FileNotFoundError: If base config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        ...
    
    def load_environment_config(self, environment: str) -> Dict[str, Any]:
        """
        Load environment-specific configuration
        
        Args:
            environment: Environment name (e.g., 'development', 'production')
            
        Returns:
            Environment configuration dictionary
            
        Raises:
            FileNotFoundError: If environment config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        ...
    
    def merge_configs(self, base_config: Dict[str, Any], 
                     env_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge base and environment configurations
        
        Args:
            base_config: Base configuration dictionary
            env_config: Environment configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        ...
