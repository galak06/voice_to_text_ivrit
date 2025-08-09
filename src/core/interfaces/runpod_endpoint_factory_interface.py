"""
RunPod Endpoint Factory Interface
Defines the contract for creating RunPod endpoints
"""

from abc import ABC, abstractmethod
from .runpod_endpoint_interface import RunPodEndpointInterface


class RunPodEndpointFactoryInterface(ABC):
    """Abstract factory for creating RunPod endpoints"""
    
    @abstractmethod
    def create_endpoint(self, endpoint_id: str) -> RunPodEndpointInterface:
        """
        Create a RunPod endpoint
        
        Args:
            endpoint_id: The ID of the endpoint to create
            
        Returns:
            A RunPod endpoint instance
        """
        pass 