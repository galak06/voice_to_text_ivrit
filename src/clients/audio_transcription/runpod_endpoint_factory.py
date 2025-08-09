"""
RunPod endpoint factory implementations
"""

# Import centralized dependency management
from ...utils.dependency_manager import dependency_manager

from src.core.interfaces import RunPodEndpointFactoryInterface, RunPodEndpointInterface


class DefaultRunPodEndpointFactory(RunPodEndpointFactoryInterface):
    """Default implementation of RunPod endpoint factory"""
    
    def create_endpoint(self, endpoint_id: str) -> RunPodEndpointInterface:
        """Create a RunPod endpoint"""
        if not dependency_manager.is_available('runpod'):
            raise ImportError("RunPod module not available. Please install it with: pip install runpod")
        
        runpod = dependency_manager.get_module('runpod')
        return runpod.Endpoint(endpoint_id) 