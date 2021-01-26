from svg_to_gcode.geometry import Vector
from svg_to_gcode.geometry import Curve
from svg_to_gcode import formulas


# A line segment
class Line(Curve):
    """The Line class inherits from the abstract Curve class and describes a straight line segment."""

    __slots__ = 'slope', 'offset'

    def __init__(self, start, end):
        self.start = start
        self.end = end

        self.slope = formulas.line_slope(start, end)
        self.offset = formulas.line_offset(start, end)

    def __repr__(self):
        return f"Line(start:{self.start}, end:{self.end}, slope:{self.slope}, offset:{self.offset})"

    def length(self):
        return abs(self.start - self.end)

    def point(self, t):
        x = self.start.x + t * (self.end.x - self.start.x)
        y = self.slope * x + self.offset

        return Vector(x, y)

    def derivative(self, t):
        return self.slope
