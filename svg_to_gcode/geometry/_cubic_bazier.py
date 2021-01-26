from svg_to_gcode.geometry import Vector
from svg_to_gcode.geometry import Curve


class CubicBazier(Curve):
    """The CubicBazier class inherits from the abstract Curve class and describes a cubic bazier."""

    __slots__ = 'control1', 'control2'

    def __init__(self, start: Vector, end: Vector, control1: Vector, control2: Vector):

        self.start = start
        self.end = end
        self.control1 = control1
        self.control2 = control2

    def __repr__(self):
        return f"CubicBazier(start: {self.start}, end: {self.end}, control1: {self.control1}, control2: {self.control2})"

    def point(self, t):
        return (1-t)**3 * self.start +\
               3 * (1-t)**2 * t * self.control1 +\
               3 * (1-t) * t**2 * self.control2 +\
               t**3 * self.end

    def derivative(self, t):
        return 3 * (1-t)**2 * (self.control1 - self.start) +\
               6 * (1-t) * t * (self.control2 - self.control1) +\
               3 * t**2 * (self.end - self.control2)

    def sanity_check(self):
        pass
