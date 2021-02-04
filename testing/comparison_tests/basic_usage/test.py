from svg_to_gcode.svg_parser import parse_string
from svg_to_gcode.compiler import Compiler, interfaces


def run_test(svg_string):

    gcode_compiler = Compiler(interfaces.Gcode, 1000, 300, 2)

    curves = parse_string(svg_string, transform=True)
    gcode_compiler.append_curves(curves)
    return gcode_compiler.compile(passes=5)
