from xml.etree import ElementTree
from typing import List
from copy import deepcopy
import re

from svg_to_gcode.svg_parser import Path, Transformation
from svg_to_gcode.geometry import Curve

NAMESPACES = {'svg': 'http://www.w3.org/2000/svg'}


def _has_style(element: ElementTree.Element, key: str, value: str) -> bool:
    """
    Check if an element contains a specific key and value either as an independent attribute or in the style attribute.
    """
    return element.get(key) == value or (element.get("style") and f"{key}:{value}" in element.get("style"))

def _parse_length(length: str):
    """
    Take a string that contains a CSS length value and return it in mm
    :param length: string containing a width or height attribute from an SVG
    :return: the length in mm, or None if the string doesn't contain a length
    """
    # The lengths can be just a number (if so we assume mm), or a number and
    # a unit: mm, in, cm, pt, px, pc
    # See https://www.w3.org/TR/CSS21/syndata.html#value-def-length for the details
    ret = None
    m = re.search('(\d+)[\.]*(\d*)(\w*)', length)
    if m is not None:
        # The various parts of m will give us the sections of the length
        # Get the numeric part.  We reassemble this so that we don't accidentally
        # try to convert strings with multiple "."s
        num = float(m[1]+"."+m[2])
        # We've got a physical unit, so we might need to scale things
        if m[3] == "mm":
            mult = 1
        elif m[3] == "cm":
            mult = 10
        elif m[3] == "in":
            mult = 25.4
        elif m[3] == "pt":
            mult = 25.4/72
        elif m[3] == "pc":
            mult = 12*25.4/72
        elif m[3] == "px":
            mult = 0.75*25.4/72
        else:
            # Default to mm
            mult = 1
        ret = num*mult
    return ret

# Todo deal with viewBoxes
def parse_root(root: ElementTree.Element, transform_origin=True, canvas_height=None, draw_hidden=False,
               visible_root=True, root_transformation=None) -> List[Curve]:

    """
    Recursively parse an etree root's children into geometric curves.

    :param root: The etree element who's children should be recursively parsed. The root will not be drawn.
    :param canvas_height: The height of the canvas. By default the height attribute of the root is used. If the root
    does not contain the height attribute, it must be either manually specified or transform must be False.
    :param transform_origin: Whether or not to transform input coordinates from the svg coordinate system to standard
    cartesian system. Depends on canvas_height for calculations.
    :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
    :param visible_root: Specifies whether or the root is visible. (Inheritance can be overridden)
    :param root_transformation: Specifies whether the root's transformation. (Transformations are inheritable)
    :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
    """

    if canvas_height is None:
        height_str = root.get("height")
        viewBox_str = root.get("viewBox")
        if height_str is None and viewBox_str:
            # "viewBox" attribute: <min-x, min-y, width, height>
            height_str = viewBox_str.split()[3]
        canvas_height = _parse_length(height_str)

    if root.get("viewBox") is not None:
        #print("We have a viewBox of >>%s<<" % (root.get("viewBox")))
        # Calulate the transform, as described in https://www.w3.org/TR/SVG/coords.html#ComputingAViewportsTransform
        # TODO Build a more resilient parser here
        p = re.compile("([\d\.]+),?\s+([\d\.]+),?\s+([\d\.]+),?\s+([\d\.]+)")
        if p.search(root.get("viewBox")):
            parts = p.search(root.get("viewBox"))
            # TODO Can these values be anything other than numbers?  "123mm" maybe?
            #      The spec says they're "number"s, so no units, but possibly + or - or e-notation
            vb_x = float(parts[1])
            vb_y = float(parts[2])
            vb_width = float(parts[3])
            vb_height = float(parts[4])
            # TODO handle the preserveAspectRatio attribute
            # Defaults if not otherwise specified
            align = "xMidYMid"
            meet_or_slice = "meet"

            e_x = 0.0
            e_y = 0.0
            width_str = root.get("width")
            e_width = _parse_length(width_str)
            e_height = canvas_height
            scale_x = e_width/vb_width
            scale_y = e_height/vb_height
            #print("vb_x: %f, vb_y: %f, vb_width: %f, vb_height: %f" % (vb_x, vb_y, vb_width, vb_height))
            #print("e_x: %f, e_y: %f, e_width: %f, e_height: %f, scale_x: %f, scale_y: %f" % (e_x, e_y, e_width, e_height, scale_x, scale_y))
            if align != "none" and meet_or_slice == "meet":
                if scale_x > scale_y:
                    scale_x = scale_y
                else:
                    scale_y = scale_x
            if align != "none" and meet_or_slice == "slice":
                if scale_x < scale_y:
                    scale_x = scale_y
                else:
                    scale_y = scale_x
            translate_x = e_x - (vb_x * scale_x)
            translate_y = e_y - (vb_y * scale_y)
            # Now apply the viewBox transformations
            root_transformation = root_transformation if root_transformation else Transformation()
            if translate_x != 0 or translate_y != 0:
                root_transformation.add_translation(translate_x, translate_y)
            if scale_x != 1.0 or scale_y != 1.0:
                root_transformation.add_scale(scale_x, scale_y)

    curves = []

    # Draw visible elements (Depth-first search)
    for element in list(root):

        # display cannot be overridden by inheritance. Just skip the element
        display = _has_style(element, "display", "none")

        if display or element.tag == "{%s}defs" % NAMESPACES["svg"]:
            continue

        transformation = deepcopy(root_transformation) if root_transformation else None

        transform = element.get('transform')
        if transform:
            transformation = Transformation() if transformation is None else transformation
            transformation.add_transform(transform)

        # Is the element and it's root not hidden?
        visible = visible_root and not (_has_style(element, "visibility", "hidden")
                                        or _has_style(element, "visibility", "collapse"))
        # Override inherited visibility
        visible = visible or (_has_style(element, "visibility", "visible"))

        # If the current element is opaque and visible, draw it
        if draw_hidden or visible:
            if element.tag == "{%s}path" % NAMESPACES["svg"]:
                path = Path(element.attrib['d'], canvas_height, transform_origin, transformation)
                curves.extend(path.curves)

        # Continue the recursion
        curves.extend(parse_root(element, transform_origin, canvas_height, draw_hidden, visible, transformation))

    # ToDo implement shapes class
    return curves


def parse_string(svg_string: str, transform_origin=True, canvas_height=None, draw_hidden=False) -> List[Curve]:
    """
        Recursively parse an svg string into geometric curves. (Wrapper for parse_root)

        :param svg_string: The etree element who's children should be recursively parsed. The root will not be drawn.
        :param canvas_height: The height of the canvas. By default the height attribute of the root is used. If the root
        does not contain the height attribute, it must be either manually specified or transform_origin must be False.
        :param transform_origin: Whether or not to transform input coordinates from the svg coordinate system to standard cartesian
         system. Depends on canvas_height for calculations.
        :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
        :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
    """
    root = ElementTree.fromstring(svg_string)
    return parse_root(root, transform_origin, canvas_height, draw_hidden)


def parse_file(file_path: str, transform_origin=True, canvas_height=None, draw_hidden=False) -> List[Curve]:
    """
            Recursively parse an svg file into geometric curves. (Wrapper for parse_root)

            :param file_path: The etree element who's children should be recursively parsed. The root will not be drawn.
            :param canvas_height: The height of the canvas. By default the height attribute of the root is used. If the root
            does not contain the height attribute, it must be either manually specified or transform_origin must be False.
            :param transform_origin: Whether or not to transform input coordinates from the svg coordinate system to standard cartesian
             system. Depends on canvas_height for calculations.
            :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
            :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
        """
    root = ElementTree.parse(file_path).getroot()
    return parse_root(root, transform_origin, canvas_height, draw_hidden)
