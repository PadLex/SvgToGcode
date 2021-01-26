from xml.etree import ElementTree
from typing import List
from svg_to_gcode.svg_parser import Path
from svg_to_gcode.geometry import Curve

NAMESPACES = {'svg': 'http://www.w3.org/2000/svg'}


# Todo deal with viewBoxes
def parse_string(svg_string, canvas_height=None, transform=True) -> List[Curve]:

    root = ElementTree.fromstring(svg_string)

    if canvas_height is None:
        height_str = root.get("height")

        if height_str.isnumeric():
            canvas_height = float(height_str)
        else:
            canvas_height = float(height_str[:-2])

    curves = []

    for xml_path in root.iter("{%s}path" % NAMESPACES["svg"]):
        path = Path(xml_path.attrib['d'], canvas_height, do_vertical_mirror=transform, do_vertical_translate=transform)
        curves.extend(path.curves)

    # ToDo implement shapes class

    return curves


def parse_file(file_path: str, canvas_height=None, transform=True):
    with open(file_path, 'r') as file:
        return parse_string(file.read(), canvas_height=canvas_height, transform=transform)
