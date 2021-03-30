import math

from svg_to_gcode import formulas
from svg_to_gcode.geometry import Vector, Matrix
from svg_to_gcode.geometry import Curve


# Todo investigate odd behaviour when transform_origin is false. Parsing it without transforming and then tracing to svg
#  without transforming translates the drawing up a little.
class EllipticalArc(Curve):
    """The EllipticalArc class inherits from the abstract Curve class and describes an elliptical arc."""

    __slots__ = 'center', 'radii', 'rotation', 'start_angle', 'sweep_angle', 'end_angle'

    def __init__(self, center: Vector, radii: Vector, rotation: float, start_angle: float, sweep_angle: float):

        # Assign and verify arguments
        self.center = center
        self.radii = radii
        self.rotation = rotation
        # Constrain angle within +-360 degrees
        self.start_angle = start_angle
        self.sweep_angle = sweep_angle

        # Calculate missing data
        self.end_angle = start_angle + sweep_angle
        self.start = self.angle_to_point(self.start_angle)
        self.end = self.angle_to_point(self.end_angle)

        self.sanity_check()

    def __repr__(self):
        return f"EllipticalArc(start: {self.start}, end: {self.end}, center: {self.center}, radii: {self.radii}," \
               f" rotation: {self.rotation}, start_angle: {self.start_angle}, sweep_angle: {self.sweep_angle})"

    def point(self, t):
        angle = formulas.linear_map(self.start_angle, self.end_angle, t)
        return self.angle_to_point(angle)

    def angle_to_point(self, angle):
        transformed_radii = Vector(self.radii.x * math.cos(angle), self.radii.y * math.sin(angle))
        point = Matrix([[math.cos(self.rotation), -math.sin(self.rotation)],
                        [math.sin(self.rotation), math.cos(self.rotation)]]) * transformed_radii + self.center
        return point

    def angle_to_point_(self, rad):
        at_origin = Vector(self.radii.x * math.cos(rad), self.radii.y * math.sin(rad))
        translated = self.center + formulas.rotate(at_origin, self.rotation, False)
        return translated

    def derivative(self, t):
        angle = formulas.linear_map(self.start_angle, self.end_angle, t)
        return self.angle_to_derivative(angle)

    def angle_to_derivative(self, rad):
        return -(self.radii.y / self.radii.x) * math.tan(rad)**-1

    def sanity_check(self):
        pass


class SVGEllipticalArc(Curve):
    """"""

    __slots__ = 'x', 'y', 'rc', 'rc_m1', 'rs', 'Jvx', 'Jvy', 'transformation'

    def __init__(self, rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x, y, transformation):
        self.x = x
        self.y = y
        self.transformation = transformation

        psi = math.radians(x_axis_rotation)
        c = math.cos(psi)
        s = math.sin(psi)
        a = 2 * rx
        b = 2 * ry
        ab_inv = 1 / (a * b)
        qx = (c * c) * (b * b) + (s * s) * (a * a)
        qy = (s * s) * (b * b) + (c * c) * (a * a)
        qxy = c * s * (b - a) * (b + a)
        v2 = (ab_inv * ab_inv) * (qx * x * x + qy * y * y + 2 * qxy * x * y)
        self.Jvx = ab_inv * (qxy * x + qy * y)
        self.Jvy = -ab_inv * (qx * x + qxy * y)

        rc_sign = 1 - 2 * large_arc_flag
        rs_sign = -1 + 2 * sweep_flag
        self.rc = 0
        self.rs = rs_sign

        if v2 < 1:
            self.rc = rc_sign * math.sqrt(1 - v2)
            self.rs = rs_sign * math.sqrt(v2)

        self.rc_m1 = 1 - self.rc

        self.start = self.point(0)
        self.end = self.point(1)

        self.sanity_check()

    def __repr__(self):
        return f"SvgEllipticalArc()"

    def point(self, t):

        p1 = (self.rc_m1 * t + self.rc) * t
        p2 = (self.rs - self.rs * t) * t
        p3_inv = 1 / ((self.rc_m1 * t - self.rc_m1) * 2 * t + 1)
        wc = p1 * p3_inv
        ws = p2 * p3_inv

        point = Vector(self.x * wc + self.Jvx * ws, self.y * wc + self.Jvy * ws)

        return self.transformation.apply_transformation(point)

    def derivative(self, t):
        raise NotImplementedError("Oops, the SVGEllipticalArc is temporary. You really should be using EllipticalArc.")

    def sanity_check(self):
        pass
