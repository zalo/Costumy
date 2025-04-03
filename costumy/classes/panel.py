# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
""" panel.py
this file contains the `Panel` class.
A very important class (along with `Pattern`)
"""
import copy
import collections
from typing import List
import svg.path as sv
from costumy.classes.point import Point
from costumy.classes.line import Line, Curve
from costumy.utils import functions as fun

class Panel:
    """
        The `Panel` class represent a piece from a garment, like a sleeve or the front of a tshirt.
        It is made of `Point` and `Line`.

        You can use a classmethod like `Panel.from_json()` or `Panel.from_svg()` to create a panel.

        A `Pattern` has multiples `Panel`.
    """
    def __init__(self, name="panel", translation=(0,0,0,), rotation=(0,0,0,)) -> None:
        """Init of a `Panel`
        This class represent a panel for a garment (like a sleeve or the front of a tshirt).
        It is made of `Point` and `Line`. A `Pattern` has multiples `Panel`

        Args:
            name (str): The panel name, like "front". Defaults to "panel".
            translation (list, optional): 3D translation vector for 3D placement of the panel. Defaults to [0,0,0].
            rotation (list, optional): 3D rotation vector for 3D placement of the panel. Given in XYZ Euler angles (as in Maya!). Defaults to [0,0,0].
        """
        self.name: str = name
        """Panel name, like "lfsleeve" or "front" """

        self.translation: list[float] = translation
        """3D translation vector defining where the panel should be in a 3D space. Given in Maya coordinate system (X right, Y up, Z foward)"""

        self.rotation: list[float] = rotation
        """3D rotation vector for 3D placement of the panel. Given in XYZ Euler angles (as in Maya)"""

        self.edges: list[Line] = []
        """List of `Line` instances that describes the panel shape."""

        self.vertices: list[Point] = []
        """List of `Point` instances that describes the panel shape."""

        self.source = None
        """Where the panel comes from"""

    #  FROM ______________________________________________________________________
    @classmethod
    def from_json(cls, data, name="panel", curvature_is_relative=True):
        """Creates a `Panel` from a section of a Garment Pattern Specification JSON.

        Args:
            data (str): panel data from json file (from a GarmentPattern Specification)
            name (str, optional): Panel name (should be unique). Defaults to "panel".
            curvature_is_relative (bool, optional): When true, converts the control points into control scale. Defaults to True.

        Returns:
            Panel instance filled with json data
        """
        panel = Panel(name, data["translation"], data["rotation"])
        panel.vertices = [Point(x[0],x[1]) for x in data["vertices"]]

        for edge in data["edges"]:

            # Start and and points
            p1 = panel.vertices[edge["endpoints"][0]]
            p2 = panel.vertices[edge["endpoints"][1]]

            # If line is a curve wih curvature info
            if "curvature" in edge:
                #if edge["curvature"].get("type")!="quadratic":
                #   continue
                pc = Point(edge["curvature"][0],edge["curvature"][1])
                if curvature_is_relative:
                    pc = fun.control_to_abs_coord(p1.as_numpy(),p2.as_numpy(),pc.as_numpy())

                pc = Point(pc[0],pc[1])
                line = Curve(p1,p2,pc)
            else:
                line = Line(p1,p2)
            line.endpoints = [ edge["endpoints"][0], edge["endpoints"][1] ]
            panel.edges.append(line)

        panel.source = cls.from_json
        return panel

    @classmethod
    def from_svg(cls, svg, name="panel"):
        """Create a `Panel` using the `d` attribute from an svg `path` element.
        Supports Quadratic curves only, no cubic curves.

        Args:
            svg (str): d attribute of an svg path element, like `M 0,0 L 1,10`
            name (str, optionnal): The panel name. Defaults to "panel"

        Returns:
            Panel : Panel with `Panel.vertices` and `Panel.edges`
        """
        panel = cls(name)
        panel.edges = []
        index = 0
        p = sv.parse_path(svg)
        bbox = p.boundingbox()
        minimum = Point(bbox[0],bbox[1])

        for segment in p:
            # real is x, imag is y
            start   = Point(segment.start.real- minimum.x, segment.start.imag - minimum.y)
            end     = Point(segment.end.real - minimum.x , segment.end.imag - minimum.y)
            if start==end: continue

            if isinstance(segment,sv.CubicBezier) :
                #idk if it should be a warning or raise an error
                print("The given svg contains Cubic Bezier curves, which are not supported.")
                print("You can use utils.functions.cubic2quad() to convert them into quadratic curves")
                raise RuntimeError("Cubic curves are not supported.")

            if isinstance(segment,sv.QuadraticBezier) :
                edge = Curve(start,end,Point(segment.control.real-minimum.x,segment.control.imag-minimum.y))
            else:
                edge = Line(start,end)

            edge.endpoints=[index,index+1]

            panel.edges.append(edge)
            panel.vertices.append(start)
            index +=1
        # The last edge should close the shape, so it returns onto the first vertice
        panel.edges[-1].endpoints[1] = 0

        # Make sure the panel is in cartesian space, not svg
        panel.move(panel.offset_in_cartesian)
        panel.scale([1,-1])
        panel.source = cls.from_svg
        return panel

    @classmethod
    def from_test_svg(cls):
        """Creates a `Panel` with commun issues from an hardcoded SVG string.
        The panel is shaped as an arrow pointing toward the SVG's coordinate system origin (top left of screen).
        Good to test features like `unsplit_lines`.
        """
        _svg = """M 0,0 V 58.3 L 21.6,37.5 C 36.1,52.8 55.5,72.7 65.7,81.4 76,90 89.9,75.2 81.5,65.7 73,56.1 52.2,36.6 37.9,21.8 L 60.6,0 Z"""
        _svg = fun.Cubic2Quad(_svg,50)
        panel = Panel.from_svg(_svg)
        panel.source = cls.from_test_svg
        return panel

    # AS ______________________________________________________________________
    def as_json(self,curvature_is_relative=True) -> dict:
        """Returns a representation of the panel as a dict, following the GarmentPattern json format.

        Args:
            curvature_is_relative (bool, optional): When true, the curvature of the edges will be converted into relative scale. Defaults to True.

        Returns:
            dic: `{"transtlation":[], "rotation":[], "vertices":[], "edges":[]}`
        """
        # "Pattern"/"panels"/ current
        jsonVertices = [vertice.as_json() for vertice in self.vertices]
        jsonEdges = [edge.as_json(curvature_is_relative) for edge in self.edges]

        dic = {
            "translation":self.translation,
            "rotation"   :self.rotation,
            "vertices"   :jsonVertices,
            "edges"      :jsonEdges,
        }
        return dic

    def as_svg(self, full_svg = False, minimal = False) -> str:
        """Returns a simple representation of the panel as an SVG.

        Args:
            full_svg (bool, optional): If True, Returns a complete SVG file to be saved as is. Defaults to False.
            minimal (bool, optional): If True, keeps only the outline (no text or href element). Defaults to False.

        Returns:
            str: multiple svg elements
        """

        # The panel is in cartesian space
        # Deepcopy it to avoid modifying the real points
        panel = copy.deepcopy(self)

        # flip it in Y to match the svg Y axis https://jenkov.com/tutorials/svg/svg-coordinate-system.html
        panel.scale([1,-1])

        # move it so that the shape is closest posible to 0,0 without having negative coordinates
        panel.move(panel.offset_in_svg)

        # The first segment starts must start with M x y,
        # and `Line.asSVGSegment()` would start with either L or Q
        firstSegment   = panel.edges[0].as_svg()                              # Only the first segment
        otherSegments  = [ edge.as_svg_segment() for edge in panel.edges[1:-1] ] # All other segments
        if isinstance(panel.edges[-1], Curve) :
            otherSegments.append(panel.edges[-1].as_svg_segment())
        closingSegment = "Z"                                                # Closing segment

        path_d = firstSegment + ' '.join(otherSegments) + closingSegment    # ex: "M 0 0 L 0 5 Z"

        mini, maxi = panel.get_bbox()

        # Group the Panel
        if minimal:
            content = fun.svgPathBundle(path_d,text="",circlebehindText=False, putingroup=False, add_a=False, stroke_size=0.1, color="gray", fill_opacity=0.6, id=panel.name, className="Panel", group_id=panel.name)
        else:
            content = fun.svgPathBundle(
                path_d,
                panel.name,
                circlebehindText=False,
                putingroup=False,
                stroke_size=0.5,
                color="gray",
                id=panel.name,
                className="Panel",
                group_id=panel.name,
                href=fun.svg_editor_url(path_d))

        if full_svg:
            return f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{mini.x-10},{mini.y-10},{maxi.x+20},{maxi.y+20}" >\n {content} </svg>\n'
        else:
            return content

    def as_svg_debug(self, full_svg = False, show_curve_points=False, freesewing_id = False) -> str:
        """Returns a detailed representation of the Panel as an SVG.

        Args:
            full_svg (bool, optional): If True, Returns a complete SVG file to be saved as is. Defaults to False.
            show_curve_points (bool, optional): if True, draw control points of quadratic curves. Defaults to False.
            freesewing_id (bool, optional): If True, displays the freesewing ID on edges if available. Defaults to False.
        Returns:
            str: multiple svg elements
        """

        # The panel is in cartesian space
        # Deepcopy it to avoid modifying the real points
        panel = copy.deepcopy(self)

        # flip it in Y to match the svg Y axis https://jenkov.com/tutorials/svg/svg-coordinate-system.html
        panel.scale([1,-1])

        # move it so that the shape is closest posible to 0,0 without having negative coordinates
        panel.move(panel.offset_in_svg)

        # Make an SVG with each edge of a different color and text near
        index = 0
        strPaths=[]
        bbox = panel.get_bbox()
        minimum = bbox[0]
        maximum = bbox[1]

        # Draw lines for each edges
        for edge in panel.edges:
            name = f"{panel.name} {index}"
            color = fun.colors[index%len(fun.colors)]
            if freesewing_id :
                shape = fun.svgPathBundle(edge.as_svg(),text=f"{edge.freesewing_ID}",color=color,text_size=3,fill_opacity=0,id=name,putingroup=False)
            else:
                shape = fun.svgPathBundle(edge.as_svg(),text=f"{index}",color=color,text_size=3,fill_opacity=0,id=name,putingroup=False)
            #shape = fun.svgPathBundle(edge.asSVG(),text=f"{edge.freesewing_ID}",color=color,text_size=1,fill_opacity=0,id=name,putingroup=False,circlebehindText=False)
            strPaths.append(shape)

            # Draw dotted lines to Curves Control points
            if show_curve_points and isinstance(edge,Curve):
                for p in [edge.p0, edge.p1]:
                    control_point_line = Line(p,edge.pc).as_svg()
                    shape = fun.svgPathBundle(control_point_line,stroke_size=0.3,stroke_dashed=True,color=color,putingroup=False,circlebehindText=False)
                    strPaths.insert(0,shape)
            index+=1

        edgesSVG = fun.gWrapper("\n".join(strPaths),transform=[0,0],className="Debug Lines")

        # Draw points for each vertice
        strPaths=[]
        for point in panel.vertices:
            strPaths.append(point.as_svg(True,color="black"))

        # Draw points for each control points
        for edge in panel.edges:
            if show_curve_points and isinstance(edge,Curve):
                strPaths.append(edge.pc.as_svg(True,size=0.5,color="#050505"))

        pointSVG = fun.gWrapper("\n".join(strPaths),transform=[0,0],className="Debug Points")

        DebugContent = f"{self.as_svg(False)} {edgesSVG} {pointSVG} "
        # DebugContent = f"{panel.asSVG(False)} {edgesSVG}"

        if full_svg:
            return f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{minimum.x-10},{minimum.y-10},{maximum.x+20},{maximum.y+20}" >\n {DebugContent} </svg>\n'
        else:
            return DebugContent

    def _as_obj(self,quality=10):
        """Experimental - Return the OBJ version of a panel

        Args:
            quality (int, optional): How many edges is used to represent a line or a curve. Defaults to 10.

        Returns:
            str: obj content
        """
        # TEST WIP
        colors = ["0 0 1", "0 1 0", "1 0 0"]
        txt=f"o {self.name}\n"
        subvertices = []
        for edge in self.edges:
            subvertices += edge.sample(quality)

        for index,vertex in enumerate(subvertices):
            txt +=vertex.asOBJSegment(color=colors[index%len(colors)]) + "\n"

        faces = []
        for i in range(1,len(subvertices)):
            faces.append(str(i))
        txt += "\nf " + " ".join(faces) + "\n"
        return txt

    # PROPERTY _________________________________________________________________
    @property
    def offset_in_svg(self):
        """ The distance between the shape's smallest position and the SVG origin """
        return -self.get_bbox()[0]

    @property
    def offset_in_cartesian(self):
        """The distance between the shape's center and the cartesian origin"""
        return -self.center

    @property
    def center(self) -> Point:
        """The panel's centroid (point in the middle of the shape)"""
        # Could be the mean of all points (but curves should be resampled first)
        # Using the bbox is pretty close, but idk probably slower

        mini, maxi = self.get_bbox()
        # minimum position of the panel's bounding box
        # maximum position of the panel's bounding box
        height = abs(maxi.y - mini.y)
        width  = abs(maxi.x - mini.x)

        center = Point( (width/2), (height/2))
        center += mini
        return round(center,4)

    @property
    def width(self) -> float:
        """The Panel approximate height"""
        mini, maxi = self.get_bbox()
        return abs(maxi.x - mini.x)

    @property
    def height(self) -> float:
        """The Panel approximate width"""
        mini, maxi = self.get_bbox()
        return abs(maxi.y - mini.y)

    # METHODS _________________________________________________________________

    def unfold(self,edge_index) -> None:
        """Unfolds the panel on an edge. `|] -> [ | ]`

        Note: implicit operations
            Does some unholy implicits operations on the panel :
            - Deletes the edge at the `edge_index`
            - Centers the unfolded panel (aligns the `Panel.center` with (0,0))
            - Normalize the edge order to bottom left `self.order_edges_for_GarmentPattern()`

        Args:
            edge_index (int): The edge's index used as the "symmetry axis" to unfold the panel.
        """
        # Select edge of symmetry and remove it
        sym = self.edges.pop(edge_index)

        # Reorder edges
        # The edge after the symmetry edge is now self.edges[0]
        self.order_edges(sym.p1)

        mirrored_edges = copy.deepcopy(self.edges)
        for e in mirrored_edges:
            e.p0 = e.p0.reflection(*sym)
            e.p1 = e.p1.reflection(*sym)
            if isinstance(e,Curve):
                e.pc = e.pc.reflection(*sym)

            # flip edge ID for stitches (based on freesewing pattern)
            if e.freesewing_ID is not None:
                e.freesewing_ID = -e.freesewing_ID

        # reverse edge order of mirrored edges
        mirrored_edges.reverse()

        for edge in mirrored_edges:
            edge.swap_endpoints()

        #add mirrored edges to current edges
        self.edges += mirrored_edges
        self.remake_vertices()

        #center shape
        #NOTE:Might be wrong to assume we are in svg space
        self.move(self.offset_in_cartesian)
        self.normalize_edge_order()

    def remake_vertices(self):
        """Remakes `self.vertices` based on the edges P0 (star points).
        Changes `self.edges` endpoints accordingly
        """
        # Change the vertices order, then the edge endpoints
        # Sort the vertices using the edge.P0
        vertexList = []
        for index, edge in enumerate(self.edges):
            vertex = edge.p0
            vertexList.append(vertex)
            edge.endpoints= [index, index+1]

        # Close the shape by setting the last edge back to the first index
        self.edges[-1].endpoints[1] = 0
        self.vertices = vertexList

    def straighten_curves(self,treshold = 0.9999):
        """Straighten curves that aint that curvy
        (transform `Curve`s into `Line`s)

        ```
        # All curves are turned into lines
        panel.straighten_curves(0.0)

        # Only curves that are exactly straight are turned into lines
        panel.straighten_curves(1.0)

        # Curves that are almost straight are turned into lines
        panel.straighten_curves(0.999)
        ```
        """
        for i, edge in enumerate(self.edges):
            if not isinstance(edge,Curve): continue
            diff = (edge.as_line().length / edge.length)
            #diff = edge.length - edge.as_line().length
            if round(diff,3) >= treshold:
                self.edges[i] = edge.as_line()

    def unsplit_lines(self, treshold = 0.9999):
        """Fuse almost collinear `Line`s. Usefull after using `unfold_lines`.

        Args:
            treshold (float, optional): 0->fuse eveything, 1-> Fuse only collinear lines. Defaults to 0.9999.
        """
        # Since Quadratic curves are fancy
        # I will only merge straight lines
        # We could Cubic2Quad merged lines if required

        for i, edge in enumerate(self.edges):
            if isinstance(edge,Curve): continue
            if i >= len(self.edges)-1:break

            next_edge = self.edges[i+1]
            # If the length is about the same with or without
            points = [edge.p0, edge.p1, next_edge.p1]
            #diff = fun.get_distance_between(*points) - fun.get_distance_between(edge.p0, next_edge.p1)
            diff = fun.get_distance_between(edge.p0, next_edge.p1) / fun.get_distance_between(*points)

            if diff >=treshold:
                removed = self.edges.pop(i+1)
                # Keep the biggest ID for stitches (with freesewing patterns)
                if removed.freesewing_ID is not None:
                    self.edges[i].freesewing_ID = min(self.edges[i].freesewing_ID, removed.freesewing_ID)
                self.edges[i].p1 = removed.p1

            i+=1
        self.remake_vertices()

    def get_bbox(self) -> List[Point]:
        """Estimate the extreme coordinates (bouding box) from vertices list

        Returns:
            List[Point]: Returns a list of Points [min,max]
        """
        subvertices = []
        for edge in self.edges:
            subvertices+=edge.sample(5)

        minimum = Point(0,0)
        maximum = Point(0,0)
        for point in subvertices:
            minimum.x = min(point.x,minimum.x)
            minimum.y = min(point.y,minimum.y)

            maximum.x = max(point.x,maximum.x)
            maximum.y = max(point.y,maximum.y)
        return (minimum,maximum,)

    def scale(self,scale=(1,1,)):
        """Scale the panel by multiplying its vertices position by a value

        Using `self.move(self.offset_in_cartesian)` will ensure the scale
        is made from the middle of the shape.

        Using `scale((1,-1))` would flip the panel verticaly.

        Args:
            scale (list, optional): float [x,y]. Defaults to [1,1].
        """
        scale = Point(scale[0],scale[1])
        for i, v in enumerate(self.vertices):
            self.vertices[i] = v * scale
        for e in self.edges:
            e.p0 = e.p0 * scale
            e.p1 = e.p1 * scale
            if isinstance(e,Curve):
                e.pc = e.pc * scale

    def move(self,offset=(0,0,)):
        """Offsets all vertices and control points by a value

        Args:
            offset (list, optional): offset as [x,y]. Defaults to [0,0].
        """
        offset = Point(offset[0],offset[1])
        for i, v in enumerate(self.vertices):
            self.vertices[i] = v + offset
        for e in self.edges:
            e.p0 = e.p0 + offset
            e.p1 = e.p1 + offset
            if isinstance(e,Curve):
                e.pc = e.pc + offset

    def rotate(self, angle:float=0, pivot = None ):
        """Rotate the whole panel around the pivot point

        Args:
            angle (float, optional): Angle of rotation in degree. Defaults to 0.
            pivot (Point, optional): A point [x,y] to rotate around. Defaults to self.center.
        """
        if pivot is None:
            pivot = self.center

        self.vertices = [Point(*fun.rotate(pivot, v, angle)) for v in self.vertices]

        for e in self.edges:
            e.p0 = Point(*fun.rotate(pivot, e.p0, angle))
            e.p1 = Point(*fun.rotate(pivot, e.p1, angle))
            if isinstance(e, Curve):
                e.pc = Point(*fun.rotate(pivot, e.pc, angle))

    def order_edges(self,origin=(0,0)):
        """
        Sorts the edges and vertices in a fancy radial way, to ensure consistency across patterns.
        The first vertex will be the one closest to the specified origin.

        The edges and vertices will be counterclock wise in cartesian space.

        Args:
            origin (tuple, optional): The first vertex will be the closest to the specified value (x,y). Defaults to (0,0).
        """

        # Find the edge with the start point nearest to the origin

        # We use the edges as the reference for everything,
        # to reconstruct the vertices in the right order

        lastDistance = float("inf") # biggest distance possible
        calculus=0
        # Find out what vertices is the nearest to 0,0 (does not take in account curve)
        for index,edge in enumerate(self.edges):
            distance = abs(edge.p0.x - origin[0]) + abs(edge.p0.y - origin[1])
            calculus += (edge.p1.x - edge.p0.x)*(edge.p1.y + edge.p0.y)

            if distance < lastDistance:
                lastDistance = distance
                shiftValue   = index # value used to rotate the list

        # Change the edge order
        x  = collections.deque(self.edges)
        x.rotate(-shiftValue)
        self.edges = list(x)
        # https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
        # We want Counter Clock wise edges in a panel.
        # If the total of calculus is negative, then the shape is counterclockwise
        isClockWise = calculus > 0
        if isClockWise:
            self.edges.reverse()


        # Change the vertices order, then the edge endpoints
        # Sort the vertices using the edge.P0
        for edge in self.edges:
            if isClockWise:
                edge.swap_endpoints()

        self.remake_vertices()

    def normalize_edge_order(self):
        """Reorder the panel edges to match the GarmentPattern specification.
        The edge nearest to the bottom right becomes the first in the list."""
        self.order_edges(origin=self.get_bbox()[0])           #CounterClock edges

    def align_translation(self, p2d=(0,0,), p3d=(0,0,0,), p3d_from_blender = True):
        """Set the panel.translation by aligning a point from the panel and a point in 3D.

        Args:
            p2d (tuple, optional): 2D position from the panel to align with the p3d. Defaults to (0,0,).
            p3d (tuple, optional): 3D position to align with the p2d (with maya axis or blender axis). Defaults to (0,0,0,).
            p3d_from_blender (bool, optional): When true, converts the p3d position into maya coordinate first, assuming it was from blender. Defaults to True.
        """
        if p3d_from_blender:
            p3d = (p3d[0], p3d[2], -p3d[1])

        x = self.center[0] - (p2d[0] - p3d[0]) #right
        y = self.center[1] - (p2d[1] - p3d[1]) #up
        z = p3d[2]                            #foward

        self.translation = [x,y,z]

    def __round__(self,ndigits=5):
        # Rounds the vertices position
        #tempPanel = copy.deepcopy(self)
        self.vertices = [round(v, ndigits) for v in self.vertices]
        for e in self.edges:
            e.p0 = round(e.p0,ndigits)
            e.p1 = round(e.p1,ndigits)
            if isinstance(e,Curve):
                e.pc = round(e.pc,ndigits)

        return self

    def __str__(self):
        # Cute print(Panel)

        nedge = len(self.edges)
        ncurve = len([x for x in self.edges if isinstance(x,Curve)])

        text="\n"
        details = [
        f"Panel named {self.name}",
        f"{len(self.vertices)} vertices",
        f"{nedge} edges ({nedge - ncurve} lines, {ncurve} curves)",
        f"source:{self.source}",
        f"repr  :{self.__repr__()}"
        ]
        text+="\n".join(details)
        text+="\n"
        return text

# Thanks for reading this far