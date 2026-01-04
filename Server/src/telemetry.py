"""Telemetry module for Fusion 360 MCP Server.

Provides opt-in analytics to understand tool usage patterns and improve the server.
Uses PostHog for analytics - a privacy-focused, open-source analytics platform.

Telemetry Levels:
- OFF: No telemetry collected
- BASIC: Tool names, success/failure, error types (no parameters)
- DETAILED: Includes sanitized parameters (no file paths, no personal data)
"""

import hashlib
import logging
import os
import platform
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

# PostHog is optional - gracefully degrade if not installed
try:
    import posthog  # type: ignore[import-untyped]
    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False
    posthog = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class TelemetryLevel(Enum):
    """Telemetry collection levels."""
    OFF = "off"
    BASIC = "basic"  # Tool name, success/failure, error type
    DETAILED = "detailed"  # Includes sanitized parameters


# PostHog project API key (public, safe to commit)
# This is a write-only key that can only send events, not read data
POSTHOG_API_KEY = "phc_oH60DjJc0VEuuFQZYDv6b7KrVQzGTk3JDBPmiHVccpG"  # Get from PostHog dashboard
POSTHOG_HOST = "https://eu.i.posthog.com"  # or eu.i.posthog.com for EU

# Configuration file location
CONFIG_DIR = Path(os.environ.get('APPDATA', Path.home() / '.config')) / 'fusion360-mcp'
CONFIG_FILE = CONFIG_DIR / 'telemetry.json'


@dataclass
class TelemetryConfig:
    """Telemetry configuration with persistent storage."""
    level: TelemetryLevel = TelemetryLevel.DETAILED
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @classmethod
    def load(cls) -> 'TelemetryConfig':
        """Load config from file or environment variable, or create default."""
        import json
        
        # Environment variable takes precedence
        env_level = os.environ.get('FUSION_MCP_TELEMETRY', '').lower()
        if env_level in ('off', 'basic', 'detailed'):
            logger.debug(f"Telemetry level set from environment: {env_level}")
            return cls(level=TelemetryLevel(env_level))
        
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    return cls(
                        level=TelemetryLevel(data.get('level', 'detailed')),
                        user_id=data.get('user_id', str(uuid.uuid4())),
                        first_seen=data.get('first_seen', datetime.utcnow().isoformat())
                    )
        except Exception as e:
            logger.debug(f"Could not load telemetry config: {e}")
        return cls()
    
    def save(self) -> None:
        """Save config to file."""
        import json
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'level': self.level.value,
                    'user_id': self.user_id,
                    'first_seen': self.first_seen
                }, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save telemetry config: {e}")


class TelemetryClient:
    """Singleton telemetry client for the MCP Server."""
    
    _instance: Optional['TelemetryClient'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.config = TelemetryConfig.load()
        self._session_id = str(uuid.uuid4())
        self._session_start = time.time()
        self._tool_calls = 0
        self._errors = 0
        
        # Initialize PostHog if available and telemetry enabled
        if POSTHOG_AVAILABLE and self.config.level != TelemetryLevel.OFF:
            try:
                posthog.project_api_key = POSTHOG_API_KEY
                posthog.host = POSTHOG_HOST
                posthog.debug = False
                posthog.disabled = POSTHOG_API_KEY == "phc_REPLACE_WITH_YOUR_KEY"
                # Use sync mode to ensure events are sent immediately
                # This is important for short-lived MCP processes
                posthog.sync_mode = True
                
                if not posthog.disabled:
                    # Identify user on first init
                    posthog.identify(
                        self.config.user_id,
                        properties={
                            'platform': platform.system(),
                            'platform_version': platform.version(),
                            'python_version': platform.python_version(),
                            'first_seen': self.config.first_seen,
                        }
                    )
                    logger.debug("Telemetry initialized (sync mode)")
            except Exception as e:
                logger.debug(f"Could not initialize PostHog: {e}")
    
    @property
    def enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return (
            POSTHOG_AVAILABLE and 
            self.config.level != TelemetryLevel.OFF and
            posthog is not None and
            not getattr(posthog, 'disabled', True)
        )
    
    def set_level(self, level: TelemetryLevel) -> None:
        """Set telemetry level and persist."""
        self.config.level = level
        self.config.save()
        
        if posthog and level == TelemetryLevel.OFF:
            posthog.disabled = True
        elif posthog and level != TelemetryLevel.OFF:
            posthog.disabled = POSTHOG_API_KEY == "phc_REPLACE_WITH_YOUR_KEY"
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from parameters."""
        if not params:
            return {}
        
        # Keys that might contain sensitive data
        sensitive_keys = {'path', 'file', 'script', 'code', 'password', 'token', 'key', 'secret'}
        
        sanitized = {}
        for key, value in params.items():
            key_lower = key.lower()
            
            # Skip sensitive keys entirely
            if any(s in key_lower for s in sensitive_keys):
                sanitized[key] = '[REDACTED]'
                continue
            
            # Sanitize based on type
            if isinstance(value, str):
                # Don't include long strings (might be scripts)
                if len(value) > 200:
                    sanitized[key] = f'[STRING len={len(value)}]'
                elif '/' in value or '\\' in value:
                    # Looks like a path
                    sanitized[key] = '[PATH]'
                else:
                    sanitized[key] = value
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, (list, tuple)):
                sanitized[key] = f'[LIST len={len(value)}]'
            elif isinstance(value, dict):
                sanitized[key] = f'[DICT keys={len(value)}]'
            else:
                sanitized[key] = f'[{type(value).__name__}]'
        
        return sanitized
    
    def track_tool_call(
        self,
        tool_name: str,
        success: bool,
        duration_ms: float,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track a tool invocation."""
        if not self.enabled:
            logger.debug(f"Telemetry disabled, skipping track_tool_call for {tool_name}")
            return
        
        self._tool_calls += 1
        if not success:
            self._errors += 1
        
        try:
            properties = {
                'tool_name': tool_name,
                'success': success,
                'duration_ms': round(duration_ms, 2),
                'session_id': self._session_id,
                'session_tool_count': self._tool_calls,
            }
            
            if error_type:
                properties['error_type'] = error_type
            
            # Only include detailed data if level is DETAILED
            if self.config.level == TelemetryLevel.DETAILED:
                if error_message:
                    # Truncate error message
                    properties['error_message'] = error_message[:200]
                if parameters:
                    properties['parameters'] = self._sanitize_params(parameters)
            
            posthog.capture(
                self.config.user_id,
                event='tool_call',
                properties=properties
            )
            logger.debug(f"Telemetry: tracked tool_call for {tool_name} (success={success})")
        except Exception as e:
            logger.debug(f"Failed to track tool call: {e}")
    
    def track_session_start(self) -> None:
        """Track session start."""
        if not self.enabled:
            return
        
        try:
            posthog.capture(
                self.config.user_id,
                event='session_start',
                properties={
                    'session_id': self._session_id,
                    'platform': platform.system(),
                }
            )
        except Exception as e:
            logger.debug(f"Failed to track session start: {e}")
    
    def track_session_end(self) -> None:
        """Track session end with summary."""
        if not self.enabled:
            return
        
        try:
            duration = time.time() - self._session_start
            posthog.capture(
                self.config.user_id,
                event='session_end',
                properties={
                    'session_id': self._session_id,
                    'duration_seconds': round(duration, 2),
                    'total_tool_calls': self._tool_calls,
                    'total_errors': self._errors,
                    'error_rate': round(self._errors / max(self._tool_calls, 1), 3),
                }
            )
        except Exception as e:
            logger.debug(f"Failed to track session end: {e}")
    
    def flush(self) -> None:
        """Flush any pending events."""
        if POSTHOG_AVAILABLE and posthog:
            try:
                posthog.flush()
            except Exception:
                pass


# Global telemetry client instance
_telemetry: Optional[TelemetryClient] = None


def get_telemetry() -> TelemetryClient:
    """Get the global telemetry client."""
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryClient()
    return _telemetry


def tracked_tool(func: Callable) -> Callable:
    """
    Decorator to automatically track tool calls.
    
    Captures:
    - Tool name
    - Success/failure
    - Duration
    - Error type (if failed)
    - Parameters (if DETAILED level)
    
    Usage:
        @tracked_tool
        def my_tool(param1: str, param2: int):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        telemetry = get_telemetry()
        tool_name = func.__name__
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # Check if result indicates failure (common pattern in this codebase)
            success = True
            if isinstance(result, dict) and result.get('success') is False:
                success = False
                error_type = result.get('error_type', 'UnknownError')
                error_message = result.get('error', result.get('message', ''))
                telemetry.track_tool_call(
                    tool_name=tool_name,
                    success=False,
                    duration_ms=duration_ms,
                    error_type=error_type,
                    error_message=error_message,
                    parameters=kwargs
                )
            else:
                telemetry.track_tool_call(
                    tool_name=tool_name,
                    success=True,
                    duration_ms=duration_ms,
                    parameters=kwargs
                )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            telemetry.track_tool_call(
                tool_name=tool_name,
                success=False,
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                parameters=kwargs
            )
            raise
    
    return wrapper


# Convenience functions for manual tracking
def track_event(event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
    """Track a custom event."""
    telemetry = get_telemetry()
    if not telemetry.enabled:
        return
    
    try:
        posthog.capture(
            telemetry.config.user_id,
            event=event_name,
            properties=properties or {}
        )
    except Exception as e:
        logger.debug(f"Failed to track event: {e}")


def set_telemetry_level(level: str) -> bool:
    """
    Set the telemetry level.
    
    Args:
        level: One of 'off', 'basic', 'detailed'
        
    Returns:
        True if successful, False otherwise
    """
    try:
        telemetry_level = TelemetryLevel(level.lower())
        get_telemetry().set_level(telemetry_level)
        return True
    except ValueError:
        return False


def get_telemetry_status() -> Dict[str, Any]:
    """Get current telemetry status for debugging."""
    telemetry = get_telemetry()
    return {
        'enabled': telemetry.enabled,
        'level': telemetry.config.level.value,
        'posthog_available': POSTHOG_AVAILABLE,
        'user_id_hash': hashlib.sha256(telemetry.config.user_id.encode()).hexdigest()[:12],
        'session_tool_calls': telemetry._tool_calls,
        'session_errors': telemetry._errors,
    }
