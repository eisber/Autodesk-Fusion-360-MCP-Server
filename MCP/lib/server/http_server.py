"""HTTP Server for Fusion 360 MCP Add-In.

This module provides a route-based HTTP server that dispatches requests
to the appropriate handlers. Replaces boilerplate if/elif chains.
"""

import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Debug logging
_THIS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEBUG_LOG = os.path.join(_THIS_DIR, "mcp_debug.log")

def _log_debug(msg):
    """Write debug message to log file."""
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - [HTTP] {msg}\n")
    except:
        pass


class RouteRegistry:
    """Registry for HTTP routes with automatic dispatching."""
    
    def __init__(self):
        self.get_routes = {}
        self.post_routes = {}
    
    def get(self, path):
        """Decorator to register a GET route."""
        def decorator(func):
            self.get_routes[path] = func
            return func
        return decorator
    
    def post(self, path):
        """Decorator to register a POST route."""
        def decorator(func):
            self.post_routes[path] = func
            return func
        return decorator
    
    def match_route(self, routes, path):
        """Find a matching route, supporting query string paths."""
        # Exact match first
        if path in routes:
            return routes[path], path
        
        # Try without query string
        base_path = path.split('?')[0]
        if base_path in routes:
            return routes[base_path], base_path
        
        # Try prefix matching for paths with query strings
        for route_path, handler in routes.items():
            if path.startswith(route_path):
                return handler, route_path
        
        return None, None


# Global route registry
routes = RouteRegistry()


def create_handler_class(design_getter, task_queue, result_queue, script_result_getter):
    """
    Factory function to create HTTP handler class with access to Fusion state.
    
    Args:
        design_getter: Callable that returns current Fusion design
        task_queue: Queue for sending tasks to Fusion main thread
        result_queue: Queue for receiving results from tasks
        script_result_getter: Callable that returns script execution result
    """
    
    class MCPHandler(BaseHTTPRequestHandler):
        def send_json(self, data, status=200):
            """Helper to send JSON response."""
            _log_debug(f"  Sending JSON response (status={status}): {str(data)[:200]}...")
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        
        def parse_query_params(self):
            """Parse query parameters from URL."""
            query = urllib.parse.urlparse(self.path).query
            return urllib.parse.parse_qs(query)
        
        def get_json_body(self):
            """Parse JSON body from POST request."""
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            return json.loads(post_data) if post_data else {}
        
        def send_task_and_wait(self, task_tuple, success_message, timeout=10.0):
            """Queue a task, wait for result, and send appropriate response."""
            import queue as q
            
            # Clear any stale results
            while not result_queue.empty():
                try:
                    result_queue.get_nowait()
                except q.Empty:
                    break
            
            # Queue the task
            task_queue.put(task_tuple)
            
            # Wait for result
            try:
                result = result_queue.get(timeout=timeout)
            except q.Empty:
                result = {"success": False, "error": "Task timed out"}
            
            if result.get("success"):
                self.send_json({"success": True, "message": success_message})
            else:
                self.send_json(
                    {"success": False, "error": result.get("error", "Unknown error")},
                    status=500
                )
        
        def do_GET(self):
            _log_debug(f"GET request: {self.path}")
            try:
                handler, matched_path = routes.match_route(routes.get_routes, self.path)
                _log_debug(f"  Matched handler: {handler}, path: {matched_path}")
                if handler:
                    handler(self, design_getter())
                    _log_debug(f"  GET completed successfully")
                else:
                    _log_debug(f"  404 Not Found")
                    self.send_error(404, 'Not Found')
            except Exception as e:
                _log_debug(f"  GET error: {e}")
                self.send_error(500, str(e))
        
        def do_POST(self):
            _log_debug(f"POST request: {self.path}")
            try:
                path = self.path.split('?')[0]
                handler, matched_path = routes.match_route(routes.post_routes, path)
                _log_debug(f"  Matched handler: {handler}, path: {matched_path}")
                if handler:
                    data = self.get_json_body()
                    _log_debug(f"  Request data keys: {list(data.keys()) if data else 'empty'}")
                    handler(self, design_getter(), data)
                    _log_debug(f"  POST completed successfully")
                else:
                    _log_debug(f"  404 Not Found")
                    self.send_error(404, 'Not Found')
            except Exception as e:
                _log_debug(f"  POST error: {e}")
                self.send_error(500, str(e))
    
    return MCPHandler
