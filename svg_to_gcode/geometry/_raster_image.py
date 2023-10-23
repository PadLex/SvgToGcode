from svg_to_gcode.geometry import Vector
from svg_to_gcode.geometry import Curve
from svg_to_gcode import formulas

# a raster image (svg image tag)
class RasterImage(Curve):
    """The Line class inherits from the abstract Curve class and describes a straight line segment."""

    __slots__ = 'image', 'img_attrib', 'transformation'

    #def __init__(self, start: (float,float), pixel_size, speed, max_power, img, transformation):
    def __init__(self, img_attrib, image, transformation):
        self.image = image
        self.img_attrib = img_attrib
        self.transformation = transformation

    def __repr__(self):
        return f"RasterImage(img_attributes:{self.img_attributes}, transformation:{self.transformation})"

    def length(self):
        warnings.warn("not applicable to 2-dimensional object")
        return 0

    def point(self, t):
        warnings.warn("not applicable to 2-dimensional object")
        return Vector(0, 0)

    def derivative(self, t):
        warnings.warn("not applicable to 2-dimensional object")
        return 0
