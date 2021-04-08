from xml.etree import ElementTree

from svg_to_gcode.geometry import LineSegmentChain, Vector


svg_namespace = 'http://www.w3.org/2000/svg'


def to_svg_path(line_segment_chain: LineSegmentChain, transformation=None, color="black", opacity="1",
                stroke_width="0.864583px", draw_arrows=False, arrow_id="arrow-346") -> ElementTree.Element:
    """
    A handy debugging function which converts the current line-chain to svg form

    :param line_segment_chain: The LineSegmentChain to the converted.
    :param transformation: A transformation to apply to every line before converting it.
    :param color: The path's color.
    :param opacity: The path's opacity.
    :param stroke_width: The path's stroke width.
    :param draw_arrows: Whether or not to draw arrows at the end of each segment. Requires placing the output of
    arrow_defs() in the document.
    :param arrow_id: The id of the arrow def. default = arrow-346
    """

    start = Vector(line_segment_chain.get(0).start.x, line_segment_chain.get(0).start.y)
    if transformation:
        start = transformation.apply_affine_transformation(start)

    d = f"M{start.x} {start.y}"

    for line in line_segment_chain:
        end = Vector(line.end.x, line.end.y)
        if transformation:
            end = transformation.apply_affine_transformation(end)
        d += f" L {end.x} {end.y}"

    style = f"fill:none;stroke:{color};stroke-opacity:{opacity};stroke-width:{stroke_width};stroke-linecap:butt;stroke-linejoin:miter;"

    path = ElementTree.Element("{%s}path" % svg_namespace)
    path.set("d", d)
    path.set("style", style)
    if draw_arrows:
        path.set("marker-mid", f"url(#{arrow_id})")

    return path


def arrow_defs(arrow_scale=1, arrow_id="arrow-346"):
    defs = ElementTree.Element("{%s}defs" % svg_namespace)

    marker = ElementTree.Element("{%s}marker" % svg_namespace)
    marker.set("id", arrow_id)
    marker.set("viewBox", "0 0 10 10")
    marker.set("refX", "5")
    marker.set("refY", "5")
    marker.set("markerWidth", str(arrow_scale))
    marker.set("markerHeight", str(arrow_scale))
    marker.set("orient", "auto-start-reverse")
    defs.append(marker)

    arrow = ElementTree.Element("{%s}path" % svg_namespace)
    arrow.set("d", "M 5 0 l 10 5 l -10 5 z")
    arrow.set("fill", "yellow")
    arrow.set("stroke", "black")
    arrow.set("stroke-width", "0.1")
    marker.append(arrow)
    
    return defs
