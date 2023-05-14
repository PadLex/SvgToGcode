import warnings
import math

from svg_to_gcode.formulas import linear_map
from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Vector
from svg_to_gcode import TOLERANCES

verbose = False


class Gcode(Interface):

    warn_nr = 0

    def __init__(self):
        self.position = None
        self._next_speed = None
        self._current_speed = None
        self._next_laser_power = None
        self._current_laser_power = None
        self._laser_mode = None
        self._laser_mode_changed = True
        self._bounding_box = None
        self._unit = None
        self._machine_params = None

        # Round outputs to the same number of significant figures as the operational tolerance.
        self.precision = abs(round(math.log(TOLERANCES["operation"], 10)))

    def set_machine_parameters(self, params):
        self._machine_params = params

    def code_initialize(self):
        # default G0 (rapid movement), G17 (select XY plane), G40 (turn cutter compensation off), G54 (use machine coordinate system 1)
        # G94 (set Feed rate to 'unit'/min)
        # note that G0 mode hase a machine defined movement speed ('Feed Rate') and is the default motion mode upon power up and reset.
        # note that some or all gcodes above might be machine defaults, this is to make sure they are
        return "; rapid movement,XY plane,cutter compensation off,coordinate system 1,move 'unit'/min\nG0 G17 G40 G54 G94"

    def set_movement_speed(self, speed):
        self._next_speed = speed
        return ''

    def rapid_move(self, x=None, y=None, z=None):
	# While in laser mode, G0 command sets 'rapid move' and disables the laser during the move (non cut moves),
	# G1 sets 'linear move' and makes a cut when the laser mode is either M3 (constant laser power) or M4 (dynamic
	# laser power). M4 does a cut only when an actual move takes place (otherwise the laser is disabled).

	# Note that G1 can have parameters ('Spindle Speed' and or 'Feed Rate'), but G0 can have none.
	# Note also that G0 is the default motion mode upon power up and reset.
        # See https://github.com/gnea/grbl/wiki/Grbl-v1.1-Laser-Mode

        # Don't do anything if rapid move was called without passing a value.
        if x is None and y is None and z is None:
            warnings.warn("rapid_move command invoked without arguments.")
            return ''

        # remove decimal places in coordinates
        x_precision = 0 if x is not None and x.is_integer() else self.precision
        y_precision = 0 if y is not None and y.is_integer() else self.precision
        z_precision = 0 if z is not None and z.is_integer() else self.precision

        command = ''
        # Move if at least one coordinate is set and a coordinate is not the same as the current position.
        command += f" X{x:.{x_precision}f}" if (x is not None and (self.position is None or abs(self.position.x - x) > TOLERANCES["operation"])) else ''
        command += f" Y{y:.{y_precision}f}" if (y is not None and (self.position is None or abs(self.position.y - y) > TOLERANCES["operation"])) else ''
        command += f" Z{z:.{z_precision}f}" if z is not None else ''

        # Don't do anything if the move is redundant.
        if command == '':
            warnings.warn("rapid_move command to the same position.")
            return ''

        command = "G0" + command

        if self.position is not None or (x is not None and y is not None):
            if x is None:
                x = self.position.x

            if y is None:
                y = self.position.y

            self.position = Vector(x, y)

        if verbose:
            print(f"Move to {x}, {y}, {z}")

        return command

    def linear_move(self, x=None, y=None, z=None):
	# While in laser mode, G0 command sets 'rapid move' and disables the laser during the move (non cut moves),
	# G1 sets 'linear move' and makes a cut when the laser mode is either M3 (constant laser power) or M4 (dynamic
	# laser power). M4 does a cut only when an actual move takes place (otherwise the laser is disabled).

	# Note that G1 can have parameters ('Spindle Speed' and or 'Feed Rate'), but G0 can have none.
	# Note also that G0 is the default motion mode upon power up and reset.
        # See https://github.com/gnea/grbl/wiki/Grbl-v1.1-Laser-Mode

        if self._next_speed is None:
            raise ValueError("Undefined movement speed. Call set_movement_speed before executing movement commands.")

        # Don't do anything if linear move was called without passing a value.
        if x is None and y is None and z is None:
            warnings.warn("linear_move command invoked without arguments.")
            return ''

        # remove decimal places in coordinates
        x_precision = 0 if x is not None and x.is_integer() else self.precision
        y_precision = 0 if y is not None and y.is_integer() else self.precision
        z_precision = 0 if z is not None and z.is_integer() else self.precision

        command = ''
        # Move if at least one coordinate is set and a coordinate is not the same as the current position.
        command += f" X{x:.{x_precision}f}" if (x is not None and (self.position is None or abs(self.position.x - x) > TOLERANCES["operation"])) else ''
        command += f" Y{y:.{y_precision}f}" if (y is not None and (self.position is None or abs(self.position.y - y) > TOLERANCES["operation"])) else ''
        command += f" Z{z:.{z_precision}f}" if z is not None else ''

        # Don't do anything if the move is redundant.
        if command == '':
            if Gcode.warn_nr > 2:
                warnings.warn("linear_move command to the same position.")
            Gcode.warn_nr += 1
            return ''

	# Note that G1 can have parameters 'Spindle Speed' (laser power) and or 'Feed Rate' (cutting speed), but G0 can have none.
        command = "G1" + command
	# add laser power (spindle speed) parameter when cutting speed changes
        if self._current_laser_power != self._next_laser_power:
            self._current_laser_power = self._next_laser_power
            command += f" S{self._current_laser_power}"
	# add movement speed (Feed rate) parameter when cutting speed changes
        if self._current_speed != self._next_speed:
            self._current_speed = self._next_speed
            command += f" F{self._current_speed}"

        if self.position is not None or (x is not None and y is not None):
            if x is None:
                x = self.position.x

            if y is None:
                y = self.position.y

            self.position = Vector(x, y)

        if verbose:
            print(f"Move to {x}, {y}, {z}")

        return command + ''

    def laser_off(self):
        self._laser_mode = 'M5'
        self._laser_mode_changed = True
        new_mode = "M5" + ("\nM9" if self._machine_params['fan'] else '') # laser off, (fan off when available)
        return f"{new_mode}"

    def set_laser_power(self, power):
        if power < 0 or power > 1:
            raise ValueError(f"{power} is out of bounds. Laser power must be given between 0 and 1. "
                             f"The interface will scale it correctly.")
	# set power for next linear move
        self._next_laser_power = int(linear_map(self._machine_params['minimum_laser_power'], self._machine_params['maximum_laser_power'], power))

        # (fan on when available), laser_on
        new_mode = ("\nM8" if self._machine_params['fan'] else '') + ("\n" + self._laser_mode if self._laser_mode_changed else '')
        self._laser_mode_changed = False
	# return laser mode (M3 constant laser power or M4 dynamic laser power) when laser mode changed
        return f"; Cut at {self._next_speed} {self._unit}/min, {int(power * 100)}% power{new_mode}"

    def set_laser_mode(self, mode):
	# set constant/dynamic laser power mode
        previous_laser_mode = self._laser_mode
        self._laser_mode = 'M3' if mode == "constant" else 'M4'

        self._laser_mode_changed = previous_laser_mode != self._laser_mode
        return ''

    def set_distance_mode(self, distance_mode):
        # set absolute/relative coordinates
        return self.set_absolute_coordinates() if distance_mode == "absolute" else self.set_relative_coordinates()

    def set_absolute_coordinates(self):
        return "G90"

    def set_relative_coordinates(self):
        return "G91"

    def program_end(self):
        return "M2"

    def dwell(self, milliseconds):
        # Gcode G4 parameter is in seconds:
        # http://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g4
        return f"G4 P{milliseconds/1000}"

    def set_origin_at_position(self):
        self.position = Vector(0, 0)
        return "G92 X0 Y0 Z0"

    def set_unit(self, unit):
        self._unit = unit
        if unit == "mm":
            return "G21"

        if unit == "inch":
            return "G20"

        return ''

    def home_axes(self):
        return "G28"
