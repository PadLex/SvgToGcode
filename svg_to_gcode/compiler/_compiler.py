import warnings
import math
import copy

from typing import Any
from importlib.metadata import version
from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Curve
from svg_to_gcode.geometry import LineSegmentChain, Vector
from svg_to_gcode import DEFAULT_SETTING
from svg_to_gcode import TOLERANCES, SETTING, check_setting


class Compiler:
    """
    The Compiler class handles the process of drawing geometric objects using interface commands and assembling the
    resulting numerical control code.
    """

    def __init__(self, interface_class: Interface, custom_header: list[str] =None, custom_footer: list[str] =None,
                 params: dict[str, Any] = None):
        """

        :param interface_class: Specify which interface to use. The most common is the gcode interface.
        :param custom_header: A list of commands to be executed before all generated commands.
        :param custom_footer: A list of commands to be executed after all generated commands.
                              Default [laser_off, program_end]
        :param settings: dictionary to specify "unit", "pass_depth", "dwell_time", "movement_speed", etc.
        """

        self._boundingbox = None
        self.interface = interface_class()

        # Round outputs to the same number of significant figures as the operational tolerance.
        self.precision = abs(round(math.log(TOLERANCES["operation"], 10)))

        if params is None or not check_setting(params):
            raise ValueError(f"Please set at least 'maximum_laser_power' and 'movement_speed' from {SETTING}")

        # get default settings and update
        self.settings = copy.deepcopy(DEFAULT_SETTING)
        for key in params.keys():
            self.settings[key] = params[key]

        self.interface.set_machine_parameters(self.settings)

        if custom_header is None:
            custom_header = []

        if custom_footer is None:
            custom_footer = [self.interface.laser_off(), self.interface.program_end()]

        self.header = [self.interface.code_initialize(),
                       self.interface.set_unit(self.settings["unit"]),
                       self.interface.set_distance_mode(self.settings["distance_mode"])] + custom_header
        self.footer = custom_footer
        self.body: list[str] = []

    def compile(self, passes=1):

        """
        Assembles the code in the header, body and footer, saving it to a file.

        :param passes: the number of passes that should be made. Every pass the machine moves_down (z-axis) by
        self.pass_depth and self.body is repeated.
        :return returns the assembled code. self.header + [self.body, -self.pass_depth] * passes + self.footer
        """

        if len(self.body) == 0:
            warnings.warn("Compile with an empty body (no curves). Is this intentional?")

        # add generator info and boundingbox for this code
        gcode = [f"; SvgToGcode v{version('svg_to_gcode')}", f"; GRBL 1.1, unit={self.settings['unit']}, {self.settings['distance_mode']} coordinates",
                 f"; Boundingbox: (X{self._boundingbox[0].x:.{0 if self._boundingbox[0].x.is_integer() else self.precision}f},"
                 f"Y{self._boundingbox[0].y:.{0 if self._boundingbox[0].y.is_integer() else self.precision}f}) to "
                 f"(X{self._boundingbox[1].x:.{0 if self._boundingbox[1].x.is_integer() else self.precision}f},"
                 f"Y{self._boundingbox[1].y:.{0 if self._boundingbox[1].y.is_integer() else self.precision}f})"]

        if not self.check_bounds():
            warnings.warn("Cut is not within machine bounds. Is this intentional?")
            gcode += ["; WARNING: Cut is not within machine bounds of "
                      f"X[0,{self.settings['x_axis_maximum_travel']}], Y[0,{self.settings['y_axis_maximum_travel']}]"]

        gcode.extend(self.header)
        for i in range(passes):
            gcode += [f"; pass #{i+1}"]
            gcode.extend(self.body)

            if i < (passes - 1) and self.settings["pass_depth"] > 0:
                # If it isn't the last pass, turn off the laser and move down
                gcode.append(self.interface.laser_off())
                gcode.append(self.interface.set_relative_coordinates())
                gcode.append(self.interface.linear_move(z=-self.settings["pass_depth"]))
                gcode.append(self.interface.set_distance_mode(self.settings["distance_mode"]))

        gcode.extend(self.footer)

        gcode = filter(lambda command: len(command) > 0, gcode)

        return '\n'.join(gcode)

    def compile_to_file(self, file_name: str, curves: list[Curve], passes=1):
        """
        A wrapper for the self.compile method. Assembles the code in the header, body and footer, saving it to a file.

        :param file_name: the path to save the file.
        :param curves: SVG curves approximated by line segments.
        :param passes: the number of passes that should be made. Every pass the machine moves_down (z-axis) by
        self.pass_depth and self.body is repeated.
        """
        # set laser_power, cutting speed
        self.append_curves(curves)
        with open(file_name, 'w') as file:
            file.write(self.compile(passes=passes))

    def append_line_chain(self, line_chain: LineSegmentChain):
        """
        Draws a LineSegmentChain by calling interface.linear_move() for each segment. The resulting code is appended to
        self.body
        """

        if line_chain.chain_size() == 0:
            warnings.warn("Attempted to parse empty LineChain")
            return

        code = []
        start = line_chain.get(0).start

        # Move to the next line_chain when the next line segment doesn't connect to the end of the previous one.
        if self.interface.position is None or abs(self.interface.position - start) > TOLERANCES["operation"]:
            if self.interface.position is None or self.settings["rapid_move"]:
                # move to the next line_chain: set laser off, rapid move to start of chain,
                # set movement (cutting) speed, set laser mode and power on
                code = [self.interface.laser_off(), self.interface.rapid_move(start.x, start.y),
                        self.interface.set_movement_speed(self.settings["movement_speed"]),
                        self.interface.set_laser_mode(self.settings["laser_mode"]), self.interface.set_laser_power(self.settings["laser_power"])]

                self._boundingbox = [copy.deepcopy(start), copy.deepcopy(start)] if self._boundingbox is None else self._boundingbox
            else:
                # move to the next line_chain: set laser mode, set laser power to 0 (cutting is off),
                # set movement speed, (no rapid) move to start of chain, set laser to power
                code = [self.interface.set_laser_mode(self.settings["laser_mode"]), self.interface.set_laser_power(0),
                        self.interface.set_movement_speed(self.settings["movement_speed"]), self.interface.linear_move(start.x, start.y),
                        self.interface.set_laser_power(self.settings["laser_power"])]

            if self.settings["dwell_time"] > 0:
                code = [self.interface.dwell(self.settings["dwell_time"])] + code

        for line in line_chain:
            code.append(self.interface.linear_move(line.end.x, line.end.y))
            if self._boundingbox is not None:
                self._boundingbox[0].x = line.end.x if line.end.x < self._boundingbox[0].x else self._boundingbox[0].x
                self._boundingbox[0].y = line.end.y if line.end.y < self._boundingbox[0].y else self._boundingbox[0].y
                self._boundingbox[1].x = line.end.x if line.end.x > self._boundingbox[1].x else self._boundingbox[1].x
                self._boundingbox[1].y = line.end.y if line.end.y > self._boundingbox[1].y else self._boundingbox[1].y

        self.body.extend(code)

    def append_curves(self, curves: list[Curve]):
        """
        Draws curves by approximating them as line segments and calling self.append_line_chain().
        The resulting code is appended to self.body
        """
        for curve in curves:
            line_chain = LineSegmentChain()

            approximation = LineSegmentChain.line_segment_approximation(curve)

            line_chain.extend(approximation)

            self.append_line_chain(line_chain)

    def check_bounds(self):
        """
        Check if line segments are within the machine cutting area. Note that machine coordinate mode must
        be absolute and machine parameters 'x_axis_maximum_travel' and 'y_axis_maximum_travel' are set
        :return returns true when box is in machine area bounds or the above is false
        """

        machine_max = Vector(self.settings["x_axis_maximum_travel"],self.settings["y_axis_maximum_travel"])
        machine_max_set = machine_max.x is not None and machine_max.y is not None

        if not machine_max_set:
            warnings.warn("Please define machine cutting area, set parameter: 'x_axis_maximum_travel' and 'y_axis_maximum_travel'")

        if self.settings["distance_mode"] == "absolute" and machine_max_set:
            return (self._boundingbox[0].x >= 0 and self._boundingbox[0].y >=0
                    and self._boundingbox[1].x * (25.4 if self.settings["unit"] == "inch" else 1) <= machine_max.x
                    and self._boundingbox[1].y * (25.4 if self.settings["unit"] == "inch" else 1) <= machine_max.y)

        return True
