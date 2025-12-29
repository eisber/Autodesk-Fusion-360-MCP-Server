# FusionMCP Server Package
"""Fusion 360 MCP Server - Model Context Protocol server for Fusion 360."""

__version__ = "0.1.0"

from .client import send_request, send_get_request
from .config import ENDPOINTS, HEADERS, BASE_URL, REQUEST_TIMEOUT
from .instructions import SYSTEM_INSTRUCTIONS
from .prompts import PROMPTS

__all__ = [
    "send_request",
    "send_get_request",
    "ENDPOINTS",
    "HEADERS",
    "BASE_URL",
    "REQUEST_TIMEOUT",
    "SYSTEM_INSTRUCTIONS",
    "PROMPTS",
]
