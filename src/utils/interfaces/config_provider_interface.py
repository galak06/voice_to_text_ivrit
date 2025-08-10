"""
Config Provider Interface
Defines the contract for configuration provider operations
Following Interface Segregation Principle (ISP)
"""

from typing import Protocol, Dict, Any, Optional


class ConfigProviderInterface(Protocol):
    """Protocol for configuration provider operations"""
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration
        
        Returns:
            Current configuration dictionary
        """
        ...
    
    def get_section(self, section_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific configuration section
        
        Args:
            section_name: Name of the configuration section
            
        Returns:
            Configuration section dictionary or None if not found
        """
        ...
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        ...
    
    def reload_config(self) -> bool:
        """
        Reload configuration from source
        
        Returns:
            True if reload successful, False otherwise
        """
        ...
