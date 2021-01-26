"""
This script contains handy mathematical equations.
It's useful to limit code repetition and abstract complicated formulas.
"""

import math
from svg_to_gcode.geometry import Vector


# Calculate the slope of the line p1p2
def line_slope(p1, p2):
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y

    if x1 == x2:
        return 1

    return (y1 - y2) / (x1 - x2)


# Calculate the offset of the line p1p2 from the origin
def line_offset(p1, p2):
    x1, y1 = p1.x, p1.y

    return y1 - line_slope(p1, p2) * x1


# Find point of intersection between line p1c2 and p2c2
def line_intersect(p1, c1, p2, c2):
    p1_c, c1_c, p2_c, c2_c = p1.conjugate(), c1.conjugate(), p2.conjugate(), c2.conjugate()

    return (((c1_c - p1_c) * p1 - (c1 - p1) * p1_c) * (c2 - p2) - ((c2_c - p2_c) * p2 - (c2 - p2) * p2_c) * (
            c1 - p1)) / ((c2 - p2) * (c1_c - p1_c) - (c1 - p1) * (c2_c - p2_c))


# Check if a point z is on the line which is perpendicular to ab and passes through the segment's midpoint
def is_on_mid_perpendicular(z, a, b):
    return ((2 * z - (a + b)) / (a - b)).x == 0


# Find center of circular arc which passes through p and g, and is tangent to the line pc
def tangent_arc_center(c, p, g):
    c_c, p_c, g_c = c.conjugate(), p.conjugate(), g.conjugate()

    return (c * g * (p_c - g_c) + p * (g * (-2 * p_c + c_c + g_c) + (p_c - c_c) * p)
            ) / (g * (-p_c + c_c) + c * (p_c - g_c) + (-c_c + g_c) * p)


# Linear map from t∈[0, 1] --> t'∈[min, max]
def linear_map(min, max, t):
    return (max - min) * t + min


# Linear map from t'∈[min, max] --> t∈[0, 1]
def inv_linear_map(min, max, t_p):
    return (t_p - min)/(max - min)


# Compute angle between two vectors v1, v2
def angle_between_vectors(v1, v2):
    x1, y1 = v1.x, v1.y
    x2, y2 = v2.x, v2.y

    dot_product = x1 * x2 + y1 * y2
    magnitude1 = math.sqrt(x1 ** 2 + y1 ** 2)
    magnitude2 = math.sqrt(x2 ** 2 + y2 ** 2)

    angle = math.acos(dot_product / (magnitude1 * magnitude2))

    angle *= -1 if x1 * y2 - y1 * x2 > 0 else 1

    return angle


# Rotate a point p by r radians. Remember that the y-axis is inverted in the svg standard.
def rotate(p, r, inverted=False):
    x, y = p.x, p.y

    if inverted:
        return Vector(x * math.cos(r) + y * math.sin(r), - x * math.sin(r) + y * math.cos(r))

    return Vector(x * math.cos(r) - y * math.sin(r), + x * math.sin(r) + y * math.cos(r))
