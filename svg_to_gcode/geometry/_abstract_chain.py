from collections.abc import Iterable

from svg_to_gcode.geometry import Curve
from svg_to_gcode import formulas


class Chain(Curve):
    """
    The Chain class is used to store a sequence of consecutive curves. When considered as a whole, Chains can also be
    viewed as a single, continuous curve. They inherit from the Curve class and are equipped with the subsequent point()
    and derivative() methods.
    """

    __slots__ = '_curves'

    def __init__(self, curves=None):
        self._curves = []

        if curves is not None:
            self.extend(curves)

    def __iter__(self):
        yield from self._curves

    def length(self):
        """
        Return the geometric length of the chain.
        The __len__ magic method wasn't overridden to avoid ambiguity between total length and chain size.
        """
        return sum([curve.length() for curve in self._curves])

    def chain_size(self):
        """
        Return the number of curves in the chain.
        The __len__ magic method wasn't overridden to avoid ambiguity between total length and chain size.
        """
        return len(self._curves)

    def get(self, index: int) -> Curve:
        """Return a curve at a given index"""
        return self._curves[index]

    def append(self, new_curve: Curve):
        """Append a new curve to the chain"""
        raise NotImplementedError("All chains must implement an append command")

    def extend(self, new_curves: Iterable):
        """Extend the Chain with an iterable"""
        for new_curve in new_curves:
            self.append(new_curve)

    def merge(self, chain: "Chain"):
        """
        Merge the Chain instance with another Chain.
        Equivalent to self.extend() but includes additional checks.
        """
        if not chain._curves:
            return

        if self._curves:
            assert self.append(chain._curves[0])

        self._curves.extend(chain._curves[1:])

    def remove_from_first(self, number_of_curves: int):
        """Remove n curves starting from the first"""
        for i in range(number_of_curves):
            self._curves.pop(0)

    def remove_from_last(self, number_of_curves: int):
        """Remove n curves starting from the last"""
        for i in range(len(self._curves) - 1, number_of_curves + 1, -1):
            self._curves.pop(-1)

    def _get_curve_t(self, t):
        lengths = [curve.length() for curve in self._curves]
        t_position = t * sum(lengths)

        position = 0
        for i, length in enumerate(lengths):
            position += length
            if position > t_position:
                break

        curve_t = formulas.inv_linear_map(position - length, position, t_position)

        return self._curves[i], curve_t

    def point(self, t):
        if self.chain_size() == 0:
            raise ValueError("Chain.point was called before adding any curves to the chain.")

        curve, curve_t = self._get_curve_t(t)
        return curve.point(curve_t)

    def derivative(self, t):
        if self.chain_size() == 0:
            raise ValueError("Chain.derivative was called before adding any curves to the chain.")

        curve, curve_t = self._get_curve_t(t)
        return curve.derivative(curve_t)

    def sanity_check(self):
        pass
