import math

from svg_to_gcode import formulas
from svg_to_gcode.geometry import Vector
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
        max_angle = 2*math.pi
        self.start_angle = formulas.mod_constrain(start_angle, -max_angle, max_angle)
        self.sweep_angle = formulas.mod_constrain(sweep_angle, -max_angle, max_angle)

        # Calculate missing data
        self.end_angle = formulas.mod_constrain(start_angle + sweep_angle, -max_angle, max_angle)
        self.start = self.angle_to_point(self.start_angle)
        self.end = self.angle_to_point(self.end_angle)

        self.sanity_check()

    def __repr__(self):
        return f"EllipticalArc(start: {self.start}, end: {self.end}, center: {self.center}, radii: {self.radii}," \
               f" rotation: {self.rotation}, start_angle: {self.start_angle}, sweep_angle: {self.sweep_angle})"

    def point(self, t):
        angle = formulas.linear_map(self.start_angle, self.end_angle, t)
        return self.angle_to_point(angle)

    def angle_to_point(self, rad):
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
