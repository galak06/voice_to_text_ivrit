"""
RunPod Endpoint Interface
Defines the contract for RunPod endpoint operations
"""

from typing import Dict, Any, Protocol


class RunPodEndpointInterface(Protocol):
    """Protocol for RunPod endpoint operations"""
    
    def run(self, request_input: Dict[str, Any]) -> Any:
        """
        Run transcription request
        
        Args:
            request_input: The request input to send to the endpoint
            
        Returns:
            The result from the endpoint
        """
        ... 