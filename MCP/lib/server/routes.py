"""HTTP route handlers for Fusion 360 MCP Add-In.

Registers all GET and POST routes using the route registry.
"""

from .http_server import routes
from .task_dispatcher import dispatcher

# Import geometry functions
from ..geometry import (
    draw_box, draw_cylinder, create_sphere,
    draw_circle, draw_ellipse, draw_2d_rectangle, draw_lines, 
    draw_one_line, draw_arc, draw_spline, draw_text,
)
from ..features import (
    extrude_last_sketch, extrude_thin, cut_extrude,
    loft, sweep, revolve_profile, boolean_operation,
    shell_existing_body, fillet_edges, holes, create_thread,
    circular_pattern, rectangular_pattern, move_last_body, offsetplane,
)
from ..utils import (
    get_model_parameters, get_current_model_state, get_faces_info,
    set_parameter, undo, delete_all, export_as_step, export_as_stl,
    select_body, select_sketch,
)


# =============================================================================
# Task Handlers - Register tasks for the dispatcher
# =============================================================================

@dispatcher.register('set_parameter')
def _set_parameter(design, name, value):
    set_parameter(design, name, value)

@dispatcher.register('undo')
def _undo(design):
    undo(design)

@dispatcher.register('draw_box')
def _draw_box(design, height, width, depth, x, y, z, plane):
    draw_box(design, None, height, width, depth, x, y, z, plane)

@dispatcher.register('draw_cylinder')
def _draw_cylinder(design, radius, height, x, y, z, plane):
    draw_cylinder(design, None, radius, height, x, y, z, plane)

@dispatcher.register('draw_sphere')
def _draw_sphere(design, radius, x, y, z):
    create_sphere(design, None, radius, x, y, z)

@dispatcher.register('circle')
def _circle(design, radius, x, y, z, plane):
    draw_circle(design, None, radius, x, y, z, plane)

@dispatcher.register('draw_lines')
def _draw_lines(design, points, plane):
    draw_lines(design, None, points, plane)

@dispatcher.register('draw_one_line')
def _draw_one_line(design, x1, y1, z1, x2, y2, z2, plane):
    draw_one_line(design, None, x1, y1, z1, x2, y2, z2, plane)

@dispatcher.register('arc')
def _arc(design, point1, point2, point3, connect, plane):
    draw_arc(design, None, point1, point2, point3, plane, connect)

@dispatcher.register('spline')
def _spline(design, points, plane):
    draw_spline(design, None, points, plane)

@dispatcher.register('ellipsis')
def _ellipsis(design, x_center, y_center, z_center, x_major, y_major, z_major, x_through, y_through, z_through, plane):
    draw_ellipse(design, None, x_center, y_center, z_center, x_major, y_major, z_major, x_through, y_through, z_through, plane)

@dispatcher.register('draw_2d_rectangle')
def _draw_2d_rectangle(design, x1, y1, z1, x2, y2, z2, plane):
    draw_2d_rectangle(design, None, x1, y1, z1, x2, y2, z2, plane)

@dispatcher.register('draw_text')
def _draw_text(design, text, thickness, x1, y1, z1, x2, y2, z2, extrusion_value, plane):
    draw_text(design, None, text, thickness, x1, y1, z1, x2, y2, z2, extrusion_value, plane)

@dispatcher.register('extrude_last_sketch')
def _extrude_last_sketch(design, value, taperangle):
    extrude_last_sketch(design, None, value, taperangle)

@dispatcher.register('extrude_thin')
def _extrude_thin(design, thickness, distance):
    extrude_thin(design, None, thickness, distance)

@dispatcher.register('cut_extrude')
def _cut_extrude(design, depth):
    cut_extrude(design, None, depth)

@dispatcher.register('loft')
def _loft(design, sketchcount):
    loft(design, None, sketchcount)

@dispatcher.register('sweep')
def _sweep(design):
    sweep(design, None)

@dispatcher.register('revolve_profile')
def _revolve_profile(design, angle):
    revolve_profile(design, None, angle)

@dispatcher.register('boolean_operation')
def _boolean_operation(design, operation):
    boolean_operation(design, None, operation)

@dispatcher.register('shell_body')
def _shell_body(design, thickness, faceindex):
    shell_existing_body(design, None, thickness, faceindex)

@dispatcher.register('fillet_edges')
def _fillet_edges(design, radius):
    fillet_edges(design, None, radius)

@dispatcher.register('holes')
def _holes(design, points, width, depth, faceindex):
    holes(design, None, points, width, depth, faceindex)

@dispatcher.register('threaded')
def _threaded(design, inside, allsizes):
    create_thread(design, None, inside, allsizes)

@dispatcher.register('circular_pattern')
def _circular_pattern(design, quantity, axis, plane):
    circular_pattern(design, None, quantity, axis, plane)

@dispatcher.register('rectangular_pattern')
def _rectangular_pattern(design, axis_one, axis_two, qty_one, qty_two, dist_one, dist_two, plane):
    rectangular_pattern(design, None, axis_one, axis_two, qty_one, qty_two, dist_one, dist_two, plane)

@dispatcher.register('move_body')
def _move_body(design, x, y, z):
    move_last_body(design, None, x, y, z)

@dispatcher.register('offsetplane')
def _offsetplane(design, offset, plane):
    offsetplane(design, None, offset, plane)

@dispatcher.register('export_stl')
def _export_stl(design, name):
    export_as_stl(design, None, name)

@dispatcher.register('export_step')
def _export_step(design, name):
    export_as_step(design, None, name)

@dispatcher.register('delete_everything')
def _delete_everything(design):
    delete_all(design, None)


# =============================================================================
# GET Route Handlers
# =============================================================================

@routes.get('/count_parameters')
def get_count_parameters(handler, design):
    from ..utils import get_model_parameters
    params = get_model_parameters(design)
    handler.send_json({"user_parameter_count": len(params)})

@routes.get('/list_parameters')
def get_list_parameters(handler, design):
    from ..utils import get_model_parameters
    params = get_model_parameters(design)
    handler.send_json({"ModelParameter": params})

@routes.get('/model_state')
def get_model_state(handler, design):
    state = get_current_model_state(design)
    handler.send_json(state)

@routes.get('/faces_info')
def get_faces(handler, design):
    params = handler.parse_query_params()
    body_idx = int(params.get('body_index', [0])[0])
    faces = get_faces_info(design, body_idx)
    handler.send_json(faces)

@routes.get('/script_result')
def get_script_result(handler, design):
    # This needs access to script_result from main module
    # Will be handled specially in the main MCP.py
    pass


# =============================================================================
# POST Route Handlers
# =============================================================================

@routes.post('/test_connection')
def post_test_connection(handler, design, data):
    handler.send_json({"success": True, "message": "Connection successful"})

@routes.post('/undo')
def post_undo(handler, design, data):
    handler.send_task_and_wait(('undo',), "Undo executed")

@routes.post('/Box')
def post_box(handler, design, data):
    height = float(data.get('height', 5))
    width = float(data.get('width', 5))
    depth = float(data.get('depth', 5))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    plane = data.get('plane', None)
    handler.send_task_and_wait(('draw_box', height, width, depth, x, y, z, plane), "Box created")

@routes.post('/draw_cylinder')
def post_cylinder(handler, design, data):
    radius = float(data.get('radius'))
    height = float(data.get('height'))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    plane = data.get('plane', 'XY')
    handler.send_task_and_wait(('draw_cylinder', radius, height, x, y, z, plane), "Cylinder created")

@routes.post('/sphere')
def post_sphere(handler, design, data):
    radius = float(data.get('radius', 5.0))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    handler.send_task_and_wait(('draw_sphere', radius, x, y, z), "Sphere created")

@routes.post('/create_circle')
def post_circle(handler, design, data):
    radius = float(data.get('radius', 1.0))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    plane = data.get('plane', 'XY')
    handler.send_task_and_wait(('circle', radius, x, y, z, plane), "Circle created")

@routes.post('/draw_lines')
def post_draw_lines(handler, design, data):
    points = data.get('points', [])
    plane = data.get('plane', 'XY')
    handler.send_task_and_wait(('draw_lines', points, plane), "Lines created")

@routes.post('/draw_one_line')
def post_draw_one_line(handler, design, data):
    x1 = float(data.get('x1', 0))
    y1 = float(data.get('y1', 0))
    z1 = float(data.get('z1', 0))
    x2 = float(data.get('x2', 1))
    y2 = float(data.get('y2', 1))
    z2 = float(data.get('z2', 0))
    plane = data.get('plane', 'XY')
    handler.send_task_and_wait(('draw_one_line', x1, y1, z1, x2, y2, z2, plane), "Line created")

@routes.post('/arc')
def post_arc(handler, design, data):
    point1 = data.get('point1', [0, 0])
    point2 = data.get('point2', [1, 1])
    point3 = data.get('point3', [2, 0])
    connect = bool(data.get('connect', False))
    plane = data.get('plane', 'XY')
    handler.send_task_and_wait(('arc', point1, point2, point3, connect, plane), "Arc created")

@routes.post('/spline')
def post_spline(handler, design, data):
    points = data.get('points', [])
    plane = data.get('plane', 'XY')
    handler.send_task_and_wait(('spline', points, plane), "Spline created")

@routes.post('/ellipsis')
def post_ellipsis(handler, design, data):
    handler.send_task_and_wait((
        'ellipsis',
        float(data.get('x_center', 0)),
        float(data.get('y_center', 0)),
        float(data.get('z_center', 0)),
        float(data.get('x_major', 10)),
        float(data.get('y_major', 0)),
        float(data.get('z_major', 0)),
        float(data.get('x_through', 5)),
        float(data.get('y_through', 4)),
        float(data.get('z_through', 0)),
        str(data.get('plane', 'XY'))
    ), "Ellipse created")

@routes.post('/draw_2d_rectangle')
def post_draw_2d_rectangle(handler, design, data):
    handler.send_task_and_wait((
        'draw_2d_rectangle',
        float(data.get('x_1', 0)),
        float(data.get('y_1', 0)),
        float(data.get('z_1', 0)),
        float(data.get('x_2', 1)),
        float(data.get('y_2', 1)),
        float(data.get('z_2', 0)),
        data.get('plane', 'XY')
    ), "2D rectangle created")

@routes.post('/draw_text')
def post_draw_text(handler, design, data):
    handler.send_task_and_wait((
        'draw_text',
        str(data.get('text', "Hello")),
        float(data.get('thickness', 0.5)),
        float(data.get('x_1', 0)),
        float(data.get('y_1', 0)),
        float(data.get('z_1', 0)),
        float(data.get('x_2', 10)),
        float(data.get('y_2', 4)),
        float(data.get('z_2', 0)),
        float(data.get('extrusion_value', 1.0)),
        str(data.get('plane', 'XY'))
    ), "Text created")

@routes.post('/extrude_last_sketch')
def post_extrude(handler, design, data):
    value = float(data.get('value', 1.0))
    taperangle = float(data.get('taperangle', 0))
    handler.send_task_and_wait(('extrude_last_sketch', value, taperangle), "Extrusion completed")

@routes.post('/extrude_thin')
def post_extrude_thin(handler, design, data):
    thickness = float(data.get('thickness', 0.5))
    distance = float(data.get('distance', 1.0))
    handler.send_task_and_wait(('extrude_thin', thickness, distance), "Thin extrusion created")

@routes.post('/cut_extrude')
def post_cut_extrude(handler, design, data):
    depth = float(data.get('depth', 1.0))
    handler.send_task_and_wait(('cut_extrude', depth), "Cut extrusion completed")

@routes.post('/loft')
def post_loft(handler, design, data):
    sketchcount = int(data.get('sketchcount', 2))
    handler.send_task_and_wait(('loft', sketchcount), "Loft created")

@routes.post('/sweep')
def post_sweep(handler, design, data):
    handler.send_task_and_wait(('sweep',), "Sweep created")

@routes.post('/revolve')
def post_revolve(handler, design, data):
    angle = float(data.get('angle', 360))
    handler.send_task_and_wait(('revolve_profile', angle), "Revolve completed")

@routes.post('/boolean_operation')
def post_boolean(handler, design, data):
    operation = data.get('operation', 'join')
    handler.send_task_and_wait(('boolean_operation', operation), "Boolean operation completed")

@routes.post('/shell_body')
def post_shell_body(handler, design, data):
    thickness = float(data.get('thickness', 0.5))
    faceindex = int(data.get('faceindex', 0))
    handler.send_task_and_wait(('shell_body', thickness, faceindex), "Shell body created")

@routes.post('/fillet_edges')
def post_fillet_edges(handler, design, data):
    radius = float(data.get('radius', 0.3))
    handler.send_task_and_wait(('fillet_edges', radius), "Fillet edges completed")

@routes.post('/holes')
def post_holes(handler, design, data):
    points = data.get('points', [[0, 0]])
    width = float(data.get('width', 1.0))
    faceindex = int(data.get('faceindex', 0))
    depth = data.get('depth', None)
    if depth is not None:
        depth = float(depth)
    handler.send_task_and_wait(('holes', points, width, depth, faceindex), "Hole created")

@routes.post('/threaded')
def post_threaded(handler, design, data):
    inside = bool(data.get('inside', True))
    allsizes = int(data.get('allsizes', 30))
    handler.send_task_and_wait(('threaded', inside, allsizes), "Thread created")

@routes.post('/circular_pattern')
def post_circular_pattern(handler, design, data):
    quantity = float(data.get('quantity'))
    axis = str(data.get('axis', "X"))
    plane = str(data.get('plane', 'XY'))
    handler.send_task_and_wait(('circular_pattern', quantity, axis, plane), "Circular pattern created")

@routes.post('/rectangular_pattern')
def post_rectangular_pattern(handler, design, data):
    handler.send_task_and_wait((
        'rectangular_pattern',
        str(data.get('axis_one', "X")),
        str(data.get('axis_two', "Y")),
        float(data.get('quantity_one', 2)),
        float(data.get('quantity_two', 2)),
        float(data.get('distance_one', 5)),
        float(data.get('distance_two', 5)),
        str(data.get('plane', 'XY'))
    ), "Rectangular pattern created")

@routes.post('/move_body')
def post_move_body(handler, design, data):
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    handler.send_task_and_wait(('move_body', x, y, z), "Body moved")

@routes.post('/offsetplane')
def post_offsetplane(handler, design, data):
    offset = float(data.get('offset', 0.0))
    plane = str(data.get('plane', 'XY'))
    handler.send_task_and_wait(('offsetplane', offset, plane), "Offset plane created")

@routes.post('/Export_STL')
def post_export_stl(handler, design, data):
    name = str(data.get('Name', 'Test.stl'))
    handler.send_task_and_wait(('export_stl', name), "STL export completed")

@routes.post('/Export_STEP')
def post_export_step(handler, design, data):
    name = str(data.get('name', 'Test.step'))
    handler.send_task_and_wait(('export_step', name), "STEP export completed")

@routes.post('/delete_everything')
def post_delete_everything(handler, design, data):
    handler.send_task_and_wait(('delete_everything',), "All bodies deleted")

@routes.post('/set_parameter')
def post_set_parameter(handler, design, data):
    name = data.get('name')
    value = data.get('value')
    if name and value:
        handler.send_task_and_wait(('set_parameter', name, value), f"Parameter {name} set")
