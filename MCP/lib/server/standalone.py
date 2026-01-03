"""Standalone launcher for the MCP Add-In HTTP server.

This module allows running the Add-In HTTP server without Fusion 360,
using mock adsk modules. Useful for testing SSE and HTTP endpoints.

Usage:
    python -m lib.server.standalone [--port PORT]
    
Or from parent directory:
    python -c "from MCP.lib.server.standalone import run_standalone; run_standalone()"
"""

import argparse
import json
import logging
import queue
import sys
import threading
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def install_mock_adsk():
    """Install mock adsk module for standalone operation."""
    if 'adsk' in sys.modules:
        return sys.modules['adsk']
    
    mock_adsk = MagicMock()
    mock_core = MagicMock()
    mock_fusion = MagicMock()
    
    mock_adsk.core = mock_core
    mock_adsk.fusion = mock_fusion
    
    # Mock Application with a realistic interface
    mock_app = MagicMock()
    mock_ui = MagicMock()
    mock_app.userInterface = mock_ui
    
    # Mock Design
    mock_design = MagicMock()
    mock_design.objectType = 'adsk::fusion::Design'
    mock_design.rootComponent = MagicMock()
    mock_design.rootComponent.name = "MockRootComponent"
    mock_design.rootComponent.bRepBodies.count = 0
    mock_design.rootComponent.sketches.count = 0
    mock_design.allParameters = []
    mock_design.userParameters = MagicMock()
    mock_design.userParameters.count = 0
    mock_app.activeProduct = mock_design
    
    # Custom event handlers storage
    _event_handlers: Dict[str, list] = {}
    
    class MockCustomEventArgs:
        def __init__(self, info=""):
            self.additionalInfo = info
    
    def register_custom_event(name):
        event = MagicMock()
        event._name = name
        event._handlers = []
        _event_handlers[name] = event._handlers
        
        def add_handler(handler):
            event._handlers.append(handler)
        event.add = add_handler
        return event
    
    def fire_custom_event(name, info=""):
        if name in _event_handlers:
            args = MockCustomEventArgs(info)
            for handler in _event_handlers[name]:
                try:
                    handler.notify(args)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
    
    def unregister_custom_event(name):
        if name in _event_handlers:
            del _event_handlers[name]
    
    mock_app.registerCustomEvent = register_custom_event
    mock_app.fireCustomEvent = fire_custom_event
    mock_app.unregisterCustomEvent = unregister_custom_event
    
    mock_core.Application.get.return_value = mock_app
    
    # Mock CustomEventHandler as a real class
    class MockCustomEventHandler:
        def __init__(self):
            pass
        def notify(self, args):
            pass
    
    mock_core.CustomEventHandler = MockCustomEventHandler
    
    # Mock enums
    mock_core.PaletteDockingStates = MagicMock()
    mock_core.PaletteDockingStates.PaletteDockStateRight = 1
    mock_core.LogLevels = MagicMock()
    mock_core.LogLevels.InfoLogLevel = 2
    
    mock_fusion.FeatureOperations = MagicMock()
    mock_fusion.FeatureOperations.NewBodyFeatureOperation = 0
    mock_fusion.FeatureOperations.JoinFeatureOperation = 1
    mock_fusion.FeatureOperations.CutFeatureOperation = 2
    
    # Install mocks
    sys.modules['adsk'] = mock_adsk
    sys.modules['adsk.core'] = mock_core
    sys.modules['adsk.fusion'] = mock_fusion
    
    return mock_adsk


# Install mocks before any imports that need adsk
install_mock_adsk()


# Now we can import the SSE module
from .sse import get_task_manager, TaskStatus


class StandaloneHandler(BaseHTTPRequestHandler):
    """HTTP handler for standalone server with SSE support."""
    
    task_queue: queue.Queue = None
    task_manager = None
    
    def log_message(self, format, *args):
        logger.debug(format, *args)
    
    def send_json(self, data: Dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_json_body(self) -> Dict:
        """Parse JSON body from request."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            body = self.rfile.read(content_length)
            return json.loads(body)
        return {}
    
    def do_GET(self):
        """Handle GET requests."""
        path = self.path.split('?')[0]
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = dict(p.split('=') for p in query.split('&') if '=' in p) if query else {}
        
        if path == '/model_state':
            self.send_json({
                "success": True,
                "name": "MockDesign",
                "bodies": 0,
                "sketches": 0,
                "body_info": []
            })
        
        elif path == '/events':
            # SSE endpoint
            self.handle_sse(params.get('task_id'))
        
        elif path == '/list_parameters':
            self.send_json({"ModelParameter": []})
        
        elif path == '/count_parameters':
            self.send_json({"count": 0})
        
        elif path == '/faces_info':
            self.send_json({"success": True, "faces": []})
        
        elif path == '/edges_info':
            self.send_json({"success": True, "edges": []})
        
        elif path == '/vertices_info':
            self.send_json({"success": True, "vertices": []})
        
        elif path == '/script_result':
            task_id = params.get('task_id', '')
            if task_id and self.task_manager:
                task_info = self.task_manager.get_task(task_id)
                if task_info:
                    self.send_json({
                        "status": task_info.status.value,
                        "result": task_info.result,
                        "error": task_info.error
                    })
                else:
                    self.send_json({"status": "not_found"})
            else:
                self.send_json({"status": "pending"})
        
        else:
            self.send_error(404, f"Unknown GET endpoint: {path}")
    
    def do_POST(self):
        """Handle POST requests."""
        path = self.path.split('?')[0]
        
        try:
            data = self.get_json_body()
        except json.JSONDecodeError:
            data = {}
        
        if path == '/test_connection':
            self.send_json({"success": True, "message": "Standalone server"})
        
        elif path == '/execute_script':
            self.handle_execute_script(data)
        
        elif path == '/undo':
            self.send_json({"success": True, "message": "Undo executed"})
        
        elif path == '/delete_everything':
            self.send_json({"success": True, "message": "All deleted"})
        
        elif path == '/set_parameter':
            self.send_json({"success": True})
        
        elif path == '/cancel_task':
            task_id = data.get('task_id', '')
            if task_id and self.task_manager:
                self.task_manager.cancel_task(task_id)
            self.send_json({"success": True, "cancelled": task_id})
        
        else:
            # Generic success for other endpoints
            self.send_json({"success": True, "message": f"Mock response for {path}"})
    
    def handle_execute_script(self, data: Dict):
        """Handle script execution with SSE task management."""
        script = data.get('script', '')
        timeout = data.get('timeout', 30)
        
        # Create task
        task_id = str(uuid.uuid4())[:8]
        
        if self.task_manager:
            self.task_manager.register_task(task_id, "execute_script")
        
        # Queue task for execution
        if self.task_queue:
            self.task_queue.put(('execute_script', script, task_id))
        
        # Return task_id immediately
        self.send_json({"task_id": task_id, "status": "queued"})
    
    def handle_sse(self, task_id_filter: Optional[str]):
        """Handle SSE event streaming."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if not self.task_manager:
            # Send error and close
            self.wfile.write(b'event: error\ndata: {"message": "Task manager not initialized"}\n\n')
            self.wfile.flush()
            return
        
        # Subscribe to ALL events (broadcast model)
        subscriber_id = self.task_manager.subscribe()
        
        try:
            # Send initial connection event
            self.wfile.write(f'event: connected\ndata: {{"subscriber_id": "{subscriber_id}"}}\n\n'.encode())
            self.wfile.flush()
            
            event_queue = self.task_manager.get_event_queue(subscriber_id)
            if not event_queue:
                return
            
            start_time = time.time()
            timeout = 60.0  # Max SSE connection time
            
            while time.time() - start_time < timeout:
                try:
                    event = event_queue.get(timeout=1.0)
                    
                    # Filter by task_id if specified
                    if task_id_filter:
                        event_task_id = event.get("data", {}).get("task_id", "")
                        if event_task_id != task_id_filter:
                            continue
                    
                    # Send SSE event
                    event_type = event.get('event', 'message')
                    event_data = json.dumps(event.get('data', {}))
                    
                    self.wfile.write(f"event: {event_type}\n".encode())
                    self.wfile.write(f"data: {event_data}\n\n".encode())
                    self.wfile.flush()
                    
                    # Close on terminal events for this task
                    if task_id_filter and event_type in ('task_completed', 'task_failed', 'task_cancelled'):
                        break
                        
                except queue.Empty:
                    # Send keepalive
                    self.wfile.write(b'event: keepalive\ndata: {}\n\n')
                    self.wfile.flush()
                    
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.task_manager.unsubscribe(subscriber_id)


class StandaloneTaskExecutor(threading.Thread):
    """Executes tasks from queue without Fusion's custom event system."""
    
    def __init__(self, task_queue: queue.Queue, stop_event: threading.Event, task_manager):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.stop_event = stop_event
        self.task_manager = task_manager
    
    def run(self):
        """Process tasks from the queue."""
        while not self.stop_event.is_set():
            try:
                task = self.task_queue.get(timeout=0.1)
                self._process_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Task executor error: {e}")
    
    def _process_task(self, task: tuple):
        """Process a single task."""
        task_name = task[0]
        
        if task_name == 'execute_script':
            script = task[1] if len(task) > 1 else ""
            task_id = task[2] if len(task) > 2 else None
            
            logger.info(f"Processing script task (id={task_id})")
            
            # Mark as started
            if task_id and self.task_manager:
                self.task_manager.start_task(task_id)
            
            # Check cancellation
            if task_id and self.task_manager and self.task_manager.is_cancelled(task_id):
                logger.info(f"Task {task_id} was cancelled")
                return
            
            # Execute the script
            result = self._execute_script(script, task_id)
            
            # Report completion
            if task_id and self.task_manager:
                if result.get("success", True):
                    self.task_manager.complete_task(task_id, result)
                else:
                    self.task_manager.fail_task(task_id, result.get("error", "Unknown error"))
    
    def _execute_script(self, script: str, task_id: Optional[str]) -> Dict[str, Any]:
        """Execute a Python script in mock context."""
        import math
        
        result = {
            "success": True,
            "return_value": None,
            "stdout": "",
            "stderr": "",
            "model_state": {"bodies": 0, "sketches": 0}
        }
        
        # Create progress function
        progress_fn = None
        if task_id and self.task_manager:
            progress_fn = lambda pct, msg="": self.task_manager.report_progress(task_id, pct, msg)
        
        # Build execution context with mocks
        exec_globals = {
            "__builtins__": __builtins__,
            "adsk": sys.modules['adsk'],
            "app": sys.modules['adsk'].core.Application.get(),
            "ui": sys.modules['adsk'].core.Application.get().userInterface,
            "design": sys.modules['adsk'].core.Application.get().activeProduct,
            "rootComp": sys.modules['adsk'].core.Application.get().activeProduct.rootComponent,
            "math": math,
            "json": json,
            "progress": progress_fn if progress_fn else (lambda pct, msg="": None),
            "is_cancelled": (lambda: self.task_manager.is_cancelled(task_id)) if task_id and self.task_manager else (lambda: False),
        }
        
        exec_locals = {}
        
        try:
            exec(script, exec_globals, exec_locals)
            if 'result' in exec_locals:
                result["return_value"] = str(exec_locals['result'])
        except SyntaxError as e:
            result["success"] = False
            result["error"] = str(e)
            result["error_type"] = "SyntaxError"
            result["error_line"] = e.lineno
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["error_type"] = type(e).__name__
        
        return result


class StandaloneServer:
    """Manages the standalone HTTP server with SSE support."""
    
    def __init__(self, port: int = 5000):
        self.port = port
        self.httpd = None
        self.task_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.task_executor = None
        self.server_thread = None
        self.task_manager = get_task_manager()
    
    def start(self):
        """Start the server and task executor."""
        logger.info(f"Starting standalone MCP Add-In server on port {self.port}")
        
        # Configure handler class
        StandaloneHandler.task_queue = self.task_queue
        StandaloneHandler.task_manager = self.task_manager
        
        # Create and start task executor
        self.task_executor = StandaloneTaskExecutor(
            self.task_queue, 
            self.stop_event,
            self.task_manager
        )
        self.task_executor.start()
        
        # Use ThreadingHTTPServer to handle concurrent requests (needed for SSE + other endpoints)
        self.httpd = ThreadingHTTPServer(('', self.port), StandaloneHandler)
        
        # Start server in background thread
        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()
        
        logger.info(f"Server started on http://localhost:{self.port}")
    
    def stop(self):
        """Stop the server and task executor."""
        logger.info("Stopping standalone server...")
        
        self.stop_event.set()
        
        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None
        
        if self.task_executor:
            self.task_executor.join(timeout=2.0)
        
        logger.info("Server stopped")
    
    def wait(self):
        """Wait for server to be stopped (blocking)."""
        try:
            while not self.stop_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Received interrupt, stopping...")
            self.stop()


def run_standalone(port: int = 5000):
    """Run the standalone server (blocking)."""
    server = StandaloneServer(port=port)
    server.start()
    server.wait()
    return server


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Standalone MCP Add-In Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    args = parser.parse_args()
    
    run_standalone(port=args.port)


if __name__ == "__main__":
    main()
