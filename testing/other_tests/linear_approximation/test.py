from xml.etree.ElementTree import Element, ElementTree

from svg_to_gcode.svg_parser import parse_file, Transformation, debug_methods
from svg_to_gcode.geometry import LineSegmentChain

from svg_to_gcode.svg_parser._parser_methods import _parse_length
import re

from svg_to_gcode import TOLERANCES

name_space = 'http://www.w3.org/2000/svg'

TOLERANCES['approximation'] = 0.1


def run_test(svg_file_name, debug_file_name):
    curves = parse_file(svg_file_name)

    success = True
    approximations = []
    count = 0
    for curve in curves:
        approximation = LineSegmentChain.line_segment_approximation(curve)
        approximations.append(approximation)
        count += approximation.chain_size()

    generate_debug(approximations, svg_file_name, debug_file_name)

    return success


def generate_debug(approximations, svg_file_name, debug_file_name):
    tree = ElementTree()
    tree.parse(svg_file_name)

    root = tree.getroot()

    height_str = root.get("height")
    (canvas_height_raw, scale_factor) = _parse_length(height_str)
    canvas_height = canvas_height_raw * scale_factor

    for path in root.iter("{%s}path" % name_space):
        path.set("fill", "none")
        path.set("stroke", "black")
        path.set("stroke-width", f"{TOLERANCES['approximation']}mm")

        style = path.get("style")
        if style and "display:none" in style:
            path.set("style", "display:none")
        elif style and ("visibility:hidden" in style or "visibility:collapse" in style):
            path.set("style", "visibility:hidden")
        else:
            path.set("style", "")

    group = Element("{%s}g" % name_space)

    change_origin = Transformation()
    viewbox_str = root.get("viewBox")
    if viewbox_str is None:
        # Inverse scale
        scale = 25.4/96.0
        change_origin.add_scale(1.0/scale, 1.0/scale)
    else:
        # TODO Build a more resilient parser here
        parts = re.search(r'([\d\.\-e]+)[,\s]+([\d\.\-e]+)[,\s]+([\d\.\-e]+)[,\s]+([\d\.\-e]+)', viewbox_str)
        if parts is not None:
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
            (canvas_width_raw,_) = _parse_length(width_str)
            e_width = canvas_width_raw    # use raw number
            e_height = canvas_height_raw  # use raw number

            scale_x = e_width/vb_width
            scale_y = e_height/vb_height
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
            # Inverse scale
            if scale_x != 1.0 or scale_y != 1.0:
                change_origin.add_scale(
                    1.0/scale_factor/scale_x, 1.0/scale_factor/scale_y)
            else:
                change_origin.add_scale(1.0/scale_factor, 1.0/scale_factor)

            # Inverse translation
            translate_x = e_x + (vb_x * scale_x)
            translate_y = e_y + (vb_y * scale_y)
            if translate_x != 0 or translate_y != 0:
                change_origin.add_translation(translate_x, translate_y)
    change_origin.add_scale(1, -1)
    change_origin.add_translation(0, -canvas_height)

    group.append(debug_methods.arrow_defs())
    for approximation in approximations:
        path = debug_methods.to_svg_path(approximation, color="red", stroke_width=f"{TOLERANCES['approximation']/2}mm",
                                         transformation=change_origin, draw_arrows=True)
        group.append(path)

    root.append(group)

    tree.write(debug_file_name)

