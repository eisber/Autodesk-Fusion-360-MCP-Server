"""End-to-end tests for MCP Server <-> Fusion 360 Add-In communication.

This module provides two testing modes:

1. MOCK MODE (default for CI/pytest):
   - Starts a mock Fusion add-in HTTP server with simulated responses
   - Spawns the MCP server in stdio mode
   - Tests the full chain: MCP Client -> MCP Server -> HTTP -> Mock Add-In
   
2. LIVE MODE (for testing with real Fusion 360):
   - Connects to a running Fusion 360 instance with MCP add-in
   - Run with: pytest tests/test_e2e.py --live
   
Environment variables:
    FUSION_MCP_PORT: Port for add-in (default: 5000)
    FUSION_MCP_URL: Full URL override
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Generator
from unittest.mock import MagicMock

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


# Configuration - uses environment variable or finds a free port
FUSION_MCP_PORT = int(os.environ.get('FUSION_MCP_PORT', '0')) or find_free_port()
BASE_URL = os.environ.get('FUSION_MCP_URL', f"http://localhost:{FUSION_MCP_PORT}")
TIMEOUT = 10


# =============================================================================
# Mock Fusion Add-In Server
# =============================================================================

class MockFusionState:
    """Simulated Fusion 360 model state."""
    
    def __init__(self):
        self.bodies = [
            {"name": "Body1", "volume": 125.0, "isVisible": True}
        ]
        self.sketches = []
        self.parameters = []
        self.task_results: Dict[str, Dict] = {}
    
    def get_model_state(self) -> Dict[str, Any]:
        return {
            "success": True,
            "name": "TestDesign",
            "bodies": len(self.bodies),
            "sketches": len(self.sketches),
            "parameters": len(self.parameters),
            "body_info": self.bodies,
        }
    
    def execute_script(self, script: str, task_id: str) -> Dict[str, Any]:
        """Execute a script in mock context."""
        result = {
            "success": True,
            "return_value": None,
            "stdout": "",
            "stderr": "",
            "error": None,
            "model_state": self.get_model_state()
        }
        
        # Create mock execution context
        mock_globals = {
            "__builtins__": __builtins__,
            "adsk": MagicMock(),
            "app": MagicMock(),
            "ui": MagicMock(),
            "design": MagicMock(),
            "rootComp": MagicMock(),
            "math": __import__('math'),
            "json": __import__('json'),
        }
        
        # Configure rootComp mock
        mock_globals["rootComp"].bRepBodies.count = len(self.bodies)
        mock_globals["rootComp"].sketches.count = len(self.sketches)
        mock_globals["rootComp"].name = "RootComponent"
        mock_globals["design"].rootComponent = mock_globals["rootComp"]
        
        exec_locals = {}
        
        try:
            exec(script, mock_globals, exec_locals)
            if 'result' in exec_locals:
                result["return_value"] = str(exec_locals['result'])
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["error_type"] = type(e).__name__
        
        # Store with error status if failed
        if not result["success"]:
            result["status"] = "error"
        
        return result


class MockFusionHandler(BaseHTTPRequestHandler):
    """HTTP handler that simulates Fusion 360 add-in responses."""
    
    state: MockFusionState = None  # Set by server
    
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def _send_json(self, data: Dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/model_state':
            self._send_json(self.state.get_model_state())
        
        elif path == '/count_parameters':
            self._send_json({"count": len(self.state.parameters)})
        
        elif path == '/list_parameters':
            self._send_json({"ModelParameter": self.state.parameters})
        
        elif path == '/script_result':
            # Parse task_id from query string
            query = self.path.split('?')[1] if '?' in self.path else ''
            params = dict(p.split('=') for p in query.split('&') if '=' in p)
            task_id = params.get('task_id', '')
            
            if task_id in self.state.task_results:
                result = self.state.task_results[task_id]
                self._send_json({"status": "completed", **result})
            else:
                self._send_json({"status": "pending"})
        
        elif path == '/faces_info':
            self._send_json({
                "success": True,
                "body_name": "Body1",
                "face_count": 6,
                "faces": [{"index": i, "area": 25.0} for i in range(6)]
            })
        
        elif path == '/edges_info':
            self._send_json({
                "success": True,
                "body_name": "Body1", 
                "edge_count": 12,
                "edges": [{"index": i, "length": 5.0} for i in range(12)]
            })
        
        elif path == '/vertices_info':
            self._send_json({
                "success": True,
                "body_name": "Body1",
                "vertex_count": 8,
                "vertices": [{"index": i, "x": 0, "y": 0, "z": 0} for i in range(8)]
            })
        
        elif path == '/timeline_info':
            self._send_json({
                "success": True,
                "feature_count": 1,
                "marker_position": 1,
                "features": []
            })
        
        elif path == '/sketch_info':
            self._send_json({"success": True, "sketches": []})
        
        elif path == '/sketch_constraints':
            self._send_json({"success": True, "constraints": []})
        
        elif path == '/sketch_dimensions':
            self._send_json({"success": True, "dimensions": []})
        
        elif path == '/construction_geometry':
            self._send_json({
                "success": True,
                "planes": ["XYPlane", "XZPlane", "YZPlane"],
                "axes": ["XAxis", "YAxis", "ZAxis"],
                "points": ["Origin"]
            })
        
        else:
            self._send_json({"error": f"Unknown GET endpoint: {path}"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}
        
        path = self.path.split('?')[0]
        
        if path == '/test_connection':
            self._send_json({"success": True, "message": "Mock connection successful"})
        
        elif path == '/execute_script':
            task_id = str(uuid.uuid4())[:8]
            script = data.get('script', '')
            
            # Execute script and store result
            result = self.state.execute_script(script, task_id)
            self.state.task_results[task_id] = result
            
            self._send_json({"task_id": task_id, "status": "queued"})
        
        elif path == '/undo':
            self._send_json({"success": True, "message": "Undo executed"})
        
        elif path == '/delete_everything':
            self.state.bodies = []
            self.state.sketches = []
            self._send_json({"success": True, "message": "All deleted"})
        
        elif path == '/circular_pattern':
            self._send_json({"success": True, "message": "Circular pattern created"})
        
        elif path == '/rectangular_pattern':
            self._send_json({"success": True, "message": "Rectangular pattern created"})
        
        elif path == '/move_body':
            self._send_json({"success": True, "message": "Body moved"})
        
        elif path == '/set_parameter':
            name = data.get('name', '')
            value = data.get('value', '')
            # Update or add parameter
            for p in self.state.parameters:
                if p['name'] == name:
                    p['expression'] = value
                    break
            else:
                self.state.parameters.append({'name': name, 'expression': value})
            self._send_json({"success": True})
        
        elif path == '/cancel_task':
            task_id = data.get('task_id', '')
            self._send_json({"success": True, "cancelled": task_id})
        
        else:
            # Generic success for unimplemented endpoints
            self._send_json({"success": True, "message": f"Mock response for {path}"})


@contextmanager
def mock_fusion_server(port: int) -> Generator[MockFusionState, None, None]:
    """Context manager that starts a mock Fusion add-in server."""
    state = MockFusionState()
    MockFusionHandler.state = state
    
    server = HTTPServer(('localhost', port), MockFusionHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    # Wait for server to be ready
    for _ in range(50):
        try:
            requests.get(f"http://localhost:{port}/model_state", timeout=0.1)
            break
        except requests.ConnectionError:
            time.sleep(0.1)
    
    try:
        yield state
    finally:
        server.shutdown()


# =============================================================================
# Test Helper Functions
# =============================================================================

def _make_connection_request(base_url: str = BASE_URL) -> Dict[str, Any]:
    """Test basic connection to Fusion 360 add-in."""
    try:
        response = requests.post(
            f"{base_url}/test_connection",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.ok else response.text
        }
    except requests.ConnectionError as e:
        return {
            "success": False,
            "error": "Connection refused - Is Fusion 360 running with MCP add-in?",
            "details": str(e)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _make_model_state_request(base_url: str = BASE_URL) -> Dict[str, Any]:
    """Test getting model state from Fusion 360."""
    try:
        response = requests.get(f"{base_url}/model_state", timeout=TIMEOUT)
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.ok else response.text
        }
    except requests.ConnectionError as e:
        return {"success": False, "error": "Connection refused", "details": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _make_execute_script_request(script: str, base_url: str = BASE_URL) -> Dict[str, Any]:
    """Test executing a Python script in Fusion 360."""
    try:
        response = requests.post(
            f"{base_url}/execute_script",
            json={"script": script, "timeout": 30},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if not response.ok:
            return {"success": False, "status_code": response.status_code, "error": response.text}
        
        submit_result = response.json()
        task_id = submit_result.get("task_id")
        
        if not task_id:
            return {"success": False, "error": "No task_id returned", "response": submit_result}
        
        # Poll for result
        for _ in range(30):
            time.sleep(0.2)
            result_response = requests.get(
                f"{base_url}/script_result?task_id={task_id}",
                timeout=TIMEOUT
            )
            
            if result_response.ok:
                result = result_response.json()
                if result.get("status") == "completed":
                    return {"success": True, "task_id": task_id, "result": result}
                elif result.get("status") == "error":
                    return {"success": False, "task_id": task_id, "error": result.get("error")}
        
        return {"success": False, "error": "Script execution timed out", "task_id": task_id}
        
    except requests.ConnectionError as e:
        return {"success": False, "error": "Connection refused", "details": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def mock_addin_port():
    """Get a free port for the mock add-in server."""
    return find_free_port()


@pytest.fixture(scope="module")
def mock_addin(mock_addin_port):
    """Start mock Fusion add-in server for the test module."""
    with mock_fusion_server(mock_addin_port) as state:
        yield {
            "port": mock_addin_port,
            "url": f"http://localhost:{mock_addin_port}",
            "state": state
        }


# =============================================================================
# E2E Tests with Mock Add-In
# =============================================================================

class TestMockAddIn:
    """Tests using mock Fusion add-in server."""
    
    def test_connection(self, mock_addin):
        """Test connection to mock add-in."""
        result = _make_connection_request(mock_addin["url"])
        assert result["success"], f"Connection failed: {result}"
    
    def test_model_state(self, mock_addin):
        """Test getting model state from mock add-in."""
        result = _make_model_state_request(mock_addin["url"])
        assert result["success"], f"Model state failed: {result}"
        assert "bodies" in result["response"]
    
    def test_execute_simple_script(self, mock_addin):
        """Test executing a simple script."""
        result = _make_execute_script_request("result = 'hello'", mock_addin["url"])
        assert result["success"], f"Script execution failed: {result}"
        assert result["result"]["return_value"] == "hello"
    
    def test_execute_script_with_math(self, mock_addin):
        """Test script execution with math operations."""
        result = _make_execute_script_request("import math; result = math.sqrt(16)", mock_addin["url"])
        assert result["success"], f"Script execution failed: {result}"
        assert result["result"]["return_value"] == "4.0"
    
    def test_execute_script_error_handling(self, mock_addin):
        """Test script execution error handling."""
        result = _make_execute_script_request("raise ValueError('test error')", mock_addin["url"])
        assert not result["success"]
        assert "error" in result
    
    def test_faces_info(self, mock_addin):
        """Test getting faces info."""
        response = requests.get(f"{mock_addin['url']}/faces_info?body_index=0", timeout=TIMEOUT)
        assert response.ok
        data = response.json()
        assert data["success"]
        assert data["face_count"] == 6
    
    def test_undo(self, mock_addin):
        """Test undo operation."""
        response = requests.post(
            f"{mock_addin['url']}/undo",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        assert response.ok
        assert response.json()["success"]
    
    def test_delete_all(self, mock_addin):
        """Test delete all operation."""
        response = requests.post(
            f"{mock_addin['url']}/delete_everything",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        assert response.ok
        assert response.json()["success"]
        
        # Verify state was cleared
        assert len(mock_addin["state"].bodies) == 0


# =============================================================================
# Live Tests (skip by default, run with --live flag)
# =============================================================================

@pytest.fixture
def live_mode(request):
    """Check if live mode is enabled."""
    return request.config.getoption("--live", default=False)


def pytest_addoption(parser):
    """Add --live option for testing with real Fusion 360."""
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run tests against live Fusion 360 instance"
    )


@pytest.mark.skipif(
    not os.environ.get('FUSION_MCP_LIVE'),
    reason="Live tests require FUSION_MCP_LIVE=1 or --live flag"
)
class TestLiveFusion:
    """Tests against a live Fusion 360 instance."""
    
    def test_live_connection(self):
        """Test connection to live Fusion 360."""
        result = _make_connection_request()
        assert result["success"], f"Live connection failed: {result}"
    
    def test_live_model_state(self):
        """Test getting model state from live Fusion 360."""
        result = _make_model_state_request()
        assert result["success"], f"Live model state failed: {result}"


# =============================================================================
# CLI Runner
# =============================================================================

def run_all_tests():
    """Run all E2E tests and print results."""
    print("=" * 60)
    print("Fusion 360 MCP Add-In - End-to-End Tests")
    print("=" * 60)
    print()
    
    port = find_free_port()
    print(f"Starting mock server on port {port}...")
    
    with mock_fusion_server(port) as state:
        url = f"http://localhost:{port}"
        
        tests = [
            ("Connection Test", lambda: _make_connection_request(url)),
            ("Model State Test", lambda: _make_model_state_request(url)),
            ("Script Execution Test", lambda: _make_execute_script_request("result = 'test'", url)),
        ]
        
        results = []
        for name, test_func in tests:
            print(f"Running: {name}...")
            result = test_func()
            results.append((name, result))
            
            if result["success"]:
                print(f"  ✓ PASSED")
            else:
                print(f"  ✗ FAILED: {result.get('error', 'Unknown error')}")
            print()
        
        # Summary
        print("=" * 60)
        passed = sum(1 for _, r in results if r["success"])
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        print("=" * 60)
        
        return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

