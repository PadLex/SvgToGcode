import math

from svg_to_gcode import formulas
from svg_to_gcode.geometry import Vector, RotationMatrix
from svg_to_gcode.geometry import Curve


class EllipticalArc(Curve):
    """The EllipticalArc class inherits from the abstract Curve class and describes an elliptical arc."""

    __slots__ = 'center', 'radii', 'rotation', 'start_angle', 'sweep_angle', 'end_angle', 'transformation'

    # ToDo apply transformation beforehand (in Path) for consistency with other geometric objects. If you (the reader)
    #  know how to easily apply an affine transformation to an ellipse feel free to make a pull request.
    def __init__(self, center: Vector, radii: Vector, rotation: float, start_angle: float, sweep_angle: float,
                 transformation: None):

        # Assign and verify arguments
        self.center = center
        self.radii = radii
        self.rotation = rotation
        self.start_angle = start_angle
        self.sweep_angle = sweep_angle
        self.transformation = transformation

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
        point = RotationMatrix(self.rotation) * transformed_radii + self.center

        if self.transformation:
            point = self.transformation.apply_affine_transformation(point)

        return point

    def derivative(self, t):
        angle = formulas.linear_map(self.start_angle, self.end_angle, t)
        return self.angle_to_derivative(angle)

    def angle_to_derivative(self, rad):
        return -(self.radii.y / self.radii.x) * math.tan(rad)**-1

    def sanity_check(self):
        pass
