"""HTTP client utilities for communicating with Fusion 360 Add-In server.

Note: Most tools now use @fusion_tool decorator from tools/base.py.
These functions are only used by testing.py and scripting.py for special cases.
"""

import json
import logging
from typing import Any

import requests

from .config import HEADERS, REQUEST_TIMEOUT


def send_request(
    endpoint: str, data: dict[str, Any], headers: dict[str, str] | None = None
) -> dict[str, Any]:
    """
    Send a POST request to the Fusion 360 server.

    Args:
        endpoint: The API endpoint URL
        data: The payload data to send (should include 'command' key)
        headers: Optional headers to include (defaults to JSON content-type)

    Returns:
        JSON response from the server

    Raises:
        requests.RequestException: If the request fails after retries
        json.JSONDecodeError: If the response is not valid JSON
    """
    max_retries = 3
    headers = headers or HEADERS
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            json_data = json.dumps(data)
            response = requests.post(endpoint, json_data, headers=headers, timeout=REQUEST_TIMEOUT)

            try:
                result: dict[str, Any] = response.json()
                return result
            except json.JSONDecodeError as e:
                logging.error("Failed to decode JSON response: %s", e)
                raise

        except requests.RequestException as e:
            logging.error("Request failed on attempt %d: %s", attempt + 1, e)
            last_exception = e
            if attempt == max_retries - 1:
                raise

        except Exception as e:
            logging.error("Unexpected error: %s", e)
            raise

    # This should never be reached due to the raise in the loop,
    # but mypy needs it for type checking
    raise last_exception or RuntimeError("Request failed after retries")


def send_get_request(endpoint: str, timeout: int = REQUEST_TIMEOUT) -> dict[str, Any]:
    """
    Send a GET request to the Fusion 360 server.

    Args:
        endpoint: The API endpoint URL
        timeout: Request timeout in seconds

    Returns:
        JSON response from the server

    Raises:
        requests.RequestException: If the request fails
    """
    try:
        response = requests.get(endpoint, timeout=timeout)
        result: dict[str, Any] = response.json()
        return result
    except requests.RequestException as e:
        logging.error("GET request failed: %s", e)
        raise
