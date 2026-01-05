# FusionMCP Server Package
"""Fusion 360 MCP Server - Model Context Protocol server for Fusion 360."""

__version__ = "0.1.0"

from .client import send_get_request, send_request
from .config import BASE_URL, ENDPOINTS, HEADERS, REQUEST_TIMEOUT
from .instructions import SYSTEM_INSTRUCTIONS
from .prompts import PROMPTS

__all__ = [
    "BASE_URL",
    "ENDPOINTS",
    "HEADERS",
    "PROMPTS",
    "REQUEST_TIMEOUT",
    "SYSTEM_INSTRUCTIONS",
    "send_get_request",
    "send_request",
]
