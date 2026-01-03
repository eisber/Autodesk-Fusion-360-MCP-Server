"""Inspection tools for Fusion 360 MCP Server.

Contains functions for introspecting the adsk module to discover
API classes, methods, properties, and their signatures/docstrings.
"""

import json
import logging
import traceback

from .scripting import execute_fusion_script


def inspect_adsk_api(path: str = "adsk.fusion") -> dict:
    """
    Inspect the Autodesk Fusion 360 API to discover classes, methods, properties,
    and their signatures/docstrings. Use this to learn about the API before
    writing scripts for execute_fusion_script.

    Args:
        path: Dot-separated path to inspect. Examples:
            - "adsk" - Top-level module (lists submodules: core, fusion, cam)
            - "adsk.fusion" - Fusion module (lists all classes)
            - "adsk.fusion.Sketch" - Specific class (shows methods, properties, docstrings)
            - "adsk.fusion.Sketch.sketchCurves" - Specific property
            - "adsk.core.Point3D.create" - Specific method (shows signature)

    Returns:
        Dictionary with:
        - path: The inspected path
        - type: "module", "class", "method", "property", etc.
        - docstring: Documentation string if available
        - signature: Method signature if applicable
        - members: List of child members with their types (for modules/classes)
        - example: Usage example if available

    Examples:
        # List all classes in adsk.fusion
        inspect_adsk_api("adsk.fusion")

        # Get details about the Sketch class
        inspect_adsk_api("adsk.fusion.Sketch")

        # Get signature for Point3D.create
        inspect_adsk_api("adsk.core.Point3D.create")
    """
    # The inspection script to run in Fusion 360
    inspection_script = '''
import inspect
import json

def get_type_name(obj):
    """Get a readable type name for an object."""
    t = type(obj).__name__
    if t == 'type':
        return 'class'
    elif t == 'module':
        return 'module'
    elif t == 'builtin_function_or_method':
        return 'method'
    elif t == 'property':
        return 'property'
    elif t == 'getset_descriptor':
        return 'property'
    elif t == 'method_descriptor':
        return 'method'
    elif callable(obj):
        return 'callable'
    else:
        return t

def get_signature_str(obj):
    """Try to get a signature string for a callable."""
    try:
        sig = inspect.signature(obj)
        return str(sig)
    except (ValueError, TypeError):
        # Many built-in methods don't have inspectable signatures
        # Try to extract from docstring
        doc = getattr(obj, '__doc__', '') or ''
        lines = doc.strip().split('\\n')
        if lines and '(' in lines[0] and ')' in lines[0]:
            return lines[0]
        return None

def get_member_info(name, obj, include_details=False):
    """Get info about a single member."""
    type_name = get_type_name(obj)
    info = {'name': name, 'type': type_name}
    
    if include_details:
        doc = getattr(obj, '__doc__', None)
        if doc:
            info['docstring'] = doc.strip()
        
        if type_name in ('method', 'callable', 'builtin_function_or_method'):
            sig = get_signature_str(obj)
            if sig:
                info['signature'] = sig
    
    return info

def inspect_path(path):
    """Inspect an adsk module path and return detailed info."""
    parts = path.split('.')
    
    # Navigate to the target object
    if parts[0] != 'adsk':
        return {'error': f'Path must start with "adsk", got: {path}'}
    
    obj = adsk
    traversed = ['adsk']
    
    for part in parts[1:]:
        try:
            obj = getattr(obj, part)
            traversed.append(part)
        except AttributeError:
            return {
                'error': f'"{part}" not found in {".".join(traversed)}',
                'path': path,
                'available': [m for m in dir(obj) if not m.startswith('_')][:50]
            }
    
    result = {
        'path': path,
        'type': get_type_name(obj),
    }
    
    # Get docstring
    doc = getattr(obj, '__doc__', None)
    if doc:
        result['docstring'] = doc.strip()
    
    # Get signature for callables
    if result['type'] in ('method', 'callable', 'builtin_function_or_method', 'class'):
        sig = get_signature_str(obj)
        if sig:
            result['signature'] = f'{parts[-1]}{sig}' if not sig.startswith(parts[-1]) else sig
    
    # Get members for modules and classes
    if result['type'] in ('module', 'class', 'type'):
        members = []
        for name in dir(obj):
            if name.startswith('_'):
                continue
            try:
                member_obj = getattr(obj, name)
                member_info = get_member_info(name, member_obj, include_details=True)
                members.append(member_info)
            except Exception:
                members.append({'name': name, 'type': 'unknown'})
        
        result['members'] = members
        result['member_count'] = len(members)
    
    # For properties, try to get the type hint from docstring
    if result['type'] == 'property':
        doc = result.get('docstring', '')
        if 'Returns' in doc or 'returns' in doc:
            result['returns'] = doc
    
    return result

# Execute inspection
target_path = PATH_PLACEHOLDER
result = inspect_path(target_path)
'''.replace('PATH_PLACEHOLDER', repr(path))

    try:
        response = execute_fusion_script(inspection_script)
        
        if not response.get('success'):
            return {
                'success': False,
                'error': response.get('error', 'Unknown error'),
                'traceback': response.get('traceback'),
            }
        
        # The result is returned via the 'result' variable
        return_value = response.get('return_value')
        if return_value:
            if isinstance(return_value, str):
                try:
                    return_value = json.loads(return_value)
                except json.JSONDecodeError:
                    pass
            return {'success': True, **return_value}
        
        return {'success': True, 'data': response}
        
    except Exception as e:
        logging.error("inspect_adsk_api failed: %s", e)
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }


def get_adsk_class_info(class_path: str) -> dict:
    """
    Get detailed documentation for a specific adsk class in docstring format,
    suitable for understanding how to use the class in scripts.

    Args:
        class_path: Full path to the class, e.g., "adsk.fusion.Sketch",
            "adsk.core.Point3D", "adsk.fusion.ExtrudeFeatures"

    Returns:
        Dictionary containing:
        - class_name: Name of the class
        - docstring: Formatted docstring with class overview, methods, and properties
        - methods: List of methods with signatures and docstrings
        - properties: List of properties with types and docstrings
        - example: Usage example if extractable

    Example output docstring format:
        '''
        class Sketch:
            \"\"\"
            Represents a sketch in Fusion 360.
            
            Properties:
                sketchCurves: SketchCurves - Collection of curves in the sketch.
                profiles: Profiles - Collection of closed profiles.
                ...
            
            Methods:
                add(plane) -> Sketch
                    Creates a new sketch on the specified plane.
                ...
            \"\"\"
        '''
    """
    inspection_script = '''
import inspect

def format_docstring_style(path):
    """Format class info as a docstring for code generation context."""
    parts = path.split('.')
    
    if parts[0] != 'adsk':
        return {'error': f'Path must start with "adsk", got: {path}'}
    
    obj = adsk
    for part in parts[1:]:
        try:
            obj = getattr(obj, part)
        except AttributeError:
            return {'error': f'Path not found: {path}'}
    
    class_name = parts[-1]
    
    # Collect properties and methods
    properties = []
    methods = []
    
    for name in sorted(dir(obj)):
        if name.startswith('_'):
            continue
        try:
            member = getattr(obj, name)
            member_type = type(member).__name__
            doc = (getattr(member, '__doc__', '') or '').strip()
            
            # Extract first line of doc as summary
            summary = doc.split('\\n')[0] if doc else ''
            
            if member_type in ('property', 'getset_descriptor'):
                # Try to extract return type from docstring
                return_type = ''
                if doc:
                    for line in doc.split('\\n'):
                        if 'Returns' in line or ':' in line:
                            return_type = line.strip()
                            break
                properties.append({
                    'name': name,
                    'summary': summary,
                    'return_type': return_type,
                    'docstring': doc
                })
            elif member_type in ('method_descriptor', 'builtin_function_or_method') or callable(member):
                # Try to get signature
                sig = ''
                try:
                    sig = str(inspect.signature(member))
                except (ValueError, TypeError):
                    # Extract from docstring if possible
                    if doc and '(' in doc.split('\\n')[0]:
                        sig = doc.split('\\n')[0]
                
                methods.append({
                    'name': name,
                    'signature': sig,
                    'summary': summary,
                    'docstring': doc
                })
        except Exception as e:
            continue
    
    # Build formatted docstring
    lines = []
    lines.append(f'class {class_name}:')
    
    # Class docstring
    class_doc = (getattr(obj, '__doc__', '') or '').strip()
    if class_doc:
        lines.append(f'    """')
        for line in class_doc.split('\\n')[:10]:  # First 10 lines
            lines.append(f'    {line}')
        if len(class_doc.split('\\n')) > 10:
            lines.append('    ...')
        lines.append(f'    """')
    
    # Properties section
    if properties:
        lines.append('')
        lines.append('    # Properties')
        for prop in properties[:30]:  # Limit to 30 properties
            if prop['summary']:
                lines.append(f'    # {prop["name"]}: {prop["summary"][:80]}')
            else:
                lines.append(f'    # {prop["name"]}')
    
    # Methods section  
    if methods:
        lines.append('')
        lines.append('    # Methods')
        for method in methods[:30]:  # Limit to 30 methods
            if method['signature']:
                lines.append(f'    # def {method["name"]}{method["signature"]}')
            else:
                lines.append(f'    # def {method["name"]}(...)')
            if method['summary']:
                lines.append(f'    #     {method["summary"][:80]}')
    
    docstring_output = '\\n'.join(lines)
    
    return {
        'class_name': class_name,
        'path': path,
        'docstring': docstring_output,
        'properties': properties,
        'methods': methods,
        'property_count': len(properties),
        'method_count': len(methods)
    }

result = format_docstring_style(CLASS_PATH_PLACEHOLDER)
'''.replace('CLASS_PATH_PLACEHOLDER', repr(class_path))

    try:
        response = execute_fusion_script(inspection_script)
        
        if not response.get('success'):
            return {
                'success': False,
                'error': response.get('error', 'Unknown error'),
                'traceback': response.get('traceback'),
            }
        
        return_value = response.get('return_value')
        if return_value:
            if isinstance(return_value, str):
                try:
                    return_value = json.loads(return_value)
                except json.JSONDecodeError:
                    pass
            return {'success': True, **return_value}
        
        return {'success': True, 'data': response}
        
    except Exception as e:
        logging.error("get_adsk_class_info failed: %s", e)
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }
