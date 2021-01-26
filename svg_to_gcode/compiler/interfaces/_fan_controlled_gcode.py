from svg_to_gcode.compiler.interfaces import Gcode
from svg_to_gcode import formulas


class FanControlledGcode(Gcode):

    def laser_off(self):
        if self._current_power is None or self._current_power > 0:
            self._current_power = 0
            return f"M107;"

        return ''

    def set_laser_power(self, power):
        self._current_power = power

        if power < 0 or power > 1:
            raise ValueError(f"{power} is out of bounds. Laser power must be given between 0 and 1. "
                             f"The interface will scale it correctly.")

        return f"M106 S{formulas.linear_map(0, 255, power)};"
