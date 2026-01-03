"""Task Registry for Fusion 360 MCP Add-In.

Provides a decorator-based registration system for task handlers.
Task name = function name. Parameter metadata auto-detected.

Usage:
    from lib.registry import task
    
    @task
    def measure_distance(design, entity1_type, entity1_index, ...):
        ...
"""

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

# Global registry: task_name -> TaskInfo
_TASK_REGISTRY: Dict[str, 'TaskInfo'] = {}


@dataclass
class ParamInfo:
    """Metadata about a function parameter."""
    name: str
    default: Any  # inspect.Parameter.empty if no default
    has_default: bool


@dataclass  
class TaskInfo:
    """Metadata about a registered task."""
    func: Callable
    param_count: int
    params: List[ParamInfo]  # Parameters (excluding design, ui)
    needs_ui: bool


def task(func):
    """Decorator to register a function as a task handler.
    
    Task name is taken from function name.
    Parameter metadata auto-detected (excluding 'design' and 'ui').
    """
    sig = inspect.signature(func)
    skip = {'design', 'ui'}
    
    params = []
    for name, param in sig.parameters.items():
        if name in skip:
            continue
        has_default = param.default is not inspect.Parameter.empty
        params.append(ParamInfo(
            name=name,
            default=param.default if has_default else None,
            has_default=has_default
        ))
    
    info = TaskInfo(
        func=func,
        param_count=len(params),
        params=params,
        needs_ui='ui' in sig.parameters
    )
    
    _TASK_REGISTRY[func.__name__] = info
    return func


def get_registry() -> Dict[str, TaskInfo]:
    """Get the task registry dict."""
    return _TASK_REGISTRY


def list_tasks() -> List[str]:
    """List all registered task names."""
    return sorted(_TASK_REGISTRY.keys())


def get_task_params(task_name: str) -> Optional[List[ParamInfo]]:
    """Get parameter info for a task."""
    info = _TASK_REGISTRY.get(task_name)
    return info.params if info else None


def build_task_args(task_name: str, data: dict) -> Tuple:
    """Build task args tuple from request data.
    
    Args:
        task_name: Name of the task
        data: Request data dict (e.g. {"command": "measure_distance", "body_index": 0})
    
    Returns:
        Tuple of (task_name, arg1, arg2, ...) ready for task_queue
    """
    info = _TASK_REGISTRY.get(task_name)
    if not info:
        raise ValueError(f"Unknown task: {task_name}")
    
    args = [task_name]
    for param in info.params:
        if param.has_default:
            args.append(data.get(param.name, param.default))
        else:
            # Required param - use data.get which returns None if missing
            args.append(data.get(param.name))
    
    return tuple(args)


def dispatch(task_name: str, design, ui, args: list):
    """Dispatch a task by name.
    
    Args:
        task_name: Name of the task (= function name)
        design: Active Fusion design
        ui: Fusion UI object
        args: List of arguments for the task
    
    Returns:
        Result from the handler function
    """
    if task_name not in _TASK_REGISTRY:
        raise ValueError(f"Unknown task: {task_name}")
    
    info = _TASK_REGISTRY[task_name]
    
    # Build argument list
    if info.needs_ui:
        return info.func(design, ui, *args[:info.param_count])
    else:
        return info.func(design, *args[:info.param_count])
