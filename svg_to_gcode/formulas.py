"""
This script contains handy mathematical equations.
It's used to limit code repetition and abstract complicated 
"""

import math
from svg_to_gcode.geometry import Vector, Matrix


def line_slope(p1, p2):
    """Calculate the slope of the line p1p2"""
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y

    if x1 == x2:
        return 1

    return (y1 - y2) / (x1 - x2)


def line_offset(p1, p2):
    """Calculate the offset of the line p1p2 from the origin"""
    x1, y1 = p1.x, p1.y

    return y1 - line_slope(p1, p2) * x1


def line_intersect(p1, c1, p2, c2):
    """Find point of intersection between line p1c2 and p2c2"""
    p1_c, c1_c, p2_c, c2_c = p1.conjugate(), c1.conjugate(), p2.conjugate(), c2.conjugate()

    return (((c1_c - p1_c) * p1 - (c1 - p1) * p1_c) * (c2 - p2) - ((c2_c - p2_c) * p2 - (c2 - p2) * p2_c) * (
            c1 - p1)) / ((c2 - p2) * (c1_c - p1_c) - (c1 - p1) * (c2_c - p2_c))


def is_on_mid_perpendicular(z, a, b):
    """Check if a point z is on the line which is perpendicular to ab and passes through the segment's midpoint"""
    return ((2 * z - (a + b)) / (a - b)).x == 0


def tangent_arc_center(c, p, g):
    """Find center of circular arc which passes through p and g, and is tangent to the line pc"""
    c_c, p_c, g_c = c.conjugate(), p.conjugate(), g.conjugate()

    return (c * g * (p_c - g_c) + p * (g * (-2 * p_c + c_c + g_c) + (p_c - c_c) * p)
            ) / (g * (-p_c + c_c) + c * (p_c - g_c) + (-c_c + g_c) * p)


def linear_map(min, max, t):
    """Linear map from t∈[0, 1] --> t'∈[min, max]"""
    return (max - min) * t + min


def inv_linear_map(min, max, t_p):
    """Linear map from t'∈[min, max] --> t∈[0, 1]"""
    return (t_p - min)/(max - min)


def angle_between_vectors(v1, v2):
    """Compute angle between two vectors v1, v2"""
    angle = math.acos(Vector.dot_product(v1, v2) / (abs(v1) * abs(v2)))

    angle *= 1 if v1.x * v2.y - v1.y * v2.x > 0 else -1

    return angle


def rotate(p, r, inverted=False):
    """Rotate a point p by r radians. Remember that the y-axis is inverted in the svg standard."""
    x, y = p

    if inverted:
        return Vector(x * math.cos(r) + y * math.sin(r), - x * math.sin(r) + y * math.cos(r))

    return Vector(x * math.cos(r) - y * math.sin(r), + x * math.sin(r) + y * math.cos(r))


def mod_constrain(n, minimum, maximum):
    """
    Constrain a value n between a minimum and a maximum value (both inclusive). Out-of-range values are wrapped
    (like in a clock).
    """
    return n

    if n > maximum:
        return mod_constrain(n - maximum, minimum, maximum)

    if n < minimum:
        return mod_constrain(n - minimum, minimum, maximum)

    return n


def center_to_endpoint_parameterization(center, radii, rotation, start_angle, sweep_angle):
    rotation_matrix = Matrix([[math.cos(rotation), -math.sin(rotation)],
                              [math.sin(rotation), math.cos(rotation)]])
    #rotation_matrix = Matrix([[math.cos(rotation), math.sin(rotation)],
    #                          [-math.sin(rotation), math.cos(rotation)]])

    start = rotation_matrix * Vector(radii.x * math.cos(start_angle), radii.y * math.sin(start_angle)) + center

    end_angle = start_angle + sweep_angle
    end = rotation_matrix * Vector(radii.x * math.cos(end_angle), radii.y * math.sin(end_angle)) + center

    large_arc_flag = 1 if abs(sweep_angle) > math.pi else 0
    sweep_flag = 1 if sweep_angle > 0 else 0

    return start, end, large_arc_flag, sweep_flag

"""
def endpoint_to_center_parameterization_paper(start, end, radii, deg_from_horizontal, large_arc_flag, sweep_flag):
    theta = math.radians(deg_from_horizontal)

    R = radii.x
    k = radii.x / radii.y
    A = Matrix([
        [math.cos(theta), -math.sin(theta)],
        [math.sin(theta), math.cos(theta)]
    ])

    r12 = A*
"""


def endpoint_to_center_parameterization_alex(start, end, radii, rotation_rad, large_arc_flag, sweep_flag):
    # Find and select one of the two possible eclipse centers by undoing the rotation (to simplify the math) and
    # then re-applying it.
    rotated_primed_values = (start - end) / 2  # Find the primed_values of the start and the end points.
    #primed_values = rotate(rotated_primed_values, -rotation_rad, True)  # Undo the ellipse's rotation.
    primed_values = Matrix([[math.cos(rotation_rad), math.sin(rotation_rad)],
                            [-math.sin(rotation_rad), math.cos(rotation_rad)]]) * rotated_primed_values
    px, py = primed_values.x, primed_values.y

    # Correct out-of-range radii
    rx = abs(radii.x)
    ry = abs(radii.y)

    delta = px ** 2 / rx ** 2 + py ** 2 / ry ** 2

    if delta > 1:
        rx *= math.sqrt(delta)
        ry *= math.sqrt(delta)

    if math.sqrt(delta) > 1:
        center = Vector(0, 0)
    else:
        radicant = ((rx * ry) ** 2 - (rx * py) ** 2 - (ry * px) ** 2) / ((rx * py) ** 2 + (ry * px) ** 2)
        radicant = max(0, radicant)

        # Find center using w3.org's formula
        center = math.sqrt(radicant) * Vector((rx * py) / ry, - (ry * px) / rx)

        center *= -1 if large_arc_flag == sweep_flag else 1  # Select one of the two solutions based on flags

    rotated_center = rotate(center, rotation_rad, False) + (start + end) / 2  # re-apply the rotation

    cx, cy = center.x, center.y
    u = Vector((px - cx) / rx, (py - cy) / ry)
    v = Vector((-px - cx) / rx, (-py - cy) / ry)

    max_angle = 2 * math.pi
    
    start_angle = angle_between_vectors(Vector(1, 0), u)
    sweep_angle_unbounded = angle_between_vectors(u, v)
    sweep_angle = sweep_angle_unbounded % max_angle

    """
    if not sweep_flag and sweep_angle > 0:
        sweep_angle -= max_angle

    if sweep_flag and sweep_angle < 0:
        sweep_angle += max_angle
    """

    print("delta:", delta, "radii:", Vector(rx, ry), "center", rotated_center, "start_angle", math.degrees(start_angle),
          "sweep_angle", math.degrees(sweep_angle), "u:", u, "v:", v)

    return Vector(rx, ry), rotated_center, start_angle, sweep_angle


def endpoint_to_center_parameterization_lib(p0, p1, radii, xAxisRotationRadians, largeArcFlag, sweepFlag):
    # Following "Conversion rom endpoint to center parameterization"
    # http:#www.w3.org/TR/SVG/implnote.html#ArcConversionEndpointToCenter

    rx = abs(radii.x)
    ry = abs(radii.y)

    # Step #1: Compute transormedPoint
    dx = (p0.x - p1.x) / 2
    dy = (p0.y - p1.y) / 2
    transormedPoint = Vector(
        math.cos(xAxisRotationRadians) * dx + math.sin(xAxisRotationRadians) * dy,
        -math.sin(xAxisRotationRadians) * dx + math.cos(xAxisRotationRadians) * dy
    )

    # Ensure radii are large enough
    radiiCheck = pow(transormedPoint.x, 2) / pow(rx, 2) + pow(transormedPoint.y, 2) / pow(ry, 2)
    if radiiCheck > 1:
        rx = math.sqrt(radiiCheck) * rx
        ry = math.sqrt(radiiCheck) * ry

    # Step #2: Compute transormedCenter
    cSquareNumerator = pow(rx, 2) * pow(ry, 2) - pow(rx, 2) * pow(transormedPoint.y, 2) - pow(ry, 2) * pow(
        transormedPoint.x, 2)
    cSquareRootDenom = pow(rx, 2) * pow(transormedPoint.y, 2) + pow(ry, 2) * pow(transormedPoint.x, 2)
    cRadicand = cSquareNumerator / cSquareRootDenom
    # Make sure this never drops below zero because o precision
    cRadicand = max(0, cRadicand)
    cCoe = math.sqrt(cRadicand)
    cCoe *= -1 if largeArcFlag == sweepFlag else 1

    transormedCenter = Vector(
        cCoe * ((rx * transormedPoint.y) / ry),
        cCoe * (-(ry * transormedPoint.x) / rx)
    )

    # Step #3: Compute center
    center = Vector(
        math.cos(xAxisRotationRadians) * transormedCenter.x - math.sin(xAxisRotationRadians) * transormedCenter.y + (
                    (p0.x + p1.x) / 2),
        math.sin(xAxisRotationRadians) * transormedCenter.x + math.cos(xAxisRotationRadians) * transormedCenter.y + (
                    (p0.y + p1.y) / 2)
    )

    # Step #4: Compute start/sweep angles
    # Start angle o the elliptical arc prior to the stretch and rotate operations.
    # Dierence between the start and end angles
    startVector = Vector(
        (transormedPoint.x - transormedCenter.x) / rx,
        (transormedPoint.y - transormedCenter.y) / ry
    )
    startAngle = angle_between_lib(Vector(1.0, 0.0), startVector)

    endVector = Vector(
        (-transormedPoint.x - transormedCenter.x) / rx,
        (-transormedPoint.y - transormedCenter.y) / ry
    )

    sweepAngle = angle_between_lib(startVector, endVector)

    if not sweepFlag and sweepAngle > 0:
        sweepAngle -= 2 * math.pi

    elif sweepFlag and sweepAngle < 0:
        sweepAngle += 2 * math.pi

    # We use % instead o `mod(..)` because we want it to be -360deg to 360deg(but actually in radians)
    sweepAngle = sweepAngle % 2 * math.pi

    return Vector(rx, ry), center, startAngle, sweepAngle


def angle_between_lib(v0, v1):
    p = v0.x * v1.x + v0.y * v1.y
    n = math.sqrt((math.pow(v0.x, 2) + math.pow(v0.y, 2)) * (math.pow(v1.x, 2) + math.pow(v1.y, 2)))
    sign = -1 if v0.x * v1.y - v0.y * v1.x < 0 else 1
    angle = sign * math.acos(p / n)

    # angle = math.atan2(v0.y, v0.x) - math.atan2(v1.y,  v1.x)

    return angle


def endpoint_to_center_parameterization_blog(p1: Vector, p2: Vector, r_: Vector, x_angle: float, flag_a: bool, flag_s: bool):
    rx = abs(r_.x)
    ry = abs(r_.y)

    # (F.6.5.1)
    dx2 = (p1.x - p2.x) / 2.0
    dy2 = (p1.y - p2.y) / 2.0
    x1p = math.cos(x_angle) * dx2 + math.sin(x_angle) * dy2
    y1p = -math.sin(x_angle) * dx2 + math.cos(x_angle) * dy2

    # (F.6.5.2)
    rxs = rx * rx
    rys = ry * ry
    x1ps = x1p * x1p
    y1ps = y1p * y1p
    # check if the radius is too small `pq < 0`, when `dq > rxs * rys` (see below)
    # cr is the ratio (dq : rxs * rys)
    cr = x1ps / rxs + y1ps / rys
    if cr > 1:
        # scale up rx,ry equally so cr == 1
        s = math.sqrt(cr)
        rx = s * rx
        ry = s * ry
        rxs = rx * rx
        rys = ry * ry

    dq = (rxs * y1ps + rys * x1ps)
    pq = (rxs * rys - dq) / dq
    q = math.sqrt(max(0, pq))  # use Max to account for float precision
    if flag_a == flag_s:
        q = -q
    cxp = q * rx * y1p / ry
    cyp = - q * ry * x1p / rx

    # (F.6.5.3)
    cx = math.cos(x_angle) * cxp - math.sin(x_angle) * cyp + (p1.x + p2.x) / 2
    cy = math.sin(x_angle) * cxp + math.cos(x_angle) * cyp + (p1.y + p2.y) / 2

    # (F.6.5.5)
    theta = svg_angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    # (F.6.5.6)
    delta = svg_angle(
        (x1p - cxp) / rx, (y1p - cyp) / ry,
        (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    delta = delta % math.pi * 2
    if not flag_s:
        delta -= 2 * math.pi

    r_ = Vector(rx, ry)
    c = Vector(cx, cy)
    angles = Vector(theta, delta)

    return r_, c, theta, delta


def svg_angle(ux, uy, vx, vy):
    u = Vector(ux, uy)
    v = Vector(vx, vy)
    # (F.6.5.4)
    dot = u * v
    len = abs(u) * abs(v)
    ang = math.acos(min(max(dot / len, -1), 1))  # floating point precision, slightly over values appear
    if (u.x * v.y - u.y * v.x) < 0:
        ang = -ang
    return ang
