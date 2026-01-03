"""Configuration for the Fusion 360 MCP Server."""

import os

# Port configuration - can be overridden via environment variable
FUSION_MCP_PORT = int(os.environ.get('FUSION_MCP_PORT', '5000'))

# Base URL for the Fusion 360 Add-In HTTP server
BASE_URL = os.environ.get('FUSION_MCP_URL', f"http://localhost:{FUSION_MCP_PORT}")


def endpoint(name: str) -> str:
    """Get the full URL for an endpoint name."""
    return f"{BASE_URL}/{name}"


# Legacy ENDPOINTS dict - kept for backwards compatibility
# New code should use @fusion_tool decorator or endpoint() function
ENDPOINTS = {
    "model_state": f"{BASE_URL}/model_state",
    "execute_script": f"{BASE_URL}/execute_script",
    "script_result": f"{BASE_URL}/script_result",
    "undo": f"{BASE_URL}/undo",
}

# Request Headers
HEADERS = {
    "Content-Type": "application/json"
}

# Timeouts (in seconds)
REQUEST_TIMEOUT = 30
SCRIPT_EXECUTION_TIMEOUT = 30
SCRIPT_POLL_INTERVAL = 0.3

# Test storage configuration
# Tests and snapshots are stored per-project in this directory
TEST_STORAGE_PATH = os.path.join(
    os.environ.get('USERPROFILE', os.path.expanduser('~')),
    'Desktop',
    'Fusion_Tests'
)
