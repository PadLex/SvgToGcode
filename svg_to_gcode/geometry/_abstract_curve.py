from svg_to_gcode import formulas
from svg_to_gcode.geometry import Vector


class Curve:
    """
    The Curve abstract class is the cornerstone of the geometry sub-module. Child classes inherit from it to represent
    different types of curves.

    :param self.start: the first point of the curve
    :type self.start: Vector

    :param self.end: the last point of the curve
    :type self.end: Vector
    """

    __slots__ = 'start', 'end'

    def point(self, t: float) -> Vector:
        """
        The point method returns a point along the curve.

        :param t: t is a number between 0 and 1.
        :return: the point at distance t*self.length from self.start. For t=0.5, the point half-way across the curve
        would be returned.
        """
        raise NotImplementedError("point(self, t) must be implemented")

    def derivative(self, t):
        """
        The derivative method returns a derivative at a point along the curve.

        :param t: t is a number between 0 and 1.
        :return: the derivative at self.point(t)
        """
        raise NotImplementedError("derivative(self, t) must be implemented")

    def sanity_check(self):
        """Verify if that the curve is valid."""
        raise NotImplementedError("sanity_check(self) must be implemented")

    # A custom print representation is trivial to implement and useful for debugging
    def __repr__(self):
        raise NotImplementedError("__repr__(self) must be implemented")

    @staticmethod
    def max_distance(curve1: "Curve", curve2: "Curve", t_range1=(0, 1), t_range2=(0, 1), samples=9):

        """
        Return the approximate maximum distance between two Curves for different values of t.

        WARNING: should only be used when comparing relatively flat curve segments. If one of the two
        curves has very eccentric humps, the tip of the hump may not be sampled.

        :param curve1: the first of two curves to be compared.
        :param curve2: the second of two curves to be compared.
        :param t_range1: (min_t, max_t) the range of t values which should be sampled in the first curve. The default
        value of (0, 1) samples the whole curve. A value of (0, 5) would only sample from the first half of the curve.
        :param t_range2: (min_t, max_t) the range of t values which should be sampled in the second curve. The default
        value of (0, 1) samples the whole curve. A value of (0, 5) would only sample from the first half of the curve.
        :param samples: the number of samples which should be taken. Higher values are slower but more accurate.
        :return: the approximate maximum distance
        """

        maximum_distance = 0
        for i in range(samples):
            t = (i + 1) / (samples + 1)
            t1 = formulas.linear_map(t_range1[0], t_range1[1], t)
            t2 = formulas.linear_map(t_range2[0], t_range2[1], t)

            distance = abs(curve1.point(t1) - curve2.point(t2))
            maximum_distance = distance if distance > maximum_distance else maximum_distance

        return maximum_distance
