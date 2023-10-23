import warnings
import math
import copy

from io import BytesIO
from typing import Any
from importlib.metadata import version

import base64
import numpy as np

from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Curve
from svg_to_gcode.geometry import LineSegmentChain, Vector, RasterImage
from svg_to_gcode import DEFAULT_SETTING
from svg_to_gcode import TOLERANCES, SETTING, check_setting

from PIL import Image

class Compiler:
    """
    The Compiler class handles the process of drawing geometric objects using interface commands and assembling the
    resulting numerical control code.
    """

    def __init__(self, interface_class: Interface, custom_header: list[str] =None, custom_footer: list[str] =None,
                 params: dict[str, Any] = None):
        """

        :param interface_class: Specify which interface to use. The most common is the gcode interface.
        :param custom_header: A list of commands to be executed before all generated commands.
        :param custom_footer: A list of commands to be executed after all generated commands.
                              Default [laser_off, program_end]
	:param settings: dictionary to specify "unit", "pass_depth", "dwell_time", "movement_speed", etc.
        """
        self._boundingbox = None
        self.interface = interface_class()

        # Round outputs to the same number of significant figures as the operational tolerance.
        self.precision = abs(round(math.log(TOLERANCES["operation"], 10)))

        if params is None or not check_setting(params):
            raise ValueError(f"Please set at least 'maximum_laser_power' and 'movement_speed' from {SETTING}")

	# get default settings and update
        self.settings = copy.deepcopy(DEFAULT_SETTING)
        for key in params.keys():
            self.settings[key] = params[key]

        self.interface.set_machine_parameters(self.settings)

        if custom_header is None:
            custom_header = []

        if custom_footer is None:
            custom_footer = [self.interface.laser_off(), self.interface.program_end()]

        self.header = [self.interface.code_initialize(),
                       self.interface.set_unit(self.settings["unit"]),
                       self.interface.set_distance_mode(self.settings["distance_mode"])] + custom_header
        self.footer = custom_footer

        # path object gcode
        self.body: list[str] = []
        # image gcode
        self.gcode: list[str] = []


    def compile(self, passes=1):

        """
        Assembles the code in the header, body and footer.

        :param passes: the number of passes that should be made. Every pass the machine moves_down (z-axis) by
        self.pass_depth and self.body is repeated.
        :return returns the assembled code. self.header + [self.body, -self.pass_depth] * passes + self.footer
        """

        if len(self.body) == 0:
            warnings.warn("Compile with an empty body (no curves).")

	# add generator info and boundingbox for this code
        gcode = [f"; SvgToGcode v{version('svg_to_gcode')}", f"; GRBL 1.1, unit={self.settings['unit']}, {self.settings['distance_mode']} coordinates"]

        if self._boundingbox:
            gcode += [ f"; Boundingbox: (X{self._boundingbox[0].x:.{0 if self._boundingbox[0].x.is_integer() else self.precision}f},"
                       f"Y{self._boundingbox[0].y:.{0 if self._boundingbox[0].y.is_integer() else self.precision}f}) to "
                       f"(X{self._boundingbox[1].x:.{0 if self._boundingbox[1].x.is_integer() else self.precision}f},"
                       f"Y{self._boundingbox[1].y:.{0 if self._boundingbox[1].y.is_integer() else self.precision}f})"]

            if not self.check_bounds():
                if self.settings["distance_mode"] == "absolute" and self.check_axis_maximum_travel():
                    warnings.warn("Cut is not within machine bounds.")
                    gcode += ["; WARNING: Cut is not within machine bounds of "
                              f"X[0,{self.settings['x_axis_maximum_travel']}], Y[0,{self.settings['y_axis_maximum_travel']}]"]
                elif not self.check_axis_maximum_travel():
                    # warnings.warn("Please define machine cutting area, set parameter: 'x_axis_maximum_travel' and 'y_axis_maximum_travel'")
                    gcode += ["; WARNING: Please define machine cutting area, set parameter: 'x_axis_maximum_travel' and 'y_axis_maximum_travel'"]
                else:
                    gcode += [f"; WARNING: distance mode is not absolute: {self.settings['distance_mode']}"]

        gcode.extend(self.header)
        for i in range(passes):
            gcode += [f"; pass #{i+1}"]
            gcode.extend(self.body)

            if i < (passes - 1) and self.settings["pass_depth"] > 0:
                # If it isn't the last pass, turn off the laser and move down
                gcode.append(self.interface.laser_off())
                gcode.append(self.interface.set_relative_coordinates())
                gcode.append(self.interface.linear_move(z=-self.settings["pass_depth"]))
                gcode.append(self.interface.set_distance_mode(self.settings["distance_mode"]))

        gcode.extend(self.footer)

        gcode = filter(lambda command: len(command) > 0, gcode)

        return '\n'.join(gcode)

    def compile_images(self):

        """
        Assembles the code in the header, body and footer.
        """

        if len(self.gcode) == 0:
            warnings.warn("Compile with no images.")
            return ''

        header_gc = ["M5","M8", "M4"]
        # laser off, fan off, program stop
        footer_gc = ["M5","M9","M2"]

        return '\n'.join(header_gc + self.gcode + footer_gc)

    def compile_to_file(self, file_name: str, curves: list[Curve], passes=1):
        """
        A wrapper for the self.compile method. Assembles the code in the header, body and footer, saving it to a file.

        :param file_name: the path to save the file.
        :param curves: SVG curves approximated by line segments.
        :param passes: the number of passes that should be made. Every pass the machine moves_down (z-axis) by
        self.pass_depth and self.body is repeated.
        """
	# set laser_power, cutting speed
        self.append_curves(curves)
        # write path objects
        with open(file_name, 'w') as file:
            file.write(self.compile(passes=passes))

        images_gcode = self.compile_images()
        if images_gcode:
            # write image objects
            with open(file_name.rsplit('.',1)[0] + "_images." + file_name.rsplit('.',1)[1], 'w') as file:
                file.write(images_gcode)

    def append_line_chain(self, line_chain: LineSegmentChain):
        """
        Draws a LineSegmentChain by calling interface.linear_move() for each segment. The resulting code is appended to
        self.body
        """

        if line_chain.chain_size() == 0:
            warnings.warn("Attempted to parse empty LineChain")
            return

        code = []
        start = line_chain.get(0).start

	# Move to the next line_chain when the next line segment doesn't connect to the end of the previous one.
        if self.interface.position is None or abs(self.interface.position - start) > TOLERANCES["operation"]:
            if self.interface.position is None or self.settings["rapid_move"]:
                # move to the next line_chain: set laser off, rapid move to start of chain,
                # set movement (cutting) speed, set laser mode and power on
                code = [self.interface.laser_off(), self.interface.rapid_move(start.x, start.y),
                        self.interface.set_movement_speed(self.settings["movement_speed"]),
                        self.interface.set_laser_mode(self.settings["laser_mode"]), self.interface.set_laser_power(self.settings["laser_power"])]

                self._boundingbox = [copy.deepcopy(start), copy.deepcopy(start)] if self._boundingbox is None else self._boundingbox
            else:
                # move to the next line_chain: set laser mode, set laser power to 0 (cutting is off),
                # set movement speed, (no rapid) move to start of chain, set laser to power
                code = [self.interface.set_laser_mode(self.settings["laser_mode"]), self.interface.set_laser_power(0),
                        self.interface.set_movement_speed(self.settings["movement_speed"]), self.interface.linear_move(start.x, start.y),
                        self.interface.set_laser_power(self.settings["laser_power"])]

            if self.settings["dwell_time"] > 0:
                code = [self.interface.dwell(self.settings["dwell_time"])] + code

        for line in line_chain:
            code.append(self.interface.linear_move(line.end.x, line.end.y))
            if self._boundingbox is not None:
                self._boundingbox[0].x = line.end.x if line.end.x < self._boundingbox[0].x else self._boundingbox[0].x
                self._boundingbox[0].y = line.end.y if line.end.y < self._boundingbox[0].y else self._boundingbox[0].y
                self._boundingbox[1].x = line.end.x if line.end.x > self._boundingbox[1].x else self._boundingbox[1].x
                self._boundingbox[1].y = line.end.y if line.end.y > self._boundingbox[1].y else self._boundingbox[1].y

        self.body.extend(code)

    def decode_base64(self, base64_string):

        # decode from utf-8 when needed
        if isinstance(base64_string, bytes):
            base64_string = base64_string.decode("utf-8")

        # remove MIME part
        base64_string = base64_string.partition(",")[2]

        # convert to right form
        imgdata = base64.b64decode(base64_string)

        # open as binary file
        img_file = BytesIO(imgdata)

        return Image.open(img_file)

    # convert a MIME base64 image image string
    def convert_image(self, image:str, img_attrib: dict[str, Any]):

        # get svg image attributes info or default
        pixelsize = img_attrib['gcode_pixelsize'] if 'gcode_pixelsize' in img_attrib else 0.1

        # convert image from base64 string
        img = self.decode_base64(image)
        #img.show()

        # convert image to new size
        img = img.resize((int(float(img_attrib['width']) * 1/float(pixelsize)), int(float(img_attrib['height']) * 1/float(pixelsize))), Image.Resampling.LANCZOS)

        # convert to B&W without alpha
        #img = img.convert("LA")
        img = img.convert("L")
        if self.settings['showimage']:
            img.show()

        # convert to nparray for fast handling
        return np.array(img)

    def image2gcode(self, img_attrib: dict[str, Any], img=None, transformation = None):

        invert_intensity = True

        # get svg image attribute/object info (set in Inkscape for example) when available
        # else set tool invocation values
        pixelsize = img_attrib['gcode_pixelsize'] if 'gcode_pixelsize' in img_attrib else self.settings["pixel_size"]
        maxpower = img_attrib['gcode_maxpower'] if 'gcode_maxpower' in img_attrib else self.settings["maximum_image_laser_power"]
        speed = img_attrib['gcode_speed'] if 'gcode_speed' in img_attrib else self.settings["image_movement_speed"]

        # set header for this image
        self.gcode += [f"; image name: {img_attrib['id']}, pixelsize: {pixelsize}, speed: {speed}, maxpower: {maxpower}\n;"]

        # set X/Y-axis precision to number of digits after the decimal separator
        XY_prec = len(str(pixelsize).split('.')[1])

        # start position
        X = round(float(img_attrib['x']), XY_prec)
        Y = round(float(img_attrib['y']), XY_prec)

        # go to start
        if transformation is not None:
            XYt = transformation.apply_affine_transformation(Vector(X, Y))
            self.gcode += [f"G0X{round(XYt[0],XY_prec)}Y{round(XYt[1],XY_prec)}"]
        else:
            self.gcode += [f"G0X{X}Y{Y}"]

        # set write speed and G1 move mode
        # (note that this stays into effect until another G code is executed,
        # so we do not have to repeat this for all coordinates emitted below)
        self.gcode += [f"G1F{speed}"]

        # Print left to right, right to left (etc.)
        # Optimized gcode:
        # - draw pixels until change of power
        # - emit X/Y coordinates only when they change
        # - emit linear move 'G1' code only once
        # - does not emit in between spaces
        #
        left2right = True

        # start print
        for line in img:

            if not left2right:
                # reverse line when printing right to left
                line = np.flip(line)

            # add line terminator (makes this algorithm regular)
            line = np.append(line,0)

            # Note that (laser) drawing from a point to a point differs from setting a point (within an image):
            #              0   1   2   3   4   5   6     <-- gcode drawing points
            # one line:    |[0]|[1]|[2]|[3]|[4]|[5]|     <-- image pixels
            #
            # For example: drawing from X0 to X2 with value S10 corresponds to setting [0] = S10 and [1] = S10
            # Note also that drawing form left to right differs subtly from the reverse

            # draw this pixel line
            #for count, bw in np.ndenumerate(line):
            for count, pixel in enumerate(line):
                # power proportional to maximum laser power
                laserpow = round((1.0 - float(pixel/255)) * maxpower) if invert_intensity else round(float(pixel/255) * maxpower)
                # delay emit first pixel (so all same power pixels can be emitted in one sweep)
                if count == 0:
                    prev_pow = laserpow

                # draw points until change of power
                if laserpow != prev_pow or count == line.size-1:
                    if transformation is not None:
                        XYt = transformation.apply_affine_transformation(Vector(X, Y))
                        code = f"X{round(XYt[0],XY_prec)}Y{round(XYt[1],XY_prec)}"
                        code += f"S{prev_pow}"
                    else:
                        code = f"X{X}"
                        code += f"S{prev_pow}"
                    self.gcode += [code]

                    if count == line.size-1:
                        continue
                    # if laserpow != prev_pow
                    prev_pow = laserpow

                # next point
                X = round(X + (pixelsize if left2right else -pixelsize), XY_prec)

            # go to next scan line
            Y = round(Y + pixelsize, XY_prec)
            if transformation is not None:
                XYt = transformation.apply_affine_transformation(Vector(X, Y))
                self.gcode += [f"X{round(XYt[0],XY_prec)}Y{round(XYt[1],XY_prec)}S0"]
            else:
                self.gcode += [f"Y{Y}S0"]

            # change print direction
            left2right = not left2right

    def append_curves(self, curves: list[Curve]):
        """
        Draws curves.
        """
        for curve in curves:
            if isinstance(curve, RasterImage):
                # curve is 'image', draw it

                # convert image (scale and type)
                img = self.convert_image(curve.image, curve.img_attrib)

                # Draw image by converting raster image scan lines to gcode, possibly applying tranformations on each pixel
                self.image2gcode(curve.img_attrib, img, curve.transformation)
            else:
                # curve is 'path', draw it
                # Draws curves by approximating them as line segments and calling self.append_line_chain().
                # The resulting code is appended to self.body
                line_chain = LineSegmentChain()
                approximation = LineSegmentChain.line_segment_approximation(curve)
                line_chain.extend(approximation)
                self.append_line_chain(line_chain)

    def check_axis_maximum_travel(self):
        return self.settings["x_axis_maximum_travel"] is not None and self.settings["y_axis_maximum_travel"] is not None
        # warnings.warn("Please define machine cutting area, set parameter: 'x_axis_maximum_travel' and 'y_axis_maximum_travel'")

    def check_bounds(self):
        """
        Check if line segments are within the machine cutting area. Note that machine coordinate mode must
        be absolute and machine parameters 'x_axis_maximum_travel' and 'y_axis_maximum_travel' are set
        :return true when box is in machine area bounds, false otherwise
        """

        if self.settings["distance_mode"] == "absolute" and self.check_axis_maximum_travel():
            machine_max = Vector(self.settings["x_axis_maximum_travel"],self.settings["y_axis_maximum_travel"])
            return (self._boundingbox[0].x >= 0 and self._boundingbox[0].y >=0
                    and self._boundingbox[1].x * (25.4 if self.settings["unit"] == "inch" else 1) <= machine_max.x
                    and self._boundingbox[1].y * (25.4 if self.settings["unit"] == "inch" else 1) <= machine_max.y)

        return False
