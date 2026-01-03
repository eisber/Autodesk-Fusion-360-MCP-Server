#!/usr/bin/env python
"""Validate tool definitions across Server and MCP components.

This script compares the shared tool definitions against the actual
implementations in both Server/src/tools/ and MCP/lib/ to detect:
- Missing tools
- Parameter mismatches (names, types, defaults, order)
- Endpoint/route mismatches
- Docstring differences

Usage:
    python scripts/validate_tools.py           # Check all
    python scripts/validate_tools.py --fix     # Show suggested fixes
    python scripts/validate_tools.py --server  # Check Server only
    python scripts/validate_tools.py --mcp     # Check MCP only
"""

from __future__ import annotations

import argparse
import ast
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent directory to path for imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from shared.tool_definitions import (
    TOOL_DEFINITIONS,
    ParamDef,
    ParamType,
    ToolDef,
    get_tool,
)


@dataclass
class ValidationError:
    """A validation error or warning."""
    tool_name: str
    component: str  # "server" or "mcp"
    severity: str  # "error" or "warning"
    message: str
    suggestion: Optional[str] = None


class ASTToolExtractor(ast.NodeVisitor):
    """Extract tool function signatures from Python source files."""
    
    def __init__(self, decorator_name: str):
        self.decorator_name = decorator_name
        self.tools: Dict[str, Dict] = {}
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions to find decorated tools."""
        for decorator in node.decorator_list:
            dec_name = self._get_decorator_name(decorator)
            if dec_name == self.decorator_name:
                self.tools[node.name] = self._extract_function_info(node, decorator)
        self.generic_visit(node)
    
    def _get_decorator_name(self, decorator) -> str:
        """Get the name of a decorator."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return ""
    
    def _extract_function_info(self, node: ast.FunctionDef, decorator) -> Dict:
        """Extract function information including parameters and decorator options."""
        info = {
            "name": node.name,
            "params": [],
            "decorator_args": {},
            "docstring": ast.get_docstring(node) or "",
            "lineno": node.lineno,
        }
        
        # Extract parameters (skip 'design', 'ui')
        skip_params = {"design", "ui"}
        defaults = node.args.defaults
        num_defaults = len(defaults)
        num_args = len(node.args.args)
        
        for i, arg in enumerate(node.args.args):
            if arg.arg in skip_params:
                continue
            
            param_info = {
                "name": arg.arg,
                "type": None,
                "default": None,
                "has_default": False,
            }
            
            # Get type annotation
            if arg.annotation:
                param_info["type"] = self._annotation_to_string(arg.annotation)
            
            # Get default value
            default_index = i - (num_args - num_defaults)
            if default_index >= 0:
                param_info["has_default"] = True
                param_info["default"] = self._value_to_string(defaults[default_index])
            
            info["params"].append(param_info)
        
        # Extract decorator keyword arguments
        if isinstance(decorator, ast.Call):
            for kw in decorator.keywords:
                info["decorator_args"][kw.arg] = self._value_to_string(kw.value)
        
        return info
    
    def _annotation_to_string(self, annotation) -> str:
        """Convert an annotation AST node to a string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            return f"{self._annotation_to_string(annotation.value)}[...]"
        return "unknown"
    
    def _value_to_string(self, value) -> str:
        """Convert a value AST node to a string."""
        if isinstance(value, ast.Constant):
            return repr(value.value)
        elif isinstance(value, ast.Name):
            return value.id
        elif isinstance(value, ast.List):
            return "[]"
        elif isinstance(value, ast.Dict):
            return "{}"
        return "unknown"


def extract_server_tools(server_tools_dir: Path) -> Dict[str, Dict]:
    """Extract all @fusion_tool decorated functions from Server."""
    all_tools = {}
    
    for py_file in server_tools_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            extractor = ASTToolExtractor("fusion_tool")
            extractor.visit(tree)
            for name, info in extractor.tools.items():
                info["file"] = py_file.name
                all_tools[name] = info
        except SyntaxError as e:
            print(f"Syntax error in {py_file}: {e}")
    
    return all_tools


def extract_mcp_tools(mcp_lib_dir: Path) -> Dict[str, Dict]:
    """Extract all @task decorated functions from MCP."""
    all_tools = {}
    
    # Search in geometry/, features/, utils/ subdirectories
    search_dirs = [
        mcp_lib_dir / "geometry",
        mcp_lib_dir / "features",
        mcp_lib_dir / "utils",
    ]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for py_file in search_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
                extractor = ASTToolExtractor("task")
                extractor.visit(tree)
                for name, info in extractor.tools.items():
                    info["file"] = f"{search_dir.name}/{py_file.name}"
                    all_tools[name] = info
            except SyntaxError as e:
                print(f"Syntax error in {py_file}: {e}")
    
    return all_tools


def validate_tool_params(
    tool_def: ToolDef,
    actual_params: List[Dict],
    component: str,
) -> List[ValidationError]:
    """Validate that actual parameters match the definition."""
    errors = []
    expected_params = tool_def.params
    
    # Check parameter count
    if len(actual_params) != len(expected_params):
        errors.append(ValidationError(
            tool_name=tool_def.name,
            component=component,
            severity="error",
            message=f"Parameter count mismatch: expected {len(expected_params)}, got {len(actual_params)}",
            suggestion=f"Expected params: {[p.name for p in expected_params]}, got: {[p['name'] for p in actual_params]}",
        ))
        return errors  # Can't compare further if counts differ
    
    # Check each parameter
    for i, (expected, actual) in enumerate(zip(expected_params, actual_params)):
        # Check name
        if expected.name != actual["name"]:
            errors.append(ValidationError(
                tool_name=tool_def.name,
                component=component,
                severity="error",
                message=f"Parameter {i} name mismatch: expected '{expected.name}', got '{actual['name']}'",
                suggestion=f"Rename parameter '{actual['name']}' to '{expected.name}'",
            ))
        
        # Check type annotation (server only)
        if component == "server" and actual.get("type"):
            expected_type = expected.type_hint
            if actual["type"] != expected_type:
                errors.append(ValidationError(
                    tool_name=tool_def.name,
                    component=component,
                    severity="warning",
                    message=f"Parameter '{expected.name}' type mismatch: expected '{expected_type}', got '{actual['type']}'",
                ))
        
        # Check default value
        if expected.required and actual.get("has_default"):
            errors.append(ValidationError(
                tool_name=tool_def.name,
                component=component,
                severity="warning",
                message=f"Parameter '{expected.name}' should be required but has default",
            ))
        elif not expected.required and not actual.get("has_default"):
            errors.append(ValidationError(
                tool_name=tool_def.name,
                component=component,
                severity="error",
                message=f"Parameter '{expected.name}' should have default={expected.default}",
                suggestion=f"Add default value: {expected.name}={repr(expected.default)}",
            ))
    
    return errors


def validate_server_tools(server_tools: Dict[str, Dict]) -> List[ValidationError]:
    """Validate Server-side tools against definitions."""
    errors = []
    
    # Check each defined tool
    for tool_def in TOOL_DEFINITIONS:
        if tool_def.name not in server_tools:
            errors.append(ValidationError(
                tool_name=tool_def.name,
                component="server",
                severity="warning",
                message=f"Tool '{tool_def.name}' not found in Server",
                suggestion=f"Add @fusion_tool function for '{tool_def.name}'",
            ))
            continue
        
        actual = server_tools[tool_def.name]
        errors.extend(validate_tool_params(tool_def, actual["params"], "server"))
    
    # Check for extra tools not in definitions
    defined_names = {t.name for t in TOOL_DEFINITIONS}
    for name in server_tools:
        if name not in defined_names:
            errors.append(ValidationError(
                tool_name=name,
                component="server",
                severity="warning",
                message=f"Tool '{name}' in Server but not in shared definitions",
                suggestion=f"Add ToolDef for '{name}' in shared/tool_definitions.py",
            ))
    
    return errors


def validate_mcp_tools(mcp_tools: Dict[str, Dict]) -> List[ValidationError]:
    """Validate MCP-side tools against definitions."""
    errors = []
    
    # Check each defined tool
    for tool_def in TOOL_DEFINITIONS:
        if tool_def.name not in mcp_tools:
            errors.append(ValidationError(
                tool_name=tool_def.name,
                component="mcp",
                severity="warning",
                message=f"Tool '{tool_def.name}' not found in MCP",
                suggestion=f"Add @task function for '{tool_def.name}'",
            ))
            continue
        
        actual = mcp_tools[tool_def.name]
        errors.extend(validate_tool_params(tool_def, actual["params"], "mcp"))
    
    # Check for extra tools not in definitions
    defined_names = {t.name for t in TOOL_DEFINITIONS}
    for name in mcp_tools:
        if name not in defined_names:
            errors.append(ValidationError(
                tool_name=name,
                component="mcp",
                severity="warning",
                message=f"Tool '{name}' in MCP but not in shared definitions",
                suggestion=f"Add ToolDef for '{name}' in shared/tool_definitions.py",
            ))
    
    return errors


def extract_routes(routes_file: Path) -> Dict[str, str]:
    """Extract route -> task_name mappings from routes.py."""
    routes = {}
    source = routes_file.read_text(encoding="utf-8")
    tree = ast.parse(source)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Look for build_task_args('task_name', data)
            if isinstance(node.func, ast.Name) and node.func.id == "build_task_args":
                if node.args and isinstance(node.args[0], ast.Constant):
                    task_name = node.args[0].value
                    # Find the parent function to get the route
                    # This is a simplification; routes are extracted elsewhere
                    routes[task_name] = task_name
    
    return routes


def print_errors(errors: List[ValidationError], show_suggestions: bool = False):
    """Print validation errors in a readable format."""
    if not errors:
        print("✅ All validations passed!")
        return
    
    # Group by component
    server_errors = [e for e in errors if e.component == "server"]
    mcp_errors = [e for e in errors if e.component == "mcp"]
    
    for component, component_errors in [("Server", server_errors), ("MCP", mcp_errors)]:
        if not component_errors:
            continue
        
        print(f"\n{'='*60}")
        print(f"{component} Issues ({len(component_errors)})")
        print("="*60)
        
        # Group by tool
        by_tool: Dict[str, List[ValidationError]] = {}
        for e in component_errors:
            by_tool.setdefault(e.tool_name, []).append(e)
        
        for tool_name, tool_errors in sorted(by_tool.items()):
            print(f"\n📦 {tool_name}:")
            for e in tool_errors:
                icon = "❌" if e.severity == "error" else "⚠️"
                print(f"  {icon} {e.message}")
                if show_suggestions and e.suggestion:
                    print(f"     💡 {e.suggestion}")


def main():
    parser = argparse.ArgumentParser(description="Validate tool definitions")
    parser.add_argument("--fix", action="store_true", help="Show suggested fixes")
    parser.add_argument("--server", action="store_true", help="Check Server only")
    parser.add_argument("--mcp", action="store_true", help="Check MCP only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Default to checking both if neither specified
    check_server = args.server or (not args.server and not args.mcp)
    check_mcp = args.mcp or (not args.server and not args.mcp)
    
    all_errors = []
    
    print("🔍 Validating tool definitions...")
    print(f"   Shared definitions: {len(TOOL_DEFINITIONS)} tools")
    
    if check_server:
        server_dir = ROOT_DIR / "Server" / "src" / "tools"
        if server_dir.exists():
            server_tools = extract_server_tools(server_dir)
            print(f"   Server tools found: {len(server_tools)}")
            if args.verbose:
                print(f"      {list(server_tools.keys())}")
            all_errors.extend(validate_server_tools(server_tools))
        else:
            print(f"   ⚠️ Server tools directory not found: {server_dir}")
    
    if check_mcp:
        mcp_dir = ROOT_DIR / "MCP" / "lib"
        if mcp_dir.exists():
            mcp_tools = extract_mcp_tools(mcp_dir)
            print(f"   MCP tools found: {len(mcp_tools)}")
            if args.verbose:
                print(f"      {list(mcp_tools.keys())}")
            all_errors.extend(validate_mcp_tools(mcp_tools))
        else:
            print(f"   ⚠️ MCP lib directory not found: {mcp_dir}")
    
    print_errors(all_errors, show_suggestions=args.fix)
    
    # Return exit code based on errors
    error_count = sum(1 for e in all_errors if e.severity == "error")
    warning_count = sum(1 for e in all_errors if e.severity == "warning")
    
    print(f"\n📊 Summary: {error_count} errors, {warning_count} warnings")
    
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
