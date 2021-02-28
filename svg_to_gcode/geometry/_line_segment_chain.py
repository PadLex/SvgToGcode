from svg_to_gcode.geometry import Chain
from svg_to_gcode.geometry import Curve, Line, Vector
from svg_to_gcode import TOLERANCES


class LineSegmentChain(Chain):
    """
    The LineSegmentChain class inherits form the abstract Chain class. It represents a series of continuous straight
    line-segments.

    LineSegmentChains can be instantiated either conventionally or through the static method line_segment_approximation(),
    which approximates any Curve with a series of line-segments contained in a new LineSegmentChain instance.
    """

    def __repr__(self):
        return f"{type(self)}({len(self._curves)} curves: {[line.__repr__() for line in self._curves[:2]]}...)"

    def append(self, line2: Line):
        if self._curves:
            line1 = self._curves[-1]

            # Assert continuity
            if abs(line1.end - line2.start) > TOLERANCES['input']:
                raise ValueError(f"The end of the last line is different from the start of the new line"
                                 f"|{line1.end} - {line2.start}| >= {TOLERANCES['input']}")

            # Join lines
            line2.start = line1.end

        self._curves.append(line2)

    def to_svg_path(self, wrapped=True, transformation=None):
        """
        A handy debugging function which converts the current line-chain to svg form

        :param wrapped: Whether or not to return just d or also wrap it with the full <path></path> element
        :param transformation: A transformation to apply to every line before converting it.
        """

        start = Vector(self._curves[0].start.x, self._curves[0].start.y)
        if transformation:
            start = transformation.apply_transformation(start)

        d = f"M{start.x} {start.y}"

        for line in self._curves:
            end = Vector(line.end.x, line.end.y)
            if transformation:
                end = transformation.apply_transformation(end)
            d += f" L {end.x} {end.y}"

        if not wrapped:
            return d

        style = "fill:none;stroke:black;stroke-width:0.864583px;stroke-linecap:butt;stroke-linejoin:miter;stroke" \
                "-opacity:1 "

        return f"""<path\nd="{d}"\nstyle="{style}"\n/>"""

    @staticmethod
    def line_segment_approximation(shape, increment_growth=3 / 2, error_cap=TOLERANCES['approximation'],
                                   error_floor=1.5 * TOLERANCES['approximation'],
                                   minimize_lines=True) -> "LineSegmentChain":

        lines = LineSegmentChain()

        if isinstance(shape, Line):
            lines.append(shape)
            return lines

        t = 0
        line_start = shape.start
        increment = 0.1

        while t < 1:
            new_t = t + increment

            if new_t > 1:
                new_t = 1

            line_end = shape.point(new_t)
            line = Line(line_start, line_end)

            distance = Curve.max_distance(shape, line, t_range1=(t, new_t))

            # If the error is too high, reduce increment and restart cycle
            if distance > error_cap:
                increment /= increment_growth
                # print(f"error {distance} is too high, lowering increment")
                continue

            # If the error is very low, increase increment but DO NOT restart cycle.
            if distance < error_floor and minimize_lines:
                increment *= increment_growth

            lines.append(line)

            line_start = line_end
            t = new_t

        return lines
