"""
Queue waiter implementations
"""

import time
from typing import Any


class QueueWaiter:
    """Handles waiting for queue processing"""
    
    def wait_for_queue(self, run_request, timeout: int = 300) -> bool:
        """
        Wait for task to be queued
        
        Args:
            run_request: RunPod request object
            timeout: Maximum wait time in seconds
            
        Returns:
            True if successfully queued, False if timeout
        """
        for i in range(timeout):
            try:
                status = run_request.status()
                if status == "IN_QUEUE":
                    time.sleep(1)
                    continue
                elif status in ["IN_PROGRESS", "COMPLETED", "FAILED"]:
                    return True
                else:
                    # Unknown status, wait a bit more
                    time.sleep(1)
            except Exception as e:
                # Log error but continue waiting
                time.sleep(1)
        
        return False  # Timeout reached
