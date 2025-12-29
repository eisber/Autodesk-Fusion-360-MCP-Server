"""HTTP client utilities for communicating with Fusion 360 Add-In server."""

import json
import logging
import requests
from typing import Any, Dict, Optional

from .config import HEADERS, REQUEST_TIMEOUT


def send_request(endpoint: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Send a POST request to the Fusion 360 server.
    
    Args:
        endpoint: The API endpoint URL
        data: The payload data to send in the request
        headers: Optional headers to include (defaults to JSON content-type)
        
    Returns:
        JSON response from the server
        
    Raises:
        requests.RequestException: If the request fails after retries
        json.JSONDecodeError: If the response is not valid JSON
    """
    max_retries = 3
    headers = headers or HEADERS
    
    for attempt in range(max_retries):
        try:
            json_data = json.dumps(data)
            response = requests.post(endpoint, json_data, headers=headers, timeout=REQUEST_TIMEOUT)
            
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logging.error("Failed to decode JSON response: %s", e)
                raise
                
        except requests.RequestException as e:
            logging.error("Request failed on attempt %d: %s", attempt + 1, e)
            if attempt == max_retries - 1:
                raise
                
        except Exception as e:
            logging.error("Unexpected error: %s", e)
            raise


def send_get_request(endpoint: str, timeout: int = REQUEST_TIMEOUT) -> Dict[str, Any]:
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
        return response.json()
    except requests.RequestException as e:
        logging.error("GET request failed: %s", e)
        raise
