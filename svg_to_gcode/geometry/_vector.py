class Vector:
    """The Vector class is a simple representation of a 2D vector."""

    __slots__ = 'x', 'y'

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector.dot_product(self, other)

        return Vector.scalar_product(self, other)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if not (isinstance(other, int) or isinstance(other, float)):
            raise TypeError(f"""unsupported operand type(s) for /: 'Vector' and {type(other)}""")

        return Vector.scalar_product(self, 1/other)

    def __abs__(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __iter__(self):
        yield from (self.x, self.y)  # ignore your editor, these parentheses are not redundant

    def __getitem__(self, index: int):
        return (self.x, self.y)[index]

    @staticmethod
    def scalar_product(v1: "Vector", n: int):
        return Vector(v1.x * n, v1.y * n)

    @staticmethod
    def dot_product(v1: "Vector", v2: "Vector"):
        return v1.x*v2.x + v1.y*v2.y

    @staticmethod
    def cross_product(v1: "Vector", v2: "Vector"):
        return Vector(v1.x * (v2.x + v2.y), v1.y * (v2.x + v2.y))
