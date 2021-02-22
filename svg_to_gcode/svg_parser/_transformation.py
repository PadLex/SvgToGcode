import math
from copy import deepcopy

from svg_to_gcode.geometry import Vector, Matrix, IdentityMatrix


class Transformation:
    """
    The Transformation class handles the parsing and computation behind svg transform attributes.
    """
    __slots__ = "translation_matrix"

    def __init__(self):
        self.translation_matrix = IdentityMatrix(4)  # Fancy matrix used for translations and linear transformations

    def __repr__(self):
        return f"Transformation({self.translation_matrix})"

    def __deepcopy__(self, memodict={}):
        copy = Transformation()
        copy.translation_matrix = deepcopy(self.translation_matrix)

        return copy

    def add_transform(self, transform_string: str):
        transformations = transform_string.split(')')

        for transformation in transformations:
            transformation = transformation.strip()
            if not transformation or '(' not in transformation:
                continue

            command, arguments = transformation.split('(')
            command = command.replace(',', '')
            command = command.strip()
            arguments = [float(argument.strip()) for argument in arguments.replace(',', ' ').split()]

            command_method = {
                "matrix": self.add_matrix,
                "translate": self.add_translation,
                "scale": self.add_scale,
                "rotate": self.add_rotation,
                "skewX": self.add_skew_x,
                "skewY": self.add_skew_y
            }[command]

            command_method(*arguments)

    # SVG transforms are equivalent to CSS transforms https://www.w3.org/TR/css-transforms-1/#MatrixDefined
    def add_matrix(self, a, b, c, d, e, f):
        matrix = Matrix([
            [a, c, 0, e],
            [b, d, 0, f],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        self.translation_matrix *= matrix

    def add_translation(self, x: float, y=0.0):
        translation_matrix = Matrix([
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        self.translation_matrix *= translation_matrix

    def add_scale(self, factor: float):
        scale_matrix = Matrix([
            [factor, 0,      0, 0],
            [0,      factor, 0, 0],
            [0,      0,      1, 0],
            [0,      0,      0, 1]
        ])

        self.translation_matrix *= scale_matrix

    def add_rotation(self, angle: float):
        angle = math.radians(angle)
        rotation_matrix = Matrix([
            [math.cos(angle), -math.sin(angle), 0, 0],
            [math.sin(angle), math.cos(angle),  0, 0],
            [0,               0,                1, 0],
            [0,               0,                0, 1]
        ])

        self.translation_matrix *= rotation_matrix

    def add_skew_x(self, angle):
        angle = math.radians(angle)
        skew_matrix = IdentityMatrix(4)
        skew_matrix.matrix_list[0][1] = math.tan(angle)

        self.translation_matrix *= skew_matrix

    def add_skew_y(self, angle):
        angle = math.radians(angle)
        skew_matrix = IdentityMatrix(4)
        skew_matrix.matrix_list[1][0] = math.tan(angle)

        self.translation_matrix *= skew_matrix

    def apply_transformation(self, point: Vector) -> Vector:
        point_4d = Matrix([[point.x], [point.y], [1], [1]])
        point_4d = self.translation_matrix * point_4d

        return Vector(point_4d.matrix_list[0][0], point_4d.matrix_list[1][0])
