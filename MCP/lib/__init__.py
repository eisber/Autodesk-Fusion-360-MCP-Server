"""Fusion 360 MCP Library.

This package contains all the modular functionality for the MCP add-in.
Importing sub-packages triggers @task decorator registration.

Note: geometry and features modules are now empty stubs.
Use execute_fusion_script for all geometry/feature creation.
"""

from . import utils

__all__ = ["utils"]
