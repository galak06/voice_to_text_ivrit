# Set up runpod package, and API key
import base64
import os
import requests
import time

# Import centralized dependency management
from src.utils.dependency_manager import dependency_manager

from src.models import AppConfig

def transcribe(model, payload_type, path_or_url, config: AppConfig = None):  
    if not dependency_manager.is_available('runpod'):
        raise ImportError("RunPod module not available. Please install it with: pip install runpod")
    
    if not payload_type in ["blob", "url"]:
        raise 1

    # Use configuration values with defaults
    if config and config.runpod:
        in_queue_timeout = config.runpod.in_queue_timeout
        max_stream_timeouts = config.runpod.max_stream_timeouts
        runpod_max_payload_len = config.runpod.max_payload_size
    else:
        # Default values if no config provided
        # Get constants from configuration
        constants = self.config.system.constants if self.config.system else None
        in_queue_timeout = constants.queue_wait_timeout if constants else 300
        max_stream_timeouts = 5
        runpod_max_payload_len = 200 * 1024 * 1024  # 200MB

    payload = {
        "input": {
            "type": payload_type,
            "model": model,
            "streaming": True
        }
    }

    if payload_type == "blob":
        audio_data = open(path_or_url, 'rb').read()
        payload["input"]["data"] = base64.b64encode(audio_data).decode('utf-8')
    else:
        payload["input"]["url"] = path_or_url

    if len(str(payload)) > runpod_max_payload_len:
        return {"error": f"Payload length is {len(str(payload))}, exceeding max payload length of {runpod_max_payload_len}."}

    # Configure runpod endpoint, and execute
    runpod = dependency_manager.get_module('runpod')
    runpod.api_key = os.environ["RUNPOD_API_KEY"]
    ep = runpod.Endpoint(os.environ["RUNPOD_ENDPOINT_ID"])
    run_request = ep.run(payload)

    # Wait for task to be queued.
    # Max wait time is in_queue_timeout seconds.
    for i in range(in_queue_timeout):
        if run_request.status() == "IN_QUEUE":
            time.sleep(1)
            continue

        break

    # Collect streaming results.
    segments = []

    timeouts = 0
    while True:
        try:
            for segment in run_request.stream():
                if "error" in segment:
                    return segment

                segments.append(segment)

            return segments

        except requests.exceptions.ReadTimeout as e:
            timeouts += 1
            if timeouts > max_stream_timeouts:
                return {"error": f"Number of request.stream() timeouts exceeded the maximum ({max_stream_timeouts})."}
            pass

        except Exception as e:
            run_request.cancel()
            return {"error": f"Exception during run_request.stream(): {e}"}

