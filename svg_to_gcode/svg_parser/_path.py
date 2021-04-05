import math
import warnings

from typing import List

from svg_to_gcode.geometry import Vector
from svg_to_gcode.geometry import Line, EllipticalArc, CubicBazier, QuadraticBezier
from svg_to_gcode.svg_parser import Transformation
from svg_to_gcode import formulas

verbose = False


class Path:
    """The Path class represents a generic svg path."""

    command_lengths = {'M': 2, 'm': 2, 'L': 2, 'l': 2, 'H': 1, 'h': 1, 'V': 1, 'v': 1, 'Z': 0, 'z': 0, 'C': 6, 'c': 6,
                       'Q': 4, 'q': 4, 'S': 4, 's': 4, 'T': 2, 't': 2, 'A': 7, 'a': 7}

    __slots__ = "curves", "initial_point", "current_point", "last_control", "canvas_height", "draw_move", \
                "transform_origin", "transformation"

    def __init__(self, d: str, canvas_height: float, transform_origin=True, transformation=None):
        self.canvas_height = canvas_height
        self.transform_origin = transform_origin

        self.curves = []
        self.initial_point = Vector(0, 0)  # type: Vector
        self.current_point = Vector(0, 0)
        self.last_control = None  # type: Vector

        self.transformation = Transformation()

        if self.transform_origin:
            self.transformation.add_translation(0, canvas_height)
            self.transformation.add_scale(1, -1)

        if transformation is not None:
            self.transformation.extend(transformation)

        try:
            self._parse_commands(d)
        except Exception as generic_exception:
            warnings.warn(f"Terminating path. The following unforeseen exception occurred: {generic_exception}")

    def __repr__(self):
        return f"Path({self.curves})"

    def _parse_commands(self, d: str):
        """Parse svg commands (stored in value of the d key) into geometric curves."""

        command_key = ''  # A character representing a specific command based on the svg standard
        command_arguments = []  # A list containing the arguments for the current command_key

        number_str = ''  # A buffer used to store numeric characters before conferring them to a number

        # Parse each character in d
        i = 0
        while i < len(d):
            character = d[i]

            is_numeric = character.isnumeric() or character in ['-', '.', 'e']  # Yes, "-6.2e-4" is a valid float.
            is_delimiter = character.isspace() or character in [',']
            is_command_key = character in self.command_lengths.keys()
            is_final = i == len(d) - 1

            # If the current command is complete, however the next command does not specify a new key, assume the next
            # command has the same key. This is implemented by inserting the current key before the next command and
            # restarting the loop without incrementing i
            try:
                if command_key and len(command_arguments) == self.command_lengths[command_key] and is_numeric:
                    duplicate = command_key
                    # If a moveto is followed by multiple pairs of coordinates, the subsequent pairs are treated as
                    # implicit lineto commands. https://www.w3.org/TR/SVG2/paths.html#PathDataMovetoCommands
                    if command_key == 'm':
                        duplicate = 'l'

                    if command_key == 'M':
                        duplicate = 'L'

                    d = d[:i] + duplicate + d[i:]
                    continue
            except KeyError as key_error:
                warnings.warn(f"Unknown command key {command_key}. Skipping curve.")

            # If the character is part of a number, keep on composing it
            if is_numeric:
                number_str += character

                # if a negative number follows another number, no delimiter is required.
                # implicitly stated decimals like .6 don't require a delimiter. In either case we add a delimiter.
                negatives = not is_final and character != 'e' and d[i + 1] == '-'
                implicit_decimals = not is_final and d[i + 1] == '.' and '.' in number_str
                if negatives or implicit_decimals:
                    d = d[:i+1] + ',' + d[i+1:]

            # If the character is a delimiter or a command key or the last character, complete the number and save it
            # as an argument
            if is_delimiter or is_command_key or is_final:
                if number_str:
                    # In svg form '-.5' can be written as '-.5'. Python doesn't like that notation.
                    if number_str[0] == '.':
                        number_str = '0' + number_str
                    if number_str[0] == '-' and number_str[1] == '.':
                        number_str = '-0' + number_str[1:]

                    command_arguments.append(float(number_str))
                    number_str = ''

            # If it's a command key or the last character, parse the previous (now complete) command and save the letter
            # as the new command key
            if is_command_key or is_final:
                if command_key:
                    self._add_svg_curve(command_key, command_arguments)

                command_key = character
                command_arguments.clear()

            # If the last character is a command key (only useful for Z), save
            if is_command_key and is_final:
                self._add_svg_curve(command_key, command_arguments)

            i += 1

    def _add_svg_curve(self, command_key: str, command_arguments: List[float]):
        """
        Offer a representation of a curve using the geometry sub-module.
        Based on Mozilla Docs: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths

        Each sub-method must be implemented with the following structure:
        def descriptive_name(*command_arguments):
            execute calculations and transformations, **do not modify or create any instance variables**
            generate curve
            modify instance variables
            return curve

        Alternatively a sub-method may simply call a base command.

        :param command_key: a character representing a specific command based on the svg standard
        :param command_arguments: A list containing the arguments for the current command_key
        """

        # Establish a new initial point and a new current point. (multiple coordinates are parsed as lineto commands)
        def absolute_move(x, y):
            self.initial_point = Vector(x, y)
            self.current_point = Vector(x, y)
            return None

        def relative_move(dx, dy):
            return absolute_move(*(self.current_point + Vector(dx, dy)))

        # Draw straight line
        def absolute_line(x, y):
            start = self.current_point
            end = Vector(x, y)

            line = Line(self.transformation.apply_affine_transformation(start),
                        self.transformation.apply_affine_transformation(end))

            self.current_point = end

            return line

        def relative_line(dx, dy):
            return absolute_line(*(self.current_point + Vector(dx, dy)))

        def absolute_horizontal_line(x):
            return absolute_line(x, self.current_point.y)

        def relative_horizontal_line(dx):
            return absolute_horizontal_line(self.current_point.x + dx)

        def absolute_vertical_line(y):
            return absolute_line(self.current_point.x, y)

        def relative_vertical_line(dy):
            return absolute_vertical_line(self.current_point.y + dy)

        def close_path():
            return absolute_line(*self.initial_point)

        # Draw curvy curves
        def absolute_cubic_bazier(control1_x, control1_y, control2_x, control2_y, x, y):

            trans_start = self.transformation.apply_affine_transformation(self.current_point)
            trans_end = self.transformation.apply_affine_transformation(Vector(x, y))
            trans_control1 = self.transformation.apply_affine_transformation(Vector(control1_x, control1_y))
            trans_control2 = self.transformation.apply_affine_transformation(Vector(control2_x, control2_y))

            cubic_bezier = CubicBazier(trans_start, trans_end, trans_control1, trans_control2)

            self.last_control = Vector(control2_x, control2_y)
            self.current_point = Vector(x, y)

            return cubic_bezier

        def relative_cubic_bazier(dx1, dy1, dx2, dy2, dx, dy):
            return absolute_cubic_bazier(self.current_point.x + dx1, self.current_point.y + dy1,
                                         self.current_point.x + dx2, self.current_point.y + dy2,
                                         self.current_point.x + dx, self.current_point.y + dy)

        def absolute_cubic_bezier_extension(x2, y2, x, y):
            start = self.current_point
            control2 = Vector(x2, y2)
            end = Vector(x, y)

            if self.last_control:
                control1 = 2 * start - self.last_control
                bazier = absolute_cubic_bazier(*control1, *control2, *end)
            else:
                bazier = absolute_quadratic_bazier(*control2, *end)

            self.current_point = start

            return bazier

        def relative_cubic_bazier_extension(dx2, dy2, dx, dy):
            return absolute_cubic_bezier_extension(self.current_point.x + dx2, self.current_point.y + dy2,
                                                   self.current_point.x + dx, self.current_point.y + dy)

        def absolute_quadratic_bazier(control1_x, control1_y, x, y):

            trans_end = self.transformation.apply_affine_transformation(self.current_point)
            trans_new_end = self.transformation.apply_affine_transformation(Vector(x, y))
            trans_control1 = self.transformation.apply_affine_transformation(Vector(control1_x, control1_y))

            quadratic_bezier = QuadraticBezier(trans_end, trans_new_end, trans_control1)

            self.last_control = Vector(control1_x, control1_y)
            self.current_point = Vector(x, y)

            return quadratic_bezier

        def relative_quadratic_bazier(dx1, dy1, dx, dy):
            return absolute_quadratic_bazier(self.current_point.x + dx1, self.current_point.y + dy1,
                                             self.current_point.x + dx, self.current_point.y + dy)

        def absolute_quadratic_bazier_extension(x, y):
            start = self.current_point
            end = Vector(x, y)

            if self.last_control:
                control = 2 * start - self.last_control
                bazier = absolute_quadratic_bazier(*control, *end)
            else:
                bazier = absolute_quadratic_bazier(*start, *end)

            self.current_point = end
            return bazier

        def relative_quadratic_bazier_extension(dx, dy):
            return absolute_quadratic_bazier_extension(self.current_point.x + dx, self.current_point.y + dy)

        # Generate EllipticalArc with center notation from svg endpoint notation.
        # Based on w3.org implementation notes. https://www.w3.org/TR/SVG2/implnote.html
        # Todo transformations aren't applied correctly to elliptical arcs
        def absolute_arc(rx, ry, deg_from_horizontal, large_arc_flag, sweep_flag, x, y):
            end = Vector(x, y)
            start = self.current_point

            radii = Vector(rx, ry)

            rotation_rad = math.radians(deg_from_horizontal)

            if abs(start-end) == 0:
                raise ValueError("start and end points can't be equal")

            radii, center, start_angle, sweep_angle = formulas.endpoint_to_center_parameterization(
                start, end, radii, rotation_rad, large_arc_flag, sweep_flag)

            arc = EllipticalArc(center, radii, rotation_rad, start_angle, sweep_angle, transformation=self.transformation)

            self.current_point = end
            return arc

        def relative_arc(rx, ry, deg_from_horizontal, large_arc_flag, sweep_flag, dx, dy):
            return absolute_arc(rx, ry, deg_from_horizontal, large_arc_flag, sweep_flag, self.current_point.x + dx, self.current_point.y + dy)

        command_methods = {
            # Only move end point
            'M': absolute_move,
            'm': relative_move,

            # Draw straight line
            'L': absolute_line,
            'l': relative_line,
            'H': absolute_horizontal_line,
            'h': relative_horizontal_line,
            'V': absolute_vertical_line,
            'v': relative_vertical_line,
            'Z': close_path,
            'z': close_path,

            # Draw bazier curves
            'C': absolute_cubic_bazier,
            'c': relative_cubic_bazier,
            'S': absolute_cubic_bezier_extension,
            's': relative_cubic_bazier_extension,
            'Q': absolute_quadratic_bazier,
            'q': relative_quadratic_bazier,
            'T': absolute_quadratic_bazier_extension,
            't': relative_quadratic_bazier_extension,

            # Draw elliptical arcs
            'A': absolute_arc,
            'a': relative_arc
        }

        try:
            curve = command_methods[command_key](*command_arguments)
        except TypeError as type_error:
            warnings.warn(f"Mis-formed input. Skipping command {command_key, command_arguments} because it caused the "
                          f"following error: \n{type_error}")
        except ValueError as value_error:
            warnings.warn(f"Impossible geometry. Skipping curve {command_key, command_arguments} because it caused the "
                          f"following value error:\n{value_error}")
        else:
            if curve is not None:
                self.curves.append(curve)

            if verbose:
                print(f"{command_key}{tuple(command_arguments)} -> {curve}")
