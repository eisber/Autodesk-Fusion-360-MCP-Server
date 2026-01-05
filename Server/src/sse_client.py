"""SSE Client for communicating with Fusion 360 Add-In.

Replaces polling with real-time event streaming for task updates.
"""

import json
import logging
import queue
import threading
import time
from collections.abc import Callable, Generator
from typing import Any

import requests

from .config import BASE_URL


class SSEClient:
    """Client for receiving Server-Sent Events from Fusion 360 Add-In."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.events_url = f"{base_url}/events"

    def stream_events(
        self, task_id: str | None = None, timeout: float = 300.0
    ) -> Generator[dict[str, Any], None, None]:
        """Stream SSE events from the add-in.

        Args:
            task_id: Optional task ID to filter events for
            timeout: Connection timeout in seconds

        Yields:
            Event dictionaries with 'event' and 'data' keys
        """
        url = self.events_url
        if task_id:
            url = f"{url}?task_id={task_id}"

        try:
            with requests.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()

                event_type = None
                event_data = []

                # Use chunk_size=1 to get lines as they arrive (SSE requires immediate streaming)
                for line in response.iter_lines(decode_unicode=True, chunk_size=1):
                    if line is None:
                        continue

                    line = line.strip() if isinstance(line, str) else line.decode("utf-8").strip()

                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        event_data.append(line[5:].strip())
                    elif line == "" and event_type:
                        # End of event
                        try:
                            data = json.loads("".join(event_data)) if event_data else {}
                            yield {"event": event_type, "data": data}
                        except json.JSONDecodeError:
                            logging.warning("Failed to parse SSE data: %s", event_data)

                        event_type = None
                        event_data = []

        except requests.RequestException as e:
            logging.error("SSE connection failed: %s", e)
            raise


def submit_task_and_wait(
    endpoint: str,
    data: dict[str, Any],
    timeout: float = 300.0,
    on_progress: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """Submit a task and wait for completion via SSE.

    This uses SSE-first architecture to avoid race conditions:
    1. Connect to SSE stream (background thread)
    2. Submit the task via POST
    3. Match task_id from task_created event
    4. Wait for task_completed/task_failed

    Args:
        endpoint: Full URL of the endpoint to POST to
        data: Request data (must include 'command')
        timeout: Maximum time to wait for completion
        on_progress: Optional callback for progress updates (percent, message)

    Returns:
        Final result from the task

    Raises:
        TimeoutError: If task doesn't complete within timeout
        requests.RequestException: On connection errors
    """
    # Extract base_url from endpoint
    # endpoint is like "http://localhost:12121/execute"
    base_url = endpoint.rsplit("/", 1)[0]

    # Queue for receiving events from SSE thread
    event_queue: queue.Queue = queue.Queue()
    stop_event = threading.Event()
    sse_error: list = []  # Store any SSE errors

    def sse_listener():
        """Background thread to listen for SSE events."""
        try:
            client = SSEClient(base_url=base_url)
            # Stream ALL events (no task_id filter) so we catch task_created
            for event in client.stream_events(timeout=timeout):
                if stop_event.is_set():
                    break
                event_queue.put(event)
        except Exception as e:
            sse_error.append(e)
            event_queue.put({"event": "error", "data": {"error": str(e)}})

    # Start SSE listener BEFORE submitting task
    sse_thread = threading.Thread(target=sse_listener, daemon=True)
    sse_thread.start()

    # Give SSE a moment to connect
    time.sleep(0.05)

    # Submit the task
    response = requests.post(endpoint, json=data, timeout=10)
    response.raise_for_status()

    submit_result: dict[str, Any] = response.json()
    task_id = submit_result.get("task_id")

    if not task_id:
        # Legacy response without task_id - return as-is
        stop_event.set()
        return submit_result

    # Wait for events related to our task
    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

            try:
                # Wait for next event with remaining timeout
                remaining = timeout - elapsed
                event = event_queue.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                continue

            event_type = event.get("event")
            event_data: dict[str, Any] = event.get("data", {})

            # Filter events for our task_id
            event_task_id = event_data.get("task_id")
            if event_task_id and event_task_id != task_id:
                continue  # Event for a different task

            if event_type == "task_progress" and on_progress:
                on_progress(event_data.get("progress", 0), event_data.get("message", ""))

            elif event_type == "task_completed":
                result: dict[str, Any] = event_data.get("result", {"success": True})
                return result

            elif event_type == "task_failed":
                return {"success": False, "error": event_data.get("error", "Task failed")}

            elif event_type == "task_cancelled":
                return {"success": False, "error": "Task was cancelled"}

            elif event_type == "error":
                raise RuntimeError(f"SSE error: {event_data.get('error')}")

            elif event_type == "keepalive":
                continue
    finally:
        stop_event.set()


def cancel_task(task_id: str, base_url: str = BASE_URL) -> dict[str, Any]:
    """Cancel a running task.

    Args:
        task_id: ID of the task to cancel
        base_url: Base URL of the add-in server

    Returns:
        Response indicating success/failure
    """
    url = f"{base_url}/task/{task_id}"
    response = requests.delete(url, timeout=10)
    result: dict[str, Any] = response.json()
    return result


def get_task_status(task_id: str, base_url: str = BASE_URL) -> dict[str, Any]:
    """Get current status of a task.

    Args:
        task_id: ID of the task to check
        base_url: Base URL of the add-in server

    Returns:
        Task status information
    """
    url = f"{base_url}/task_status?task_id={task_id}"
    response = requests.get(url, timeout=10)
    result: dict[str, Any] = response.json()
    return result
