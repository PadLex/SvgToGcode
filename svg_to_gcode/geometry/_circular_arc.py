import math

from svg_to_gcode.geometry import Vector
from svg_to_gcode.geometry import Curve
from svg_to_gcode import formulas
from svg_to_gcode import TOLERANCES


class CircularArc(Curve):
    """The CircularArc class inherits from the abstract Curve class and describes a circular arc."""

    __slots__ = 'center', 'radius', 'start_angle', 'end_angle'

    # ToDo use different instantiation parameters to be consistent with elliptical arcs
    def __init__(self, start: Vector, end: Vector, center: Vector):
        self.start = start
        self.end = end
        self.center = center

        self.radius = abs(self.start - self.center)
        self.start_angle = self.point_to_angle(self.start)
        self.end_angle = self.point_to_angle(self.end)

    def __repr__(self):
        return f"Arc(start: {self.start}, end: {self.end}, center: {self.center})"

    def length(self):
        return abs(self.start_angle - self.end_angle) * self.radius

    def angle_to_point(self, rad):
        at_origin = self.radius * Vector(math.cos(rad), math.sin(rad))
        translated = at_origin + self.center
        return translated

    def point_to_angle(self, point: Vector):
        translated = (point - self.center)/self.radius  # translate the point onto the unit circle
        return math.acos(translated.x)

    def point(self, t):
        angle = formulas.linear_map(self.start_angle, self.end_angle, t)
        return self.angle_to_point(angle)

    def derivative(self, t):
        position = self.point(t)
        return (self.center.x - position.x) / (position.y - self.center.y)

    def sanity_check(self):
        # Assert that the Arc is not a point or a line
        try:
            assert abs(self.start - self.end) > TOLERANCES["input"]
        except AssertionError:
            raise ValueError(f"Arc is a point. The start and the end points are equivalent: "
                             f"|{self.start} - {self.end}| <= {TOLERANCES['input']}")

        try:
            assert abs(self.start - self.center) > TOLERANCES["input"]
        except AssertionError:
            raise ValueError(f"Arc is a line. The start and the center points are equivalent, "
                             f"|{self.start} - {self.center}| <= {TOLERANCES['input']}")

        try:
            assert abs(self.end - self.center) > TOLERANCES["input"]
        except AssertionError:
            raise ValueError(f"Arc is a line. The end and the center points are equivalent, "
                             f"|{self.end} - {self.center}| <= {TOLERANCES['input']}")

        # Assert that the center is equidistant from the start and the end
        try:
            assert abs(abs(self.start - self.center) - abs(self.end - self.center)) < TOLERANCES['input']
        except AssertionError:
            raise ValueError(f"Center is not equidistant to the start and end points within tolerance, "
                             f"|{abs(self.start - self.center)} - {abs(self.end - self.center)}| >= {TOLERANCES['input']}")
