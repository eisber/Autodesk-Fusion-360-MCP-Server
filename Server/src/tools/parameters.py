"""Parameter tools for Fusion 360 MCP Server.

Contains functions for managing model parameters.
"""

import logging
import requests

from ..client import send_request
from ..config import ENDPOINTS, HEADERS


def count():
    """Count the parameters in the current model."""
    try:
        endpoint = ENDPOINTS["count_parameters"]
        return send_request(endpoint, {}, {})
    except requests.RequestException as e:
        logging.error("Count failed: %s", e)
        raise


def list_parameters():
    """List all parameters in the current model."""
    try:
        endpoint = ENDPOINTS["list_parameters"]
        return send_request(endpoint, {}, {})
    except requests.RequestException as e:
        logging.error("List parameters failed: %s", e)
        raise


def change_parameter(name: str, value: str):
    """
    Change the value of a parameter.
    
    Args:
        name: Parameter name
        value: New value expression
    """
    try:
        endpoint = ENDPOINTS["change_parameter"]
        data = {
            "name": name,
            "value": value
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Change parameter failed: %s", e)
        raise
