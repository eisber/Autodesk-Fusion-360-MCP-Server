"""HTTP Server for Fusion 360 MCP Add-In.

This module provides a route-based HTTP server that dispatches requests
to the appropriate handlers. Replaces boilerplate if/elif chains.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse


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
            try:
                handler, matched_path = routes.match_route(routes.get_routes, self.path)
                if handler:
                    handler(self, design_getter())
                else:
                    self.send_error(404, 'Not Found')
            except Exception as e:
                self.send_error(500, str(e))
        
        def do_POST(self):
            try:
                path = self.path.split('?')[0]
                handler, matched_path = routes.match_route(routes.post_routes, path)
                if handler:
                    data = self.get_json_body()
                    handler(self, design_getter(), data)
                else:
                    self.send_error(404, 'Not Found')
            except Exception as e:
                self.send_error(500, str(e))
    
    return MCPHandler
