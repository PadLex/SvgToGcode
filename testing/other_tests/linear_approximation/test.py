from xml.etree.ElementTree import Element, ElementTree

from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.geometry import LineSegmentChain

from svg_to_gcode import TOLERANCES
#TOLERANCES["approximation"] = 10**-2

name_space = 'http://www.w3.org/2000/svg'


def run_test(svg_file_name, debug_file_name):
    curves = parse_file(svg_file_name)

    success = True
    approximations = []
    for curve in curves:
        approximation = LineSegmentChain.line_segment_approximation(curve)
        approximations.append(approximation)

        # Todo find a way to automatically determine success. Right now manual revision of debug files is required.

    generate_debug(approximations, svg_file_name, debug_file_name)

    return success


def generate_debug(approximations, svg_file_name, debug_file_name):
    tree = ElementTree()
    tree.parse(svg_file_name)

    root = tree.getroot()

    height_str = root.get("height")
    canvas_height = float(height_str) if height_str.isnumeric() else float(height_str[:-2])

    for path in root.iter("{%s}path" % name_space):
        path.set("fill", "none")
        path.set("stroke", "black")
        path.set("stroke-width", f"{TOLERANCES['approximation']}mm")
        path.set("style", "")

    group = Element("{%s}g" % name_space)

    for approximation in approximations:
        path = Element("{%s}path" % name_space)
        path.set("d", approximation.to_svg_path(wrapped=False, transform=True, height=canvas_height))
        path.set("fill", "none")
        path.set("stroke", "red")
        path.set("stroke-width", f"{TOLERANCES['approximation']/2}mm")

        group.append(path)

    root.append(group)

    tree.write(debug_file_name)

