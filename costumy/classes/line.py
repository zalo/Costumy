# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
from costumy.classes.point import Point
from costumy.utils import functions as fun

import numpy as np

def _as_point(i):
    if isinstance(i,Point):
        return i

    elif isinstance(i, (list,tuple,np.ndarray,)):
        if len(i)==2:
            return Point(i[0],i[1])
        else:
            raise ValueError(f"A Point requires 2 values (x,y), not {len(i)}")
    else:
        raise TypeError()


class Line:
    """
        The `Line` class is the representation of a basic line. It is made of two `Point`.\n
        A `Curve` is like a `Line`, but it has a `pc`, the control point of a quadratic curve

        Args:
            P0 (Point): starting coordinate
            P1 (Point): ending coordinate
    """
    def __init__(self, p0:Point, p1:Point):
        """Init of a `Line` instance"""
        self.p0 = _as_point(p0)
        """Start `Point`"""

        self.p1 = _as_point(p1)
        """ End `Point` """

        self.endpoints = []
        """Used for the json representation of a line. An edge has two endpoints, two int used as indexes in a vertices like [0,1] """

        self.freesewing_ID = None
        """Used to remap stitches when created by a `Design`"""

    def sample(self,quality=10):
        """Sample the line into a list of len(quality) points. Usefull to draw a curve using straight lines.

        Args:
            subdivision (int, optional): The number of points to split the line into. More point -> Curve looks more smooth. Defaults to 10.

        Returns:
            list: list of `Point`. Starts by `edge.p1` and ends with `edge.P1`
        """
        sampledPoints=[self.p0]

        for i in range(quality+1):
            step = i/quality
            if step==0 or step==1: continue
            sample = fun.pointOnLine(self.p0,self.p1,step)
            sampledPoints.append(Point(sample[0],sample[1]))

        sampledPoints.append(self.p1)

        return sampledPoints

    def as_json(self,relative=True):
        """Json representation of an edge for the specification.json\n
        Note that in the json, the edges are defined by the endpoints.
        Each endpoint is an Index to point to the vertices list, where the coordinate are.

        In a `Curve`, adds the "curvature" with its relative value `"curvature":[float,float]`

        Args:
            relative (bool, optional): Converts curvature to relative position. Defaults to True

        Returns:
            dic: `{"endpoints":[int,int]}`
        """
        # return {"endpoints":[firstPointIndex,firstPointIndex+1]}
        return {"endpoints":[self.endpoints[0],self.endpoints[1]]}

    def as_svg(self):
        """Line as a SVG path `d` element

        Returns:
            str: "M StartPoint L EndPoint" like `M 10 10 L 20 20`
        """
        return f'M {self.p0.x} {self.p0.y} L {self.p1.x} {self.p1.y}'

    def as_svg_segment(self):
        """Line as a segment of a path `d` element.
        Usefull when joining multiple `Line` to form one SVG path.

        Returns:
            str: "L EndPoint" like `L 20 20`
        """
        return f' L {self.p1.x} {self.p1.y}'

    def swap_endpoints(self):
        """Swap the edge.
        `self.p0` and `self.p1` swap values, endpoints are reversed"""
        _P0 = self.p0
        _P1 = self.p1
        self.p0 = _P1
        self.p1 = _P0
        self.endpoints.reverse()


    def _as_obj_segment(self):
        return ""

    def as_curve(self):
        """Return a straight `Curve` made from the line.
        The `Curve.PC` is the `Line.center`
        """
        #controlPoint = (self.P0 + self.P1) / 2
        return Curve(self.p0, self.p1, self.center)

    def as_line(self):
        """Useless to call this for a straight line but be my guess

        Returns:
            `Line`: return itself
        """
        return self


    @property
    def center(self):
        """Center of line"""
        return Point(*fun.pointOnLine(self.p0,self.p1,0.5))

    @property
    def length(self):
        """Distance between `self.P0` and `self.P1`"""
        return fun.get_distance_between(self.p0, self.p1)


    def __str__(self):
        """Overwrite the str representation to make line easier to visualise when printed"""
        return f"\n\033[1medge:\033[0m {self.p0} | {self.p1}"

    def __iter__(self):
        """Define unpacking behavior, *Line -> P0, P1"""
        return iter((self.p0, self.p1))

class Curve(Line):
    def __init__(self, p0:Point, p1:Point, pc:Point):
        super().__init__(p0, p1)
        self.pc = _as_point(pc)

    def get_curvature(self,relative=True):
        """Using an absolute position, get the relative value for curvature

        Args:
            relative (bool, optional): When true, converts the curvature into relative position. Defaults to True.

        Returns:
            tuple: (x,y)
        """
        # Using an absolute position, get the relative value for curvature
        if relative:
            return fun.control_to_relative_coord(self.p0.as_numpy(),self.p1.as_numpy(),self.pc.as_numpy())
        else:
            return self.pc

    def as_json(self,relative=True):
        curvature = self.get_curvature(relative)
        if not relative:
            curvature = (round(curvature[0],5),round(curvature[1],5))
        return {"endpoints":[self.endpoints[0],self.endpoints[1]],"curvature":[curvature[0],curvature[1]]}

    def as_svg(self):
        """Curve as a SVG path `d` element

        Returns:
            str: "M StartPoint Q ControlPoint EndPoint" like `M 10 10 Q 10 10 20 20`
        """
        return f'M {self.p0.x} {self.p0.y} Q {self.pc.x} {self.pc.y} {self.p1.x} {self.p1.y} '

    def as_svg_segment(self):
        """Curve as a segment of a path `d` element.
        Usefull when joining multiple `Line` to form one SVG path.

        Returns:
            str: "Q ControlPoint EndPoint " like `Q 10 10 L 20 20`
        """
        return f'Q {self.pc.x} {self.pc.y} {self.p1.x} {self.p1.y} '


    def as_curve(self):
        """Useless to call this for a curve but go ahead have fun

        Returns:
            `Curve`: return itself
        """
        return self

    def as_line(self):
        """Return a straight `Line` made from the Curve.

        Returns:
            `Line`: return new line
        """
        return Line(self.p0,self.p1)

    def sample(self,quality=10):
        sampledPoints=[self.p0]

        for i in range(quality+1):
            step = i/quality
            if step==0 or step==1:continue
            sample = fun.pointOnQuadCurve(self.p0,self.pc,self.p1,step)
            sampledPoints.append(Point(sample[0],sample[1]))

        sampledPoints.append(self.p1)

        return sampledPoints


    @property
    def center(self):
        """Center of line"""
        return Point(*fun.pointOnQuadCurve(self.p0,self.pc,self.p1,0.5))

    @property
    def length(self):
        """Approximative Distance between `self.P0` and `self.P1`
        (The length is the total distance between 10 straight lines placed on the curve )
        """
        # distance of the curve made from 10 points
        return fun.get_distance_between(*self.sample(20))
        #_c = (self.P0.x - self.P1.x)**2 - (self.P0.y - self.P1.y)**2


    def __str__(self):
        return f"\n\033[1mcurv\033[0m: {self.p0} | {self.p1} | {self.pc}"
