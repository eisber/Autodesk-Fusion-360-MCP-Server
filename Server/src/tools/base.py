"""Base decorator for Fusion 360 tool functions.

Provides @fusion_tool decorator that combines:
- SSE-based task submission and monitoring (eliminates timeouts)
- Telemetry tracking
- Error logging
- Automatic parameter extraction
- Progress callback support

Usage:
    @fusion_tool
    def measure_distance(entity1_type: str, entity1_index: int, ...):
        '''Docstring becomes the tool description.'''
        pass  # Implementation auto-generated

    @fusion_tool(method="GET")
    def get_faces_info(body_index: int = 0):
        '''GET request with query params.'''
        pass

    @fusion_tool(endpoint="custom_endpoint")
    def my_tool():
        '''Override the endpoint name.'''
        pass

    @fusion_tool(use_sse=False)  # Disable SSE for legacy behavior
    def quick_tool():
        '''Use blocking HTTP instead of SSE.'''
        pass
"""

import inspect
import logging
import time
from collections.abc import Callable
from functools import wraps

import requests

from ..config import BASE_URL, HEADERS, REQUEST_TIMEOUT
from ..sse_client import submit_task_and_wait
from ..telemetry import capture_exception, get_telemetry


def fusion_tool(
    _func: Callable | None = None,
    *,
    endpoint: str | None = None,
    method: str = "POST",
    command: str | None = None,
    use_sse: bool = True,
    timeout: float = 300.0,
) -> Callable | Callable[[Callable], Callable]:
    """
    Decorator that creates a complete Fusion 360 tool from a function signature.

    The function body is ignored - the decorator generates the HTTP call automatically.
    Function parameters become the request data (POST) or query params (GET).

    Can be used with or without arguments:
        @fusion_tool
        def my_tool(...): ...

        @fusion_tool(method="GET")
        def my_tool(...): ...

    Args:
        endpoint: Name of the endpoint (defaults to function name)
        method: HTTP method - "POST" or "GET"
        command: Override the command name sent to add-in (defaults to endpoint)
        use_sse: Use SSE for POST requests (default True) - eliminates timeouts
        timeout: Maximum wait time for SSE completion (default 300s)

    Returns:
        Decorated function that makes HTTP request and tracks telemetry.
    """

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        tool_name = func.__name__
        endpoint_name = endpoint or tool_name
        cmd_name = command or endpoint_name
        endpoint_url = f"{BASE_URL}/{endpoint_name}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            telemetry = get_telemetry()
            start_time = time.time()

            # Bind arguments to parameter names
            try:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                params = dict(bound.arguments)
            except TypeError:
                # Handle **kwargs case - just use kwargs directly
                params = kwargs

            try:
                if method == "GET":
                    # GET requests don't use SSE
                    if params:
                        query = "&".join(f"{k}={v}" for k, v in params.items())
                        url = f"{endpoint_url}?{query}"
                    else:
                        url = endpoint_url
                    response = requests.get(url, timeout=REQUEST_TIMEOUT)
                    result = response.json()
                else:
                    # POST with command + data
                    request_data = {"command": cmd_name, **params}

                    if use_sse:
                        # Use SSE for real-time progress and no timeouts
                        result = submit_task_and_wait(endpoint_url, request_data, timeout=timeout)
                    else:
                        # Legacy blocking POST
                        response = requests.post(
                            endpoint_url,
                            json=request_data,
                            headers=HEADERS,
                            timeout=REQUEST_TIMEOUT,
                        )
                        result = response.json()

                # Track telemetry
                duration_ms = (time.time() - start_time) * 1000
                success = True
                if isinstance(result, dict) and result.get("success") is False:
                    success = False
                    telemetry.track_tool_call(
                        tool_name=tool_name,
                        success=False,
                        duration_ms=duration_ms,
                        error_type=result.get("error_type", "UnknownError"),
                        error_message=result.get("error", ""),
                        parameters=params,
                    )
                else:
                    telemetry.track_tool_call(
                        tool_name=tool_name,
                        success=True,
                        duration_ms=duration_ms,
                        parameters=params,
                    )

                return result

            except requests.RequestException as e:
                duration_ms = (time.time() - start_time) * 1000
                logging.error("%s failed: %s", tool_name, e)
                telemetry.track_tool_call(
                    tool_name=tool_name,
                    success=False,
                    duration_ms=duration_ms,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    parameters=params,
                )
                capture_exception(e, context={"tool_name": tool_name})
                raise
            except TimeoutError as e:
                duration_ms = (time.time() - start_time) * 1000
                logging.error("%s timed out: %s", tool_name, e)
                telemetry.track_tool_call(
                    tool_name=tool_name,
                    success=False,
                    duration_ms=duration_ms,
                    error_type="TimeoutError",
                    error_message=str(e),
                    parameters=params,
                )
                capture_exception(e, context={"tool_name": tool_name})
                return {"success": False, "error": str(e)}
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logging.error("%s failed: %s", tool_name, e)
                telemetry.track_tool_call(
                    tool_name=tool_name,
                    success=False,
                    duration_ms=duration_ms,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    parameters=params,
                )
                capture_exception(e, context={"tool_name": tool_name})
                raise

        return wrapper

    # Support @fusion_tool without parentheses
    if _func is not None:
        return decorator(_func)
    return decorator
