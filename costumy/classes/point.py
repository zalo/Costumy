# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""
point.py
File with the Point class
"""
import numpy as np
from costumy.utils import functions as fun

class Point:
    """
        The point class is a fancy representation of [x,y] coordinates.\n

        ```
        coords = Point(1,2)
        # coords.x  -> 1
        # coords.y  -> 2

        # coords[0] -> 1
        # coords[1] -> 2

        ```
        Note that not all operations (like mul, rel...) were overwritten.
    """
    def __init__(self,x,y):
        """`Point` initialisation

        Args:
            x (float): x coordinate
            y (float): y coordinate
        """
        self.x = x
        """x coordinate or [0]"""
        self.y = y
        """y coordinate or [1]"""

    def as_obj_segment(self, y_is_up=True,color=""):
        """Experimental - converts into a obj vertex statement

        Args:
            y_is_up (bool, optional): True Like in Maya X Y 0, False like in Blender X 0 Y . Defaults to True.
            color (str, optional): vertex color like "1 0 0" for red . Defaults to "".

        Returns:
            str: point as a vertex obj line ex: `v 1 2 3 ` or `v 4 5 6 1 0 0` with color
        """
        if y_is_up:
            vertexData = f"v {self.x} {self.y} 0 "
        else:
            vertexData = f"v {self.x} 0 {self.y} "
        return vertexData+color

    def as_svg(self,coord=False, size=1, color="black") -> str:
        """The Point represented by a small dot in a SVG, using a `circle` svg element.

        Args:
            coord (bool, optional): When true, add a `title` element, displaying coords onmousehover. Defaults to False.

        Returns:
            str: svg circle element
        """
        x = round(self.x,5)
        y = round(self.y,5)
        dot = f'<circle class="DebugDot" cx="{x}" cy="{y}" r="{size}" stroke="{color}" stroke-width="0.4" fill="{color}" fill-opacity="0.7"/>'
        if coord:
            dot = f'<circle class="DebugDot" cx="{x}" cy="{y}" r="{size}" stroke="{color}" stroke-width="0.4" fill="{color}" fill-opacity="0.7">'
            dot += f'<title>X {x}  Y {y}</title>'
            dot += '</circle>'
        return dot

    def as_json(self):
        """json representation of the Point
        ** IMPLICIT ROUND TO 5 DECIMALS **

        Returns:
            list: [x,y]
        """
        return [round(self.x,5), round(self.y,5)]

    def as_numpy(self):
        """returns `x` and `y` as a numpy array

        Returns:
            np.array: [x,y]
        """
        return np.array([self.x, self.y])

    def reflection(self,start_point, end_point):
        """move point to reflected position based on symmetry line defined by start_point, end_point"""
        _p = fun.reflection_of_point(self,start_point, end_point)
        return Point(*_p)

    def __getitem__(self, key):
        """Overwrite the get method to use both `Point.x `and `Point[0]` (or y and [1])"""
        return (self.x, self.y)[key]

    def __setitem__(self, key, item):
        """Overwrite the set method to use both `Point.x` and `Point[0]` (or y and [1])"""
        if key==0:
            self.x = item
        if key==1:
            self.y = item

    def __str__(self) -> str:
        """Overwrite the str representation to make the point easier to debug when printed"""
        x = str(self.x).ljust(6)
        y = str(self.y).ljust(6)
        return f"\033[91mx\033[0m:{x} \033[92my\033[0m:{y}"

    def __eq__(self, other) -> bool:
        """Overwrite the eq operation to make the equal comparaison available, like `if Point==Point:` """
        return self.x == other.x and self.y == other.y

    def __add__(self,other) :
        if isinstance(other, (Point,list,tuple)):
            return Point(self.x + other[0], self.y + other[1])
        elif isinstance(other,(float,int)):
            return Point(self.x + other, self.y + other)
        else : raise TypeError

    def __sub__(self,other) :
        if isinstance(other, (Point,list,tuple)):
            return Point(self.x - other[0], self.y - other[1])

        elif isinstance(other,(float,int)):
            return Point(self.x - other, self.y - other)
        else : raise TypeError

    def __mul__(self,other) :
        if isinstance(other, (Point,list,tuple)):
            return Point(self.x * other[0], self.y * other[1])

        elif isinstance(other,(float,int)):
            return Point(self.x * other, self.y * other)
        else : raise TypeError

    def __truediv__(self,other) :
        if isinstance(other, (Point,list,tuple)):
            return Point(self.x / other[0], self.y / other[1])

        elif isinstance(other,(float,int)):
            return Point(self.x / other, self.y / other)
        else : raise TypeError

    def __neg__(self):
        return Point(-self.x,-self.y)

    def __lt__(self, other):
        #Defines behavior for the less-than operator, <.
        if isinstance(other, (Point, list, tuple)):
            return (self.x < other[0] and self.y < other[1])
        elif isinstance(other, (float,int)):
            return Point(self.x < other, self.y < other)
        else :
            raise TypeError

    def __gt__(self, other):
        #Defines behavior for the greater-than operator, >.
        if isinstance(other, (Point, list, tuple)):
            return (self.x > other[0] and self.y > other[1])
        elif isinstance(other, (float,int)):
            return Point(self.x > other, self.y > other)
        else :
            raise TypeError

    def __round__(self,ndigits=0):
        if isinstance(ndigits, (int)):
            return Point(round(self.x, ndigits), round(self.y, ndigits))
        else :
            raise TypeError

    def __iter__(self):
        return iter((self.x, self.y))

    __rmul__ = __mul__

    def __len__(self):
        return 2

    def __abs__(self):
        return Point(abs(self.x),abs(self.y))

    def __hash__(self):
        return hash(tuple([self.x,self.y]))
