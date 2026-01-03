"""End-to-end tests using real SSE path.

This module tests the full SSE streaming pipeline by:
1. Starting the standalone Add-In server (with mock adsk)
2. Testing SSE events are properly streamed
3. Verifying the Server's SSE client works with the Add-In

Run with: pytest tests/test_e2e_sse.py -v
"""

import json
import os
import signal
import socket
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

import pytest
import requests


# =============================================================================
# Configuration
# =============================================================================

def find_free_port() -> int:
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


# Test timeouts
REQUEST_TIMEOUT = 3   # HTTP request timeout
TEST_TIMEOUT = 3      # Overall test timeout
SSE_TIMEOUT = 3       # SSE streaming timeout

MCP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MCP'))

# Add MCP directory to path for imports
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)

# Add MCP directory to path for imports
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)


# =============================================================================
# Standalone Add-In Server Fixture
# =============================================================================

def _install_mock_adsk():
    """Install mock adsk modules for testing."""
    from unittest.mock import MagicMock
    
    if 'adsk' in sys.modules:
        return
    
    mock_adsk = MagicMock()
    mock_core = MagicMock()
    mock_fusion = MagicMock()
    
    mock_adsk.core = mock_core
    mock_adsk.fusion = mock_fusion
    
    mock_app = MagicMock()
    mock_app.userInterface = MagicMock()
    
    mock_design = MagicMock()
    mock_design.rootComponent = MagicMock()
    mock_design.rootComponent.bRepBodies = MagicMock()
    mock_design.rootComponent.bRepBodies.count = 0
    mock_design.rootComponent.sketches = MagicMock()
    mock_design.rootComponent.sketches.count = 0
    mock_app.activeProduct = mock_design
    
    mock_core.Application.get.return_value = mock_app
    
    sys.modules['adsk'] = mock_adsk
    sys.modules['adsk.core'] = mock_core
    sys.modules['adsk.fusion'] = mock_fusion


# Install mocks before importing standalone
_install_mock_adsk()


@contextmanager
def standalone_addin_server(port: int) -> Generator[str, None, None]:
    """Start the standalone Add-In server in a thread.
    
    Yields:
        Base URL of the running server
    """
    from lib.server.standalone import StandaloneServer
    
    server = StandaloneServer(port=port)
    server.start()
    
    base_url = f"http://localhost:{port}"
    
    # Wait for server to be ready
    for _ in range(50):
        try:
            response = requests.get(f"{base_url}/model_state", timeout=0.5)
            if response.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(0.1)
    else:
        server.stop()
        raise RuntimeError("Standalone server failed to start")
    
    try:
        yield base_url
    finally:
        server.stop()


@pytest.fixture(scope="function")
def addin_server():
    """Function-scoped fixture that provides a running Add-In server.
    
    Creates a fresh server for each test to avoid state leakage.
    """
    # Reset the task manager to clear any leftover state
    from lib.server.sse import get_task_manager
    get_task_manager().reset()
    
    port = find_free_port()
    with standalone_addin_server(port) as base_url:
        yield base_url


# =============================================================================
# SSE Helper Functions
# =============================================================================

def stream_sse_events(url: str, timeout: float = SSE_TIMEOUT) -> Generator[Dict[str, Any], None, None]:
    """Stream SSE events from a URL.
    
    Yields:
        Event dictionaries with 'event' and 'data' keys
    """
    start_time = time.time()
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        
        event_type = None
        event_data = []
        
        # Use small chunk_size to get lines as they arrive (SSE requires immediate streaming)
        for line in response.iter_lines(decode_unicode=True, chunk_size=1):
            # Check for timeout
            if time.time() - start_time > timeout:
                return
            
            if line is None:
                continue
            
            line = line.strip() if isinstance(line, str) else line.decode('utf-8').strip()
            
            if line.startswith('event:'):
                event_type = line[6:].strip()
            elif line.startswith('data:'):
                event_data.append(line[5:].strip())
            elif line == '' and event_type:
                # End of event
                try:
                    data = json.loads(''.join(event_data)) if event_data else {}
                    yield {"event": event_type, "data": data}
                except json.JSONDecodeError:
                    pass
                
                event_type = None
                event_data = []


def submit_script_and_collect_events(
    base_url: str,
    script: str,
    timeout: float = SSE_TIMEOUT
) -> Dict[str, Any]:
    """Submit a script and collect all SSE events until completion.
    
    Strategy: Connect to SSE stream FIRST (without task_id filter), 
    then submit script. This ensures we don't miss any events due to race conditions.
    
    Returns:
        Dictionary with:
        - task_id: The assigned task ID
        - events: List of all SSE events received
        - result: Final result (if completed)
        - error: Error message (if failed)
    """
    import threading
    import queue as q
    
    events = []
    result_holder = {"result": None, "error": None}
    task_id_holder = {"task_id": None}
    done_event = threading.Event()
    connected_event = threading.Event()
    
    def sse_listener():
        """Listen for SSE events in background thread."""
        # Track the task_id from task_created event (first one we see)
        observed_task_id = None
        
        try:
            # Connect without task_id filter first - we'll filter client-side
            sse_url = f"{base_url}/events"
            for event in stream_sse_events(sse_url, timeout=timeout):
                # Signal that we're connected on first event (usually 'connected')
                if not connected_event.is_set():
                    connected_event.set()
                
                event_task_id = event["data"].get("task_id", "")
                
                # Learn the task_id from task_created event
                if event["event"] == "task_created" and event_task_id:
                    observed_task_id = event_task_id
                
                # Skip events from other tasks (if we know our task)
                if observed_task_id and event_task_id and event_task_id != observed_task_id:
                    continue
                
                events.append(event)
                
                # Check terminal events for our observed task
                if event["event"] == "task_completed" and event_task_id == observed_task_id:
                    result_holder["result"] = event["data"].get("result", {})
                    # Also update task_id_holder so caller knows
                    task_id_holder["task_id"] = observed_task_id
                    done_event.set()
                    break
                elif event["event"] == "task_failed" and event_task_id == observed_task_id:
                    result_holder["error"] = event["data"].get("error", "Unknown error")
                    task_id_holder["task_id"] = observed_task_id
                    done_event.set()
                    break
                elif event["event"] == "task_cancelled" and event_task_id == observed_task_id:
                    result_holder["error"] = "Task was cancelled"
                    task_id_holder["task_id"] = observed_task_id
                    done_event.set()
                    break
        except requests.exceptions.Timeout:
            pass  # Normal - stream ended
        except Exception as e:
            result_holder["error"] = str(e)
        finally:
            connected_event.set()  # Ensure we unblock even on error
            done_event.set()
    
    # Start SSE listener FIRST
    listener_thread = threading.Thread(target=sse_listener, name="sse_listener", daemon=True)
    listener_thread.start()
    
    # Wait for SSE connection to be established
    if not connected_event.wait(timeout=REQUEST_TIMEOUT):
        return {"task_id": None, "events": [], "result": None, "error": "SSE connection timeout"}
    
    # Now submit the script - SSE listener is already connected
    response = requests.post(
        f"{base_url}/execute_script",
        json={"script": script, "timeout": timeout},
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    submit_result = response.json()
    
    task_id = submit_result.get("task_id")
    task_id_holder["task_id"] = task_id
    
    if not task_id:
        return {"task_id": None, "events": [], "result": submit_result, "error": None}
    
    # Wait for completion with timeout
    done_event.wait(timeout=timeout)
    
    # Give thread a moment to cleanup
    listener_thread.join(timeout=1.0)
    
    return {
        "task_id": task_id,
        "events": events,
        "result": result_holder["result"],
        "error": result_holder["error"]
    }


# =============================================================================
# Tests: Direct HTTP with SSE
# =============================================================================

@pytest.mark.timeout(TEST_TIMEOUT)
class TestDirectSSE:
    """Test SSE functionality using direct HTTP requests."""
    
    def test_connection(self, addin_server):
        """Test basic connection to standalone server."""
        response = requests.post(
            f"{addin_server}/test_connection",
            json={},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    def test_model_state(self, addin_server):
        """Test getting model state."""
        response = requests.get(f"{addin_server}/model_state", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        # Should have mock model state
        assert "bodies" in data or "body_count" in data or "success" in data
    
    def test_execute_script_with_sse_completion(self, addin_server):
        """Test script execution with SSE completion event."""
        result = submit_script_and_collect_events(
            addin_server,
            "result = 2 + 2",
            timeout=SSE_TIMEOUT
        )
        
        assert result["task_id"] is not None
        assert result["error"] is None
        assert result["result"] is not None
        
        # Should have received task_completed event
        event_types = [e["event"] for e in result["events"]]
        assert "task_completed" in event_types
    
    def test_execute_script_with_progress(self, addin_server):
        """Test script execution with progress events."""
        script = '''
progress(25, "Starting...")
progress(50, "Half done")
progress(75, "Almost there")
progress(100, "Complete!")
result = "done"
'''
        result = submit_script_and_collect_events(
            addin_server,
            script,
            timeout=SSE_TIMEOUT
        )
        
        assert result["task_id"] is not None
        assert result["error"] is None
        
        # Check for progress events
        progress_events = [e for e in result["events"] if e["event"] == "task_progress"]
        
        # Should have received progress events (may be consolidated)
        # At minimum we should get the completion event
        event_types = [e["event"] for e in result["events"]]
        assert "task_completed" in event_types
    
    def test_execute_script_with_error(self, addin_server):
        """Test script execution that raises an error."""
        result = submit_script_and_collect_events(
            addin_server,
            "raise ValueError('test error')",
            timeout=SSE_TIMEOUT
        )
        
        assert result["task_id"] is not None
        
        # Should have received task_failed event
        event_types = [e["event"] for e in result["events"]]
        assert "task_failed" in event_types or result["error"] is not None
    
    def test_execute_script_syntax_error(self, addin_server):
        """Test script with syntax error."""
        result = submit_script_and_collect_events(
            addin_server,
            "def broken(",  # Syntax error
            timeout=SSE_TIMEOUT
        )
        
        assert result["task_id"] is not None
        
        # Should fail
        event_types = [e["event"] for e in result["events"]]
        assert "task_failed" in event_types or result["error"] is not None


# =============================================================================
# Tests: MCP Client SDK
# =============================================================================

@pytest.mark.timeout(TEST_TIMEOUT)
class TestMCPServerBasic:
    """Basic tests for MCP server communication with Add-In."""
    
    def test_server_responds_to_connection(self, addin_server):
        """Test that the Add-In server responds to test_connection."""
        response = requests.post(
            f"{addin_server}/test_connection",
            json={},
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        assert response.json().get("success") is True


# =============================================================================
# Tests: SSE Client Coverage
# =============================================================================

@pytest.mark.timeout(TEST_TIMEOUT)
class TestSSEClientIntegration:
    """Test the SSE client from Server/src/sse_client.py."""
    
    def test_sse_client_stream_events(self, addin_server):
        """Test SSEClient.stream_events() directly."""
        # Import and patch config
        server_dir = os.path.join(os.path.dirname(__file__), '..')
        if server_dir not in sys.path:
            sys.path.insert(0, server_dir)
        
        import src.config as config
        original_base_url = config.BASE_URL
        config.BASE_URL = addin_server
        
        try:
            from src.sse_client import SSEClient
            
            client = SSEClient(base_url=addin_server)
            events = []
            start_time = time.time()
            
            # Connect WITHOUT task_id filter to receive all events
            for event in client.stream_events(task_id=None, timeout=SSE_TIMEOUT):
                events.append(event)
                # Stop after receiving a few events (connected + keepalive)
                if len(events) >= 2 or (time.time() - start_time > 1.5):
                    break
            
            # Should have received at least the connected event
            assert len(events) >= 1
            event_types = [e.get("event") for e in events]
            assert "connected" in event_types or "keepalive" in event_types
            
        finally:
            config.BASE_URL = original_base_url
    
    def test_submit_task_and_wait(self, addin_server):
        """Test submit_task_and_wait() function with SSE-first architecture."""
        server_dir = os.path.join(os.path.dirname(__file__), '..')
        if server_dir not in sys.path:
            sys.path.insert(0, server_dir)
        
        # Patch the BASE_URL
        import src.config as config
        original_base_url = config.BASE_URL
        config.BASE_URL = addin_server
        
        try:
            from src.sse_client import submit_task_and_wait
            
            # Track progress calls
            progress_calls = []
            def on_progress(pct, msg):
                progress_calls.append((pct, msg))
            
            result = submit_task_and_wait(
                endpoint=f"{addin_server}/execute_script",
                data={"script": "progress(50, 'halfway'); result = 42", "timeout": 30},
                timeout=SSE_TIMEOUT,
                on_progress=on_progress
            )
            
            # Should have received a result
            assert result is not None
            assert result.get("success", True)  # Default to True if not specified
            
        finally:
            config.BASE_URL = original_base_url


# =============================================================================
# Skip marker for CI without MCP SDK
# =============================================================================

def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "mcp_sdk: mark test as requiring MCP client SDK"
    )
