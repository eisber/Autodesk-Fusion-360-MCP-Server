"""Server-Sent Events (SSE) support for Fusion 360 MCP Add-In.

This module provides SSE streaming for real-time task progress updates,
eliminating polling and timeout issues for long-running operations.
"""

import json
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(Enum):
    """Status of a task in the execution pipeline."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Information about a tracked task."""
    task_id: str
    task_name: str
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = 0.0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    cancelled: bool = False


class TaskManager:
    """Manages task lifecycle with SSE event streaming.
    
    Provides:
    - Task ID tracking for cancellation support
    - Progress updates via SSE
    - Thread-safe event queue for streaming
    """
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_lock = threading.Lock()
        # Event queue for SSE streaming (multiple subscribers possible)
        self.event_queues: Dict[str, queue.Queue] = {}
        self.queue_lock = threading.Lock()
        # Active task being executed (only one at a time in Fusion)
        self.current_task_id: Optional[str] = None
    
    def reset(self):
        """Reset all state. Useful for testing."""
        with self.task_lock:
            self.tasks.clear()
            self.current_task_id = None
        with self.queue_lock:
            self.event_queues.clear()
    
    def create_task(self, task_name: str) -> str:
        """Create a new tracked task and return its ID."""
        task_id = str(uuid.uuid4())[:8]  # Short ID for readability
        return self.register_task(task_id, task_name)
    
    def register_task(self, task_id: str, task_name: str = "execute_script") -> str:
        """Register a task with a specific ID."""
        with self.task_lock:
            self.tasks[task_id] = TaskInfo(
                task_id=task_id,
                task_name=task_name
            )
        
        self._broadcast_event("task_created", {
            "task_id": task_id,
            "task_name": task_name,
            "status": TaskStatus.QUEUED.value
        })
        
        return task_id
    
    def start_task(self, task_id: str):
        """Mark a task as started."""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                self.current_task_id = task_id
        
        self._broadcast_event("task_started", {
            "task_id": task_id,
            "status": TaskStatus.RUNNING.value
        })
    
    def report_progress(self, task_id: str, progress: float, message: str = ""):
        """Report progress for a running task (0.0 to 100.0)."""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.progress = progress
                task.message = message
        
        self._broadcast_event("task_progress", {
            "task_id": task_id,
            "progress": progress,
            "message": message
        })
    
    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """Mark a task as completed with result."""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.progress = 100.0
                task.result = result
                task.completed_at = time.time()
                if self.current_task_id == task_id:
                    self.current_task_id = None
        
        self._broadcast_event("task_completed", {
            "task_id": task_id,
            "status": TaskStatus.COMPLETED.value,
            "result": result
        })
    
    def fail_task(self, task_id: str, error: str):
        """Mark a task as failed with error message."""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error = error
                task.completed_at = time.time()
                if self.current_task_id == task_id:
                    self.current_task_id = None
        
        self._broadcast_event("task_failed", {
            "task_id": task_id,
            "status": TaskStatus.FAILED.value,
            "error": error
        })
    
    def cancel_task(self, task_id: str) -> bool:
        """Request cancellation of a task. Returns True if task was found."""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in (TaskStatus.QUEUED, TaskStatus.RUNNING):
                    task.cancelled = True
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = time.time()
                    
                    self._broadcast_event("task_cancelled", {
                        "task_id": task_id,
                        "status": TaskStatus.CANCELLED.value
                    })
                    return True
        return False
    
    def is_cancelled(self, task_id: str) -> bool:
        """Check if a task has been cancelled."""
        with self.task_lock:
            if task_id in self.tasks:
                return self.tasks[task_id].cancelled
        return False
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task info by ID."""
        with self.task_lock:
            return self.tasks.get(task_id)
    
    def cleanup_old_tasks(self, max_age_seconds: float = 300):
        """Remove tasks older than max_age_seconds."""
        cutoff = time.time() - max_age_seconds
        with self.task_lock:
            to_remove = [
                tid for tid, task in self.tasks.items()
                if task.completed_at and task.completed_at < cutoff
            ]
            for tid in to_remove:
                del self.tasks[tid]
    
    def subscribe(self) -> str:
        """Subscribe to SSE events. Returns subscriber ID."""
        subscriber_id = str(uuid.uuid4())[:8]
        with self.queue_lock:
            self.event_queues[subscriber_id] = queue.Queue()
        return subscriber_id
    
    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from SSE events."""
        with self.queue_lock:
            if subscriber_id in self.event_queues:
                del self.event_queues[subscriber_id]
    
    def get_event_queue(self, subscriber_id: str) -> Optional[queue.Queue]:
        """Get the event queue for a subscriber."""
        with self.queue_lock:
            return self.event_queues.get(subscriber_id)
    
    def _broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all subscribers."""
        event = {"event": event_type, "data": data}
        with self.queue_lock:
            for q in self.event_queues.values():
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass  # Drop events if queue is full


def format_sse(event_type: str, data: Dict[str, Any]) -> bytes:
    """Format data as SSE message."""
    lines = []
    lines.append(f"event: {event_type}")
    lines.append(f"data: {json.dumps(data)}")
    lines.append("")  # Empty line to end message
    return ("\n".join(lines) + "\n").encode('utf-8')


# Global task manager instance
task_manager = TaskManager()


def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    return task_manager


class ProgressReporter:
    """Context manager for reporting progress from within a task.
    
    Usage:
        with ProgressReporter(task_id) as progress:
            progress(10, "Starting...")
            # do work
            progress(50, "Halfway done")
            # more work
            progress(100, "Complete")
    """
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self._manager = get_task_manager()
    
    def __call__(self, percent: float, message: str = ""):
        """Report progress (0-100)."""
        if not self._manager.is_cancelled(self.task_id):
            self._manager.report_progress(self.task_id, percent, message)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def is_cancelled(self) -> bool:
        """Check if this task was cancelled."""
        return self._manager.is_cancelled(self.task_id)
