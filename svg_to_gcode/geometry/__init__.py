"""
The geometry sub-module offers a geometric representation of curves.

specific maintenance notes:
    - Explicit variable declaration for geometric objects. ** You can't dynamically declare instance variables. **
     Refer to the docs for more info https://docs.python.org/3/reference/datamodel.html?highlight=__slots__#slots
    - The origin is at the bottom-left. As such, all svg_curves must be transformed from the top-left coordinate system
     before generating geometric objects.
"""

from svg_to_gcode.geometry._vector import Vector
from svg_to_gcode.geometry._matrix import Matrix, IdentityMatrix, RotationMatrix

from svg_to_gcode.geometry._abstract_curve import Curve
from svg_to_gcode.geometry._line import Line
from svg_to_gcode.geometry._circular_arc import CircularArc
from svg_to_gcode.geometry._elliptical_arc import EllipticalArc
from svg_to_gcode.geometry._quadratic_bazier import QuadraticBezier
from svg_to_gcode.geometry._cubic_bazier import CubicBazier

from svg_to_gcode.geometry._abstract_chain import Chain
from svg_to_gcode.geometry._line_segment_chain import LineSegmentChain
from svg_to_gcode.geometry._smooth_arc_chain import SmoothArcChain
