"""
RunPod endpoint factory implementations
"""

from typing import Optional
from src.core.interfaces import RunPodEndpointFactoryInterface, RunPodEndpointInterface
from src.utils.dependency_manager import dependency_manager


class RunPodEndpointFactory(RunPodEndpointFactoryInterface):
    """Default implementation of RunPod endpoint factory"""
    
    def create_endpoint(self, endpoint_id: str, api_key: str) -> Optional[RunPodEndpointInterface]:
        """Create a RunPod endpoint"""
        try:
            if not dependency_manager.is_available('runpod'):
                raise ImportError("RunPod module not available")
            
            runpod = dependency_manager.get_module('runpod')
            runpod.api_key = api_key
            endpoint = runpod.Endpoint(endpoint_id)
            
            return endpoint
            
        except Exception as e:
            # Log error but don't raise - let caller handle
            return None
