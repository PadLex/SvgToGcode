import re

from xml.etree import ElementTree
from typing import List
from copy import deepcopy

from svg_to_gcode.svg_parser import Path, Transformation
from svg_to_gcode.geometry import Curve, RasterImage


NAMESPACES = {'svg': 'http://www.w3.org/2000/svg',
              'xlink':'http://www.w3.org/1999/xlink'}


def _has_style(element: ElementTree.Element, key: str, value: str) -> bool:
    """
    Check if an element contains a specific key and value either as an independent attribute or in the style attribute.
    """
    return element.get(key) == value or (element.get("style") and f"{key}:{value}" in element.get("style"))


def add_viewbox_transformation(transformation: Transformation, transform_origin, vwbox):
    """
    Transform SVG coordinate system to a math-cartesion coordinate system and correct its origin.
    When viewBox is missing the 'height' value of the viewport is used.
    """

    # update transformation
    up_transformation = Transformation()

    # 'svg tag' examples:
    #   <svg width="452mm" height="280mm" viewBox="0 -280 452 280" xmlns="http://www.w3.org/2000/svg" version="1.1">
    #        ----------------------------
    #        viewport: -^ --------^
    #   <svg width="793.70081" height="1122.5197" viewBox="0 0 210 296.99999" ... >
    #        ------------------------------------
    #        viewport: --^ ---------------^

    # Note on 'user-units':
    #   - viewBox values are in 'user-units'
    #   - drawings, like the ones described by 'svg path', are done in user space (coordinates are in user-units).
    #   - viewport values are not necessarily in user-units, but have a fixed mapping to user-units
    #   - Inkscape defaults to 'user-unit' in mm: 1 user-unit is 1 mm).

    # Considering the above, a sensible approach is to use a 1 on 1 mapping of svg (user space) coordinates to gcode (coordinates).
    # After all gcode coordinates are also unit less (it depends on the drawing mode if a unit is 'mm' or 'in'ch)
    # As a consequence, only viewBox values have to be taken into account.

    if transform_origin:
        # viewBox "x" and "y" represent the upper left corner of the document.
        # when non zero, the upper left corner should be corrected to (0,0)
        # (a laser or CNC machine has a positive workarea only, which should be as large as possible)
        if vwbox["x"] or vwbox["y"]:
            up_transformation.add_translation(-vwbox["x"],-vwbox["y"])

        # viewBox "width" and "height" represent the dimensions of the 'svg'
        # (a rectangle - left upper at (vwbox['x'],vwbox['y']) - in user space)

        # Note: If A and B are the matrices of two linear transformations, then the effect of first applying A and then B
        # to a column vector x is given by B(Ax) == (BA)x
        # So, in the below case, transformation order is 'scale' first and 'translation' second.
        up_transformation.add_translation(0, vwbox["height"])       # Translation
        up_transformation.add_scale(1, -1)                          # T * Scale
        # applying it to a vector:                                  # T * S * Vector(x,y)

    if transformation is not None:
        up_transformation.extend(transformation)

    return up_transformation

def get_viewBox(root: ElementTree.Element) -> {}:
    """
    Get viewBox info.
    """

    vwbox = {}
    root_vwbox = root.get('viewBox')

    if root_vwbox:
        # viewBox info in user-units (Inkscape defaults to 'user-unit' in mm: 1 user-unit is 1 mm).
        vwbox["x"], vwbox["y"], vwbox["width"], vwbox["height"] = re.findall("[0-9]+\.?[0-9]*", root_vwbox)

        # viewBox "x" and "y" represent the upper left corner of the document.
        # when non zero, the upper left corner of the canvas should be corrected to (0,0)
        # (a laser or CNC machine has a positive workarea only, which should be as large as possible)

        # not that viewBox parameters should not have unit letters (they are 'in' user-units)
        vwbox["x"] = float(vwbox["x"])
        vwbox["y"] = float(vwbox["y"])

        # viewBox "width" and "height" represent the dimensions of the 'svg'
        # (a rectangle - left upper at (vwbox['x'],vwbox['y']) - in user space)
        vwbox["width"] = float(vwbox["width"])
        vwbox["height"] = float(vwbox["height"])

    return vwbox


def parse_root(root: ElementTree.Element, transform_origin=True, viewbox=None, draw_hidden=False,
               visible_root=True, root_transformation=None) -> List[Curve]:

    """
    Recursively parse an etree root's children into geometric curves.

    :param root: The etree element who's children should be recursively parsed. The root will not be drawn.
    :param viewbox: ViewBox of the SVG, used to transform it to a math-cartesion coordinate system and
    correct its origin. When the viewBox is missing the viewport (of the root) is used. If the root
    does not contain a viewBox or viewport, it must be either manually specified or transform must be False.
    :param transform_origin: Whether or not to transform input coordinates from the svg coordinate system to standard
    cartesian system. Depends on viewBox height for calculations.
    :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
    :param visible_root: Specifies whether or the root is visible. (Inheritance can be overridden)
    :param root_transformation: Specifies whether the root's transformation. (Transformations are inheritable)
    :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
    """

    if viewbox is None:
        # get viewbox (if any)
        viewbox = get_viewBox(root)

        if not viewbox:
            # get viewport (as a fallback)

            viewbox = { 'x':0.0, 'y':0.0, 'width':0.0, 'height':0.0 }
            width_str = root.get("width")
            viewbox["width"] = float(width_str) if width_str.isnumeric() else float(width_str[:-2])
            height_str = root.get("height")
            viewbox["height"] = float(height_str) if height_str.isnumeric() else float(height_str[:-2])

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
                path = Path(element.attrib['d'],
                               add_viewbox_transformation(transformation, transform_origin, viewbox))
                curves.extend(path.curves)
            else:
                if element.tag == "{%s}image" % NAMESPACES["svg"]:
                    # svg image

                    # instantiate curve (image)
                    ri = RasterImage(element.attrib, element.attrib["{%s}href" % NAMESPACES["xlink"]],
                                add_viewbox_transformation(transformation, transform_origin, viewbox))
                    curves.append(ri)

        # Continue the recursion
        curves.extend(parse_root(element, transform_origin, viewbox, draw_hidden, visible, transformation))

    # ToDo implement shapes class
    return curves


def parse_string(svg_string: str, transform_origin=True, viewbox=None, draw_hidden=False) -> List[Curve]:
    """
        Recursively parse an svg string into geometric curves. (Wrapper for parse_root)

        :param svg_string: The etree element who's children should be recursively parsed. The root will not be drawn.
        :param viewbox: ViewBox of the SVG, used to transform it to a math-cartesion coordinate system and
        correct its origin. When the viewBox is missing the viewport (of the root) is used. If the root
        does not contain a viewBox or viewport, it must be either manually specified or transform must be False.
        :param transform_origin: Whether or not to transform input coordinates from the svg coordinate system to standard cartesian
         system. Depends on canvas_height for calculations.
        :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
        :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
    """
    root = ElementTree.fromstring(svg_string)
    return parse_root(root, transform_origin, viewbox, draw_hidden)


def parse_file(file_path: str, transform_origin=True, viewbox=None, draw_hidden=False) -> List[Curve]:
    """
            Recursively parse an svg file into geometric curves. (Wrapper for parse_root)

            :param file_path: The etree element who's children should be recursively parsed. The root will not be drawn.
            :param viewbox: ViewBox of the SVG, used to transform it to a math-cartesion coordinate system and
            correct its origin. When the viewBox is missing the viewport (of the root) is used. If the root
            does not contain a viewBox or viewport, it must be either manually specified or transform must be False.
            :param transform_origin: Whether or not to transform input coordinates from the svg coordinate system to standard cartesian
             system. Depends on canvas_height for calculations.
            :param draw_hidden: Whether or not to draw hidden elements based on their display, visibility and opacity attributes.
            :return: A list of geometric curves describing the svg. Use the Compiler sub-module to compile them to gcode.
        """
    root = ElementTree.parse(file_path).getroot()
    return parse_root(root, transform_origin, viewbox, draw_hidden)
