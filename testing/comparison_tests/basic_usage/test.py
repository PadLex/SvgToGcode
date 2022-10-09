from svg_to_gcode.svg_parser import parse_string
from svg_to_gcode.compiler import Compiler, interfaces


def run_test(svg_string):

    gcode_compiler = Compiler(interfaces.Gcode, params={"laser_power":1,"movement_speed":300,"maximum_laser_power":255,"pass_depth":2})

    curves = parse_string(svg_string, transform_origin=True)
    gcode_compiler.append_curves(curves)
    return gcode_compiler.compile(passes=5)
