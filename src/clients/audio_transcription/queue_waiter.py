"""
Queue waiter implementations
"""

import time


class QueueWaiter:
    """Handles waiting for RunPod queue processing"""
    
    def wait_for_queue(self, run_request, timeout_seconds: int = 300) -> str:
        """Wait for task to be queued and return status"""
        status = "UNKNOWN"
        for i in range(timeout_seconds):
            status = run_request.status()
            if status == "IN_QUEUE":
                time.sleep(1)
                continue
            break
        
        return status 