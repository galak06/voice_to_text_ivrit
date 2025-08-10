"""
Queue waiter implementations
"""

import time


class QueueWaiter:
    """Handles waiting for RunPod queue processing"""
    
    def wait_for_queue(self, run_request, timeout_seconds: int = None) -> str:
        """
        Wait for queue processing to complete
        
        Args:
            run_request: The run request object
            timeout_seconds: Timeout in seconds (uses config default if None)
            
        Returns:
            The result ID
        """
        # Get timeout from configuration if not provided
        if timeout_seconds is None:
            from src.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            constants = config_manager.config.system.constants if config_manager.config.system else None
            timeout_seconds = constants.queue_wait_timeout if constants else 300
        
        """Wait for task to be queued and return status"""
        status = "UNKNOWN"
        for i in range(timeout_seconds):
            status = run_request.status()
            if status == "IN_QUEUE":
                time.sleep(1)
                continue
            break
        
        return status 