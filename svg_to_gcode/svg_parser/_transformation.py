import math
from copy import deepcopy

from svg_to_gcode.geometry import Vector, Matrix, IdentityMatrix


class Transformation:
    """
    The Transformation class handles the parsing and computation behind svg transform attributes.
    """
    __slots__ = "translation_matrix", "transformation_record", "command_methods"

    def __init__(self):
        # Fancy matrix used for affine transformations (translations and linear transformations)
        self.translation_matrix = IdentityMatrix(4)

        self.transformation_record = []

        self.command_methods = {
                "matrix": self.add_matrix,
                "translate": self.add_translation,
                "scale": self.add_scale,
                "rotate": self.add_rotation,
                "skewX": self.add_skew_x,
                "skewY": self.add_skew_y
            }

    def __repr__(self):
        transformations = ", ".join(
            [f"{transformation[0]}("f"{', '.join(map(lambda x: str(x), self.transformation_record[0][1]))})"
                                    for transformation in self.transformation_record])
        return f"Transformation({transformations})"

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

            command_method = self.command_methods[command]

            command_method(*arguments)

    # SVG transforms are equivalent to CSS transforms https://www.w3.org/TR/css-transforms-1/#MatrixDefined
    def add_matrix(self, a, b, c, d, e, f):
        self.transformation_record.append(("matrix", [a, b, c, d, e, f]))
        matrix = Matrix([
            [a, c, 0, e],
            [b, d, 0, f],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        self.translation_matrix *= matrix

    def add_translation(self, x: float, y=0.0):
        self.transformation_record.append(("translate", [x, y]))
        translation_matrix = Matrix([
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        self.translation_matrix *= translation_matrix

    def add_scale(self, factor: float, factor_y=None):
        factor_x = factor
        factor_y = factor if factor_y is None else factor_y

        self.transformation_record.append(("scale", [factor_x, factor_y]))

        scale_matrix = Matrix([
            [factor_x, 0,        0, 0],
            [0,        factor_y, 0, 0],
            [0,        0,        1, 0],
            [0,        0,        0, 1]
        ])

        self.translation_matrix *= scale_matrix

    def add_rotation(self, angle: float):
        self.transformation_record.append(("rotate", [angle]))

        angle = math.radians(angle)
        rotation_matrix = Matrix([
            [math.cos(angle), -math.sin(angle), 0, 0],
            [math.sin(angle), math.cos(angle),  0, 0],
            [0,               0,                1, 0],
            [0,               0,                0, 1]
        ])

        self.translation_matrix *= rotation_matrix

    def add_skew_x(self, angle):
        self.transformation_record.append(("skewX", [angle]))

        angle = math.radians(angle)
        skew_matrix = IdentityMatrix(4)
        skew_matrix.matrix_list[0][1] = math.tan(angle)

        self.translation_matrix *= skew_matrix

    def add_skew_y(self, angle):
        self.transformation_record.append(("skewY", [angle]))

        angle = math.radians(angle)
        skew_matrix = IdentityMatrix(4)
        skew_matrix.matrix_list[1][0] = math.tan(angle)

        self.translation_matrix *= skew_matrix

    def extend(self, other: "Transformation"):
        self.translation_matrix *= other.translation_matrix
        self.transformation_record.extend(other.transformation_record)

    def apply_affine_transformation(self, vector: Vector) -> Vector:
        """
        Apply the full affine transformation (linear + translation) to a vector. Generally used to transform points.
        Eg the center of an ellipse.
        """
        vector_4d = Matrix([[vector.x], [vector.y], [1], [1]])
        vector_4d = self.translation_matrix * vector_4d

        return Vector(vector_4d.matrix_list[0][0], vector_4d.matrix_list[1][0])

    def apply_linear_transformation(self, vector: Vector) -> Vector:
        """
        Apply the linear component of the affine transformation (no translation) to a vector.
        Generally used to transform vector properties. Eg the radii of an ellipse.
        """
        a = self.translation_matrix[0][0]
        b = self.translation_matrix[1][0]
        c = self.translation_matrix[0][1]
        d = self.translation_matrix[1][1]

        linear_transformation = Matrix([
            [a, c],
            [b, d]
        ])

        return linear_transformation * vector
