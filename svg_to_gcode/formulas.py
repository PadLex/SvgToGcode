"""
This script contains handy mathematical equations.
It's used to limit code repetition and abstract complicated math functions.
"""

import math
from svg_to_gcode.geometry import Vector, RotationMatrix
from svg_to_gcode import TOLERANCES


def tolerance_constrain(value, maximum, minimum, tolerance=TOLERANCES["operation"]):
    """
    Constrain a value between if it surpasses a limit and is within operational tolerance of the limit. Else return the
    value. Useful if you want to correct for flatting point errors but still want to raise an exception if the value is
    out-of-bounds for a different reason.
    """

    if value > maximum and value-maximum < tolerance:
        return maximum

    if value < minimum and minimum-value < tolerance:
        return minimum

    return value


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
    cos_angle = Vector.dot_product(v1, v2) / (abs(v1) * abs(v2))
    cos_angle = tolerance_constrain(cos_angle, 1, -1)

    angle = math.acos(cos_angle)

    angle *= 1 if v1.x * v2.y - v1.y * v2.x > 0 else -1

    return angle


def center_to_endpoint_parameterization(center, radii, rotation, start_angle, sweep_angle):
    rotation_matrix = RotationMatrix(rotation)

    start = rotation_matrix * Vector(radii.x * math.cos(start_angle), radii.y * math.sin(start_angle)) + center

    end_angle = start_angle + sweep_angle
    end = rotation_matrix * Vector(radii.x * math.cos(end_angle), radii.y * math.sin(end_angle)) + center

    large_arc_flag = 1 if abs(sweep_angle) > math.pi else 0
    sweep_flag = 1 if sweep_angle > 0 else 0

    return start, end, large_arc_flag, sweep_flag


def endpoint_to_center_parameterization(start, end, radii, rotation_rad, large_arc_flag, sweep_flag):
    # Find and select one of the two possible eclipse centers by undoing the rotation (to simplify the math) and
    # then re-applying it.
    rotated_primed_values = (start - end) / 2  # Find the primed_values of the start and the end points.
    primed_values = RotationMatrix(rotation_rad, True) * rotated_primed_values
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

    rotated_center = RotationMatrix(rotation_rad) * center + (start + end) / 2  # re-apply the rotation

    cx, cy = center.x, center.y
    u = Vector((px - cx) / rx, (py - cy) / ry)
    v = Vector((-px - cx) / rx, (-py - cy) / ry)

    max_angle = 2 * math.pi
    
    start_angle = angle_between_vectors(Vector(1, 0), u)
    sweep_angle_unbounded = angle_between_vectors(u, v)
    sweep_angle = sweep_angle_unbounded % max_angle

    if not sweep_flag and sweep_angle > 0:
        sweep_angle -= max_angle

    if sweep_flag and sweep_angle < 0:
        sweep_angle += max_angle

    return Vector(rx, ry), rotated_center, start_angle, sweep_angle
