"""Task dispatcher for Fusion 360 MCP Add-In.

Maps task names to handler functions, eliminating giant if/elif chains.
"""


class TaskDispatcher:
    """Registry for task handlers with automatic dispatching."""
    
    def __init__(self):
        self.handlers = {}
    
    def register(self, name):
        """Decorator to register a task handler."""
        def decorator(func):
            self.handlers[name] = func
            return func
        return decorator
    
    def dispatch(self, task_name, design, *args):
        """
        Dispatch a task to its handler.
        
        Args:
            task_name: Name of the task to execute
            design: Fusion 360 design object
            *args: Arguments to pass to the handler
        
        Returns:
            dict with success status and optional error message
        """
        handler = self.handlers.get(task_name)
        if handler:
            try:
                handler(design, *args)
                return {"success": True, "task": task_name}
            except Exception as e:
                import traceback
                return {
                    "success": False,
                    "task": task_name,
                    "error": traceback.format_exc()
                }
        else:
            return {"success": False, "error": f"Unknown task: {task_name}"}


# Global task dispatcher
dispatcher = TaskDispatcher()
