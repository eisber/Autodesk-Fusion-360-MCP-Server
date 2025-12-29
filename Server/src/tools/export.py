"""Export tools for Fusion 360 MCP Server.

Contains functions for exporting models to various formats.
"""

import logging
import requests

from ..client import send_request
from ..config import ENDPOINTS


def export_step(name: str):
    """
    Export the model as a STEP file.
    
    Args:
        name: Name for the export file/folder
    """
    try:
        endpoint = ENDPOINTS["export_step"]
        data = {"name": name}
        return send_request(endpoint, data, {})
    except requests.RequestException as e:
        logging.error("Export STEP failed: %s", e)
        raise


def export_stl(name: str):
    """
    Export the model as STL files.
    
    Args:
        name: Name for the export folder
    """
    try:
        endpoint = ENDPOINTS["export_stl"]
        data = {"name": name}
        return send_request(endpoint, data, {})
    except requests.RequestException as e:
        logging.error("Export STL failed: %s", e)
        raise
