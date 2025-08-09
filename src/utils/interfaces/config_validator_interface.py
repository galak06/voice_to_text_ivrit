"""
Config Validator Interface
Defines the contract for configuration validation operations
Following Interface Segregation Principle (ISP)
"""

from typing import Protocol, Dict, Any, List


class ConfigValidatorInterface(Protocol):
    """Protocol for configuration validation operations"""
    
    def validate_required_fields(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate that all required fields are present
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of missing required field names
        """
        ...
    
    def validate_field_types(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate that fields have correct types
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of type validation error messages
        """
        ...
    
    def validate_paths(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate that file/directory paths exist and are accessible
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of path validation error messages
        """
        ...
    
    def validate_consistency(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration consistency and dependencies
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of consistency validation error messages
        """
        ...
