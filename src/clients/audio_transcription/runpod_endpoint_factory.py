"""
RunPod endpoint factory implementations
"""

# Optional import for RunPod
try:
    import runpod
    RUNPOD_AVAILABLE = True
except ImportError:
    runpod = None
    RUNPOD_AVAILABLE = False

from .protocols import RunPodEndpointFactory, RunPodEndpoint


class DefaultRunPodEndpointFactory(RunPodEndpointFactory):
    """Default implementation of RunPod endpoint factory"""
    
    def create_endpoint(self, endpoint_id: str) -> RunPodEndpoint:
        """Create a RunPod endpoint"""
        if not RUNPOD_AVAILABLE:
            raise ImportError("RunPod module not available. Please install it with: pip install runpod")
        
        if runpod is None:
            raise RuntimeError("RunPod module not properly imported")
        
        return runpod.Endpoint(endpoint_id) 