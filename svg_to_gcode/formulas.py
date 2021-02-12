"""
This script contains handy mathematical equations.
It's used to limit code repetition and abstract complicated formulas.
"""

import math
from svg_to_gcode.geometry import Vector


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

    angle *= -1 if v1.x * v2.y - v1.y * v2.x > 0 else 1

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

    if n > maximum:
        return mod_constrain(n - maximum, minimum, maximum)

    if n < minimum:
        return mod_constrain(n - minimum, minimum, maximum)

    return n

