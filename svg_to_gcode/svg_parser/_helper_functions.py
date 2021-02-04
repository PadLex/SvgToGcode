from xml.etree import ElementTree
from typing import List
from svg_to_gcode.svg_parser import Path
from svg_to_gcode.geometry import Curve

NAMESPACES = {'svg': 'http://www.w3.org/2000/svg'}


def _has_style(element: ElementTree.Element, key: str, value: str) -> bool:
    """
    Check if an element contains a specific key and value either as an independent attribute or in the style attribute.
    """
    return element.get(key) == value or (element.get("style") and f"{key}:{value}" in element.get("style"))


def parse_root(root: ElementTree.Element, canvas_height=None, transform=True, draw_hidden=False, _visible_root=True) \
        -> List[Curve]:

    """
    Recursively parse an etree root's children into geometric curves.

    :param root: The etree element who's children should be recursively parsed. The root will not be drawn.
    :param canvas_height: The height of the canvas. By default the height attribute of the root is used. If the root
    does not contain the height attribute, it must be either manually specified or transform must be False.
    :param transform: Whether or not to transform input coordinates from the svg coordinate system to standard cartesian
     system. Depends on canvas_height for calculations.
    :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
    :param _visible_root: Internally used to specify whether or the root is visible. (Inheritance can be overridden)
    :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
    """

    if canvas_height is None:
        height_str = root.get("height")
        canvas_height = float(height_str) if height_str.isnumeric() else float(height_str[:-2])

    curves = []

    if draw_hidden:
        # Parse paths
        for element in root.iter("{%s}path" % NAMESPACES["svg"]):
            path = Path(element.attrib['d'], canvas_height, transform, transform)
            curves.extend(path.curves)
    else:
        # Draw visible elements (Depth-first search)
        for element in list(root):

            # display cannot be overridden by inheritance. Just skip the element
            if _has_style(element, "display", "none"):
                continue

            # Is the element and it's root not hidden?
            visible = _visible_root and not (_has_style(element, "visibility", "hidden")
                                             or _has_style(element, "visibility", "collapse"))
            # Override inherited visibility
            visible = visible or (_has_style(element, "visibility", "visible"))

            transparent = _has_style(element, "opacity", "0")

            # If the current element is opaque and visible, draw it
            if not transparent and visible:
                if element.tag == "{%s}path" % NAMESPACES["svg"]:
                    path = Path(element.attrib['d'], canvas_height, transform, transform)
                    curves.extend(path.curves)

            # Continue the recursion
            curves.extend(parse_root(element, canvas_height, transform, False, visible))

    # ToDo implement shapes class
    return curves


# Todo deal with viewBoxes
def parse_string(svg_string: str, canvas_height=None, transform=True, draw_hidden=False) -> List[Curve]:
    """
        Recursively parse an svg string into geometric curves. (Wrapper for parse_root)

        :param svg_string: The etree element who's children should be recursively parsed. The root will not be drawn.
        :param canvas_height: The height of the canvas. By default the height attribute of the root is used. If the root
        does not contain the height attribute, it must be either manually specified or transform must be False.
        :param transform: Whether or not to transform input coordinates from the svg coordinate system to standard cartesian
         system. Depends on canvas_height for calculations.
        :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
        :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
    """
    root = ElementTree.fromstring(svg_string)
    return parse_root(root, canvas_height, transform, draw_hidden)


def parse_file(file_path: str, canvas_height=None, transform=True, draw_hidden=False) -> List[Curve]:
    """
            Recursively parse an svg file into geometric curves. (Wrapper for parse_root)

            :param file_path: The etree element who's children should be recursively parsed. The root will not be drawn.
            :param canvas_height: The height of the canvas. By default the height attribute of the root is used. If the root
            does not contain the height attribute, it must be either manually specified or transform must be False.
            :param transform: Whether or not to transform input coordinates from the svg coordinate system to standard cartesian
             system. Depends on canvas_height for calculations.
            :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
            :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
        """
    root = ElementTree.parse(file_path).getroot()
    return parse_root(root, canvas_height, transform, draw_hidden)
