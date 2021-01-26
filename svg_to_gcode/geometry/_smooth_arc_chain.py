"""
This is an unfinished class which should not be committed yet.
"""

from svg_to_gcode.geometry import Chain
from svg_to_gcode.geometry import CircularArc
from svg_to_gcode import TOLERANCES, formulas


class SmoothArcChain(Chain):

    def __repr__(self):
        return f"SmoothArcs({[arc.__repr__() for arc in self._curves]})"

    def append(self, arc2: CircularArc):

        if self._curves:
            arc1 = self._curves[-1]

            # Assert continuity
            try:
                assert abs(arc1.end - arc2.start) < TOLERANCES['input']
            except AssertionError:
                raise ValueError(f"The end of the last arc is different from the start of the new arc, "
                                 f"|{arc1.end} - {arc2.start}| >= {TOLERANCES['input']}")

            try:
                assert abs(arc1.derivative(arc1.end) - arc2.derivative(arc2.start)) < TOLERANCES['input']
            except AssertionError:
                raise ValueError(f"The last arc and the new arc form a discontinues curve, "
                                 f"|{arc1.derivative(1)} - {arc2.derivative(0)}| >= {TOLERANCES['input']}")

            # Join arcs
            arc2.start = arc1.end

        self._curves.append(arc2)

    @staticmethod
    def cubic_bazier_to_arcs(bazier, _arcs=None):

        smooth_arcs = _arcs if _arcs else SmoothArcChain()

        start, control1, control2, end = bazier.start, bazier.control1, bazier.control2, bazier.end
        tangent_intersect = formulas.line_intersect(start, control1, end, control2)

        # print("tangent_intersect:", tangent_intersect)

        start_length = abs(start - tangent_intersect)
        end_length = abs(end - tangent_intersect)
        base_length = abs(start - end)

        # print("start_length:", start_length, "end_length:", end_length, "base_length:", base_length)

        incenter_point = (start_length * end + end_length * start + base_length * tangent_intersect) / \
                         (start_length + end_length + base_length)

        # print("incenter:", incenter_point)

        center1 = formulas.tangent_arc_center(control1, start, incenter_point)
        center2 = formulas.tangent_arc_center(control2, end, incenter_point)

        # print("centers:", center1, center2)

        smooth_arcs.append(CircularArc(start, incenter_point, center1))
        smooth_arcs.append(CircularArc(incenter_point, end, center2))

        return smooth_arcs
