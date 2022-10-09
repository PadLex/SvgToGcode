from svg_to_gcode.compiler.interfaces import Gcode
from svg_to_gcode import formulas


class FanControlledGcode(Gcode):

    # Override the set_laser_power method, use gcode M7 - mist coolant - instead of M8 - flood coolant -
    # (note that setting 'fan' must be True for this to work)
    def set_laser_power(self, power):
        if power < 0 or power > 1:
            raise ValueError(f"{power} is out of bounds. Laser power must be given between 0 and 1. "
                             f"The interface will scale it correctly.")
	# set power for next linear move
        self._next_laser_power = int(formulas.linear_map(self._machine_params['minimum_laser_power'], self._machine_params['maximum_laser_power'], power))

        # (fan on when available, use M7 instead of M8), laser_on
        new_mode = ("\nM7" if self._machine_params['fan'] else '') + ("\n" + self._laser_mode if self._laser_mode_changed else '')
        self._laser_mode_changed = False
	# return laser mode (M3 constant laser power or M4 dynamic laser power) when laser mode changed
        return f"; Cut at {self._next_speed} {self._unit}/min, {int(power * 100)}% power{new_mode}"
