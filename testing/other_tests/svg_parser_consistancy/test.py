from xml.etree.ElementTree import Element, ElementTree

from svg_to_gcode.svg_parser import parse_file, parse_string, parse_root
from svg_to_gcode.geometry import LineSegmentChain

from svg_to_gcode import TOLERANCES

name_space = 'http://www.w3.org/2000/svg'


def run_test(svg_file_name, _):
    root = ElementTree().parse(svg_file_name)
    root_curves = parse_root(root)

    with open(svg_file_name, 'rb') as svg_file:
        svg_string = svg_file.read()
    string_curves = parse_string(svg_string)

    file_curves = parse_file(svg_file_name)

    if str(root_curves) != str(string_curves) or str(string_curves) != str(file_curves):
        print("Inconsistent parsing.")
        print("parse_root() ->", root_curves)
        print("parse_string() ->", string_curves)
        print("parse_file() ->", file_curves)
        return False

    return True




