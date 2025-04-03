# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""
Various functions for costumy. Reasonably chaotic.
"""
import json
import os.path
import subprocess
import tempfile
import time
from xml.dom import minidom

import numpy as np
import svg.path as sv
import re
import cmath
import xml.etree.ElementTree as ET
import math
from importlib import resources
from pathlib import Path

class _paths:
    """Paths used by functions in this file """
    base = Path(str(resources.files("costumy").joinpath("")))

    cubic2quad = base / "node"/ "cubic2quad_pipe.js"
    """script to approximate cubic curves with quadratic curves"""

    generate_freesewing = base/ "node" / "generate_pattern.mjs"
    """script to generate freesewing patterns"""

# Handy list of hand picked colors
colors = [
    "#f23c3c", #red
    "#f2813c", #orange
    "#f2c53c", #jaune
    "#a7f23c", #vert
    "#3cf2d2", #teal
    "#3c96f2", #blue
    "#8d3cf2"  #purple
]


# IMPORT AND EXPORT _______________________________________________________________________________

def ImportInkscapeSVG(svgFilePath):
    """Retrive the name and svg path `d` attribute from an Inkscape svg

    Args:
        svgFilePath (path): file path to the svg file

    Returns:
        dic: all elements as a name:path.d pair `{"name":"M 0 0 L 10 10 Z}`
    """
    doc = minidom.parse(svgFilePath)  # parseString also exists
    svgPaths = {label.getAttribute("inkscape:label") : path.getAttribute('d') for label, path in zip(doc.getElementsByTagName('path'),doc.getElementsByTagName('path'))}
    doc.unlink()
    return svgPaths

def ImportPatternFriendSVG(svgFilePath):
    """Retrive the id and d attributes from all path item found in the file

    Args:
        svgFilePath (path): file path to the svg file

    Returns:
        dic: all elements as a `name:path.d` pair `{"name":"M 0 0 L 10 10 Z}`
    """
    if os.path.exists(svgFilePath):
        doc = minidom.parse(svgFilePath)  # parseString also exists
    else :
        doc = minidom.parseString(svgFilePath)  # parseString also exists
    svgPathDic = {}
    uniqueNameInt = 0
    for svgPath in doc.getElementsByTagName("path"):
        path_name = svgPath.getAttribute("id")
        path_d    = svgPath.getAttribute("d")
        if path_name == "":
            path_name = f"NoName_{uniqueNameInt}"
            uniqueNameInt+=1
        svgPathDic[path_name] = path_d
    doc.unlink()
    return svgPathDic

def ImportFreeSewingSVG(svgFilePath,idMustStartsWith = "fs",keepOnlyFabricClass = False,):
    """Retrive the id and d attributes from all path item found in the file.
    Keys are the ID of the path's parent group

    Args:
        svgFilePath (path): file path to the svg file

    Returns:
        dic: all elements as a `name:path.d` pair `{"name":"M 0 0 L 10 10 Z}`
    """
    if os.path.exists(svgFilePath):
        doc = minidom.parse(svgFilePath)  # parseString also exists
    else :
        doc = minidom.parseString(svgFilePath)
    svgPathDic = {}
    uniqueNameInt = 0
    for svgPath in doc.getElementsByTagName("path"):
        path_class    = svgPath.getAttribute("class")
        if path_class =="fabric" or not keepOnlyFabricClass:
            if svgPath.parentNode.nodeName=="g": #group:
                path_name = svgPath.parentNode.getAttribute("id")
            else:path_name = svgPath.getAttribute("id")
            path_d    = svgPath.getAttribute("d")
            if path_name == "":
                path_name = f"NoName_{uniqueNameInt}"
                uniqueNameInt+=1
            if path_name.startswith(idMustStartsWith):
                svgPathDic[path_name] = path_d

    doc.unlink()
    return svgPathDic

def SplitPadSystemXML(xmlFilePath):
    uniquePatterns = {}
    if os.path.exists(xmlFilePath):
        root = ET.parse(xmlFilePath).getroot()                             # pattern
    else:
        root = ET.ElementTree(ET.fromstring(xmlFilePath))
        #root = ET.parseString(xmlFilePath).getroot()                       # pattern

    for piece in root.iter("piece"):                            # pattern/pieces[]
        edges       = []
        vertices    = []
        pointsPos   = []
        name        = piece.find("name").text                       # MyName
        patternNumber = piece.find("pattern_number").text

        plan_prod = piece.find("plan_production")                   # Use the plan_production shapes
        if plan_prod.text !="production":continue
        if patternNumber not in uniquePatterns:
            uniquePatterns[patternNumber] = '<?xml version="1.0" encoding="UTF-8"?>\n <pattern>' + ET.tostring(piece,encoding="unicode")
        else :
            uniquePatterns[patternNumber]+= "\n" + ET.tostring(piece,encoding="unicode")
    for key,value in uniquePatterns.items():
        uniquePatterns[key] += "</pattern>"
    return uniquePatterns

def ImportSVG(svg):
    """Guesses between Import from Inkscape or PatternFriend

    Args:
        svg (str): file path to the svg file or string representing an svg

    Returns:
        dic: all elements as a `name:path.d` pair `{"name":"M 0 0 L 10 10 Z}`
    """
    svg = str(svg)
    if os.path.exists(svg):
        with open(svg,"r") as f:
            isinkscapefile= "Inkscape" in f.readlines()[1]

        if isinkscapefile:
            return ImportInkscapeSVG(svg)
        else:
            return ImportPatternFriendSVG(svg)
    else:
        return ImportPatternFriendSVG(svg)

def ExportSVG(outputPath,data):
    """Write an SVG to the specidied outputPath"""
    with open(outputPath,"w",encoding="UTF-8") as f:
        f.write(data)

def ExportJSON(outputPath,data):
    """Write a json file at the specified outputPath"""
    with open(outputPath,"w",encoding="UTF-8") as f:
        f.write(json.dumps(data,indent=2))

def TempPreview(FileContent,filename="PatternPreview.svg"):
    """Open a temporary file in the default app, based on the finename extension. Deletes after a second

    Args:
        FileContent (str): file content
        filename (str,optional): name of the temp file. Defaults to "PatternPreview.svg"
    """
    with tempfile.TemporaryDirectory(prefix="PatternFriend_") as td:
        f_name = os.path.join(td, filename)
        with open(f_name, 'w') as fh:
            #fh.write("hi from function")
            fh.write(FileContent)
            fh.seek(0) #otherwise the file cant load apparently
            os.startfile(f_name)
            time.sleep(1) #otherwise the file cant load

def svg_editor_url(svg_d,local=False):
    """Return a link to the svg_path_editor tool to edit and visualize the quad beziers

    Args:
        svg (str): d attribute of a svg path
        local (bool, optional): if true will use localhost instead of web url. Defaults to False.

    Returns:
        str: url
    """
    baseURL = "https://yqnn.github.io/svg-path-editor/#P="
    if local: baseURL="http://localhost:4200/#P="
    return( baseURL + svg_d.replace(" ","_").replace(",","_"))

def svg_visualizer_url(svg_d):
    """Return a link to the svg visualizer tool to explain a path step by step

    Args:
        svg (str): d attribute of a svg path

    Returns:
        str: url
    """
    baseURL = "https://svg-path-visualizer.netlify.app/#"
    return( baseURL + svg_d.replace(" ","%20").replace(",","%20"))


# SVG ______________________________________________________________________________________________

def generate_freesewing_pattern(measurements, options=None):
    """Creates a freesewing SVG pattern by calling generate_pattern.js with node.js"""
    # To add new designs we need some work to install new node modules
    # and each design will need a custom js file because it does not use a dynamic import
    # See https://github.com/freesewing/pattern-via-io

    #NOTE: There is a way to get pannels from freesewing as JSON too. It could be easier that way !

    freesewing_template = {
        "sa": 10,
        "scale": 1,
        "complete": False,
        "paperless": False,
        "locale": "en",
        "units": "metric",
        "measurements": measurements,
        "options": options,
    }
    process = subprocess.Popen(['node', str(_paths.generate_freesewing)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process_stdout, _ = process.communicate(input=json.dumps(freesewing_template, indent=4).encode())
    return process_stdout.decode()


def multiply_svg(svg_d,value):
    """Experimental - Using regex, multiply any number found in a string, like an path d attribute. Usefull for Cubic2Quad

    Args:
        svg_d (str): d attribute like `M 1 2 L 3 4 Z`
        value (float): value to multiply the numbers

    Returns:
        str: multiplied version of the string, like `M 10 20 L 30 40 Z`
    """
    svg_d = svg_d.replace(","," ")
    svg_d = re.sub("[A-Za-z]+", lambda ele: " " + ele[0] + " ", svg_d)
    d_list = svg_d.split()

    for index,element in enumerate(d_list):
        # If its a number
        if element.replace(".", "").replace("-","").isnumeric():
            # multiply the number and reput it in the list as a string
            d_list[index] = str(float(element) * value)

    return " ".join(d_list)
    #return re.sub('\d+',lambda x:repr(int(x.group())*value),svg_d)

def Cubic2Quad(svg_d,tolerance=5):
    """Approximate an svg with cubic curve into an svg with lines and quadratic curves only. Also converts the SVG in absolute elements.
    Calls the node.js script `node/cubic2quad_pipe.js`\n
    ** THE SCALE OF A SHAPE AFFECTS THE OUTPUT**, you can use `multiply_svg` to help


    Args:
        svg_d (str): a path `d` element like `M 2 5 C 2 8 8 8 8 5 Z`
        tolerance (int, optional): Tolerance of a curve before it is split into multiple curves. A big value would try to use as few curve possible. Defaults to 5.

    Raises:
        ValueError: Happens if the output of the node.js script is empty

    Returns:
        str: converted d path attribute, no cubic, in absolute positions.
    """

    base = Path(str(resources.files("costumy").joinpath("")))
    js_script = base / "node"/ "cubic2quad_pipe.js"
    with subprocess.Popen(["node", str(js_script) ,svg_d,str(tolerance)],  stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        out = process.stdout.read().decode('UTF-8').replace("\n","")
        out = out.strip()
        if out=="": raise ValueError("Nothing returned by the node.js script for Cubic2Quad")
    return out

def ConvertFakeCubic(svg_d,tolerance=5):
    """EXPERIMENTAL, convert "fake" cubic curves into quadratic curves
    (This solution works most of the time, but its quirky and unoptimised)

    Args:
        svg_d (str): d element of an svg `path` (`d="M 0,0 L 1 2 L 2 4 Z`)
        tolerance (float, optional): Tolerance for Cubic2Quad. Defaults to 5.

    Returns:
        str: svg d element with cubic curves changed
    """
    # Check for any cubic curves that could easily be turned into a Quadratic curve instead
    svg = sv.parse_path(svg_d)
    for index,item in enumerate(svg) :
        # if the first control point is at the same position than the start point
        if isinstance(item,sv.CubicBezier):
            start = (item.start.real,  item.start.imag)
            c1 =    (item.control1.real,item.control1.imag)
            c2 =    (item.control2.real,item.control2.imag)
            end =   (item.end.real,    item.end.imag)
            intersection = get_intersect( start, c1, end, c2)
            apoint = complex(intersection[0],intersection[1])

            if item.start==item.control1:
                svg[index] = sv.QuadraticBezier(item.start,item.control2,item.end)

            # if the last control point is at the same position than the end point
            elif item.end==item.control2:
                svg[index] = sv.QuadraticBezier(item.start,item.control1,item.end)

            # If a vector from start->control1 and a vector from end->c2 would intersect at some point
            elif cmath.isfinite(apoint):
                svg[index] = sv.QuadraticBezier(item.start,apoint,item.end)

                # HACK : This solution might cause problems
                # We run Cubic2Quad on the curve and check if the curve would be splitted into smaller segments.
                # If yes, then keep it intact (so that it can be converted again by cubic2quad)
                # If not, then use the intersection as the new control point and convert it into a Quadratic Curve directly
                # This is meant to fix situations where the control point are on different side, I havent test it that much
                #
                #    control points are on different sides             control points are on the same side
                #  +---------------------------------------+        +---------------------------------------+
                #  |           **                          |        |           **                          |
                #  |      c1     **                        |        |      c1     **                        |
                #  |              **                       |        |              **                       |
                #  |               **                      |        |               **                      |
                #  |                 **                    |        |                 **                    |
                #  |                  **                   |        |                  **                   |
                #  |                   **         c2       |        |      c2           **                  |
                #  |                     **                |        |                     **                |
                #  +---------------------------------------+        +---------------------------------------+

                cub2qua = Cubic2Quad(f"M {start[0]} {start[1]} C {c1[0]} {c1[1]} {c2[0]} {c2[1]} {end[0]} {end[1]}",tolerance=tolerance)
                if len( sv.parse_path(cub2qua) ) <= 4 : # Meaning there is more than one curve
                    svg[index] = item




    #Rebuild the dictionary with the modificated svg paths (some Cubic curves are now Quadratic)

    return svg.d()

def svgPathBundle( path, text="", color="red", position=(0,0,), stroke_size=1.0, text_size=-1, circlebehindText=True, putingroup=True, fill_opacity=0.1, id="", className="",group_id="",href="",add_a=True, stroke_dashed = False):
    """Creates svg elements with inline style

    Args:
        path (str): path `d` value, like `M 0 0 L 10 10 Z`
        text (str, optional): Text placed at the center of the shape made by the path. Defaults to "".
        color (str, optional): Color used for various item, can be #hex too. Defaults to "red".
        position (list, optional): float[x,y] adds a transform to the group to move it in svg space. Defaults to [0,0].
        stroke_size (float, optional): size of the stroke. Defaults to 1.
        text_size (int, optional): size of the text, set to -1 to let the code decide the size. Defaults to -1.
        circlebehindText (bool, optional): When true, add a circle behind the text, usefull for small text, like in the debug svg. Defaults to True.
        putingroup (bool, optional): When true, place the path,text,circle,href elements in a `g` group. Defaults to True.
        fill_opacity (float, optional): opacity of background of shape and circles. Defaults to 0.1.
        id (str, optional): id of the path element. Defaults to "".
        className (str, optional): class name of the group. Defaults to "".
        group_id (str, optional): id of the group. Defaults to "".
        href (str, optional): When true, add an a element with an href to the group (to open an url when the shape is clicked). Defaults to "".
        add_a (bool, optional): When true, place the text,circle,href elements in a `a` element with the class "annotation". Defaults to True.

    Returns:
        str: svg element to put within an svg file
    """

    #Transform info
    box = sv.parse_path(path).boundingbox()
    boxSize = [box[0]+box[2], box[1]+box[3] ]
    boxCenter = [boxSize[0]/2, boxSize[1]/2 ]
    translate = f"translate({position[0]},{position[1]})"
    transform = (f'transform="{translate}"',"")[position==[0,0]]
    if text_size == -1:
        if boxSize[0]<=150 : text_size=5
        elif boxSize[0]<=500 : text_size=20
        else: text_size=15


    #Basic Shape
    dashed = ('','stroke-dasharray="1" style= "filter: brightness(0.9)"')[stroke_dashed]
    group   = f'<g id="{group_id}" class="{className}" {transform}>\n   '
    shape   = f'<path id="{id}" d="{path}" stroke="{color}" stroke-linecap="round" {dashed} fill="{color}" fill-opacity="{fill_opacity}" stroke-width="{stroke_size}" />'

    # Annotations
    href = ( "", f'href="{href}"' )[href!=""] #if href is empty remove it
    aref    = f'\n  <a class="annotation" {href}>'
    circle  = f'\n  <circle cx="{boxCenter[0]}" cy="{boxCenter[1]}" r="2" fill="{color}" stroke="black" stroke-width="0.1" />'
    if text!="":
        textitem= f'\n   <text x="{boxCenter[0]}" y="{boxCenter[1]}" font-size="{text_size}" font-family="monospace" text-anchor="middle" alignment-baseline="middle"  fill="black" > {text} </text>'
    else:
        textitem=""

    # Circles behind text (used for edges ID)
    if circlebehindText:
        textitem = f"{circle}{textitem}"
    else:
        textitem = f"{textitem}"

    if add_a:
        content = f'{shape}{aref}{textitem} </a>'
    else:
        content = f'{shape}{textitem}'

    if putingroup:
        final = f'{group} {content} </g>'
    else:
        final = f'{content}'

    return final

def svgWrapper(strPaths,viewBoxMinimum=[0,0],viewBoxMaximum=[100,100]):
    """Puts the content inside the highest level of svg (so you use this only to make the final svg file)

    Args:
        strPaths (str): svg content like paths and groups
        viewBoxMinimum (list, optional): x,y smallest positions found withint the svg content. Defaults to [0,0].
        viewBoxMaximum (list, optional): x,y biggest positions found withint the svg content. Defaults to [100,100].

    Returns:
        str: svg html element to save into a file
    """
    base = f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{viewBoxMinimum[0]-10},{viewBoxMinimum[1]-10},{viewBoxMaximum[0]+20},{viewBoxMaximum[1]+20}" >\n {strPaths} </svg>\n'
    return base

def gWrapper(strPaths,transform=[0,0],className=""):
    """Puts some svg content inside a svg group element\n
    We use this to organise the panels and layout them without changing their actual vertices values

    Args:
        strPaths (str): svg content like path
        translate (list, optional): x,y of the tranform position. Defaults to [0,0].
        className (str, optional): Name of the html class for the group. Defaults to "".

    Returns:
        str: svg group with the content inside
    """
    #final = "\n".join(strPaths)
    translate = f"translate({transform[0]},{transform[1]})"
    transform = (f'transform="{translate}"',"")[transform==[0,0]]

    #Basic Shape
    base = f'<g class="{className}" {transform} >\n {strPaths} </g>\n'
    return base


# CURVES AND COORDINATES __________________________________________________________________________

def pointOnQuadCurve(start,middle,end,t):
    """Find the position of a point placed on a Quadratic Bezier Curve at t% (lerp)

    Args:
        start (array): First Point [x,y]
        end (array): Second point [x,y]
        t (float): value between 0 and 1, 0.5 would give the middle of the curve

    Returns :
        x,y position of the sampled point
    """
    x = (1 - t) * (1 - t) * start[0] + (2 - 2 * t) * t * middle[0] + t * t * end[0]
    y = (1 - t) * (1 - t) * start[1] + (2 - 2 * t) * t * middle[1] + t * t * end[1]

    return x,y

def pointOnLine(start,end,t):
    """Find the position of a point placed on a line at t% (lerp)

    Args:
        start (array): First Point [x,y]
        end (array): Second point [x,y]
        t (float): value between 0 and 1, 0.5 would give the middle of the line

    Returns :
        x,y position of the sampled point
    """
    x = (1 - t) * start[0] + t * end[0]
    y = (1 - t) * start[1] + t * end[1]
    # x = (1 - t) * start.x + t * end.x
    # y = (1 - t) * start.y + t * end.y
    return x, y

def pointOnCubicCurve(start, b1, b2, end, t):
    """Find the position of a point placed on a Cubic Bezier Curve at t% (lerp)

    Args:
        start (tuple): (x,y) start position
        b1 (tuple): (x,y) first cubic bezier handle
        b2 (tuple): (x,y) second cubic bezier handle
        end (tuple): (x,y) last cubic bezier handle
        t (float): lerp amount (between 0 and 1)

    Returns:
        tuple: (x,y) of a point at `t` amount on the cubic curve
    """
    x = (1.0-t)**3 * start[0] + 3*(1.0-t)**2 * t * b1[0] + 3*(1.0-t)* t**2 * b2[0] + t**3 * end[0]
    y = (1.0-t)**3 * start[1] + 3*(1.0-t)**2 * t * b1[1] + 3*(1.0-t)* t**2 * b2[1] + t**3 * end[1]
    return (x,y,)

def control_to_abs_coord(start, end, control_scale):
    """ transform local position to world position (for curvatures values)
        Modified from GarmentPattern (MIT licence in /licences/GarmentPattern), https://github.com/maria-korosteleva/Garment-Pattern-Generator/tree/master
    """
    # modified from https://github.com/maria-korosteleva/Garment-Pattern-Generator
    start, end, control_scale = np.array(start), np.array(end), np.array(control_scale)

    edge = end - start
    edge_perp = np.array([-edge[1], edge[0]])

    control_start = start + control_scale[0] * edge
    control_point = control_start + control_scale[1] * edge_perp
    return control_point[0], control_point[1]

def control_to_relative_coord(start, end, control_point):
    """
    Derives relative (local) coordinates of Bezier control point given as
    a absolute (world) coordinates. FIXED VERSION
    Modified from GarmentPattern (MIT licence in /licences/GarmentPattern), https://github.com/maria-korosteleva/Garment-Pattern-Generator/tree/master

    """
    start, end, control_point = np.array(start), np.array(end), np.array(control_point)

    control_scale = [None, None]
    edge_vec = (end - start)
    edge_len = np.linalg.norm(abs(edge_vec))
    control_vec = control_point - start

    # X
    # project control_vec on edge_vec by dot product properties
    control_projected_len = edge_vec.dot(control_vec) / edge_len
    control_scale[0] = control_projected_len / edge_len
    # Y
    control_projected = edge_vec * control_scale[0]
    vert_comp = control_vec - control_projected
    control_scale[1] = np.linalg.norm(vert_comp) / edge_len
    # Distinguish left&right curvature
    control_scale[1] *= -np.sign(np.cross(control_vec, edge_vec))

    return round(control_scale[0],5), round(control_scale[1],5)

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate on the scale given by a to b, using t as the point on that scale.
    Examples
    --------
        50 == lerp(0, 100, 0.5)

        4.2 == lerp(1, 5, 0.8)
    """
    return (1 - t) * a + t * b

def get_intersect(a1, a2, b1, b2):
    """
    Returns the point of intersection of the lines passing through a2,a1 and b2,b1.
    a1: [x, y] a point on the first line
    a2: [x, y] another point on the first line
    b1: [x, y] a point on the second line
    b2: [x, y] another point on the second line
    https://stackoverflow.com/questions/3252194/numpy-and-line-intersections
    """
    s = np.vstack([a1,a2,b1,b2])        # s for stacked
    h = np.hstack((s, np.ones((4, 1)))) # h for homogeneous
    l1 = np.cross(h[0], h[1])           # get first line
    l2 = np.cross(h[2], h[3])           # get second line
    x, y, z = np.cross(l1, l2)          # point of intersection
    if z == 0:                          # lines are parallel
        return (float('inf'), float('inf'))
    return (x/z, y/z)

def get_distance_between(*points):
    """Returns the total distance between multiple points (all 2D points, BROKEN : or all 3D points)"""

    lens = set([len(x) for x in points])
    if lens=={2}:
        dst = sum(math.hypot(x1 - x2, y1 - y2) for (x1, y1), (x2, y2) in zip(points, points[1:]))
    elif lens=={3}:
        raise NotImplementedError("total distances between 3D points is broken")
        dst = sum([distance_3D(p1,p2) for p1,p2 in zip(points, points[:1])])
    else:
        raise ValueError("Multiple size of points given. Points must be either all 2D or all 3D")
    return dst

def distance_3D(point1, point2) -> float:
    """Calculate distance between two points in 3D."""

    return math.sqrt((point2[0] - point1[0]) ** 2 +
                     (point2[1] - point1[1]) ** 2 +
                     (point2[2] - point1[2]) ** 2)

# https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
def rotate(origin, point, angle):
    """Rotates the point around the origin by the angle

    Args:
        origin (tuple): [x,y] origin of the rotation
        point (tuple): [x,y] to change
        angle (float): angle value in degree

    Returns:
        x, y : [x,y] of rotated point
    """

    angle = math.radians(angle)

    qx = origin[0] + math.cos(angle) * (point[0] - origin[0]) - math.sin(angle) * (point[1] - origin[1])
    qy = origin[1] + math.sin(angle) * (point[0] - origin[0]) + math.cos(angle) * (point[1] - origin[1])

    return round(qx,4), round(qy,4)

# https://stackoverflow.com/questions/6802577/rotation-of-3d-vector
def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])

def rotate_euler(point,xyz_angle):
    """ Rotates a point given an euler rotation angle in degrees"""
    x,y,z = xyz_angle
    xm = rotation_matrix([1,0,0],math.radians(x))
    ym = rotation_matrix([0,1,0],math.radians(y))
    zm = rotation_matrix([0,0,1],math.radians(z))

    point = np.dot(xm, point)
    point = np.dot(ym, point)
    point = np.dot(zm, point)
    return list(point)



# https://stackoverflow.com/questions/6949722/reflection-of-a-point-over-a-line
def reflection_of_point(p_0, q_i, q_j):
    """Calculates reflection of a point across an edge

    Args:
        p_0 (ndarray): Inner point, (2,)
        q_i (ndarray): First vertex of the edge, (2,)
        q_j (ndarray): Second vertex of the edge, (2,)

    Returns:
        ndarray: Reflected point, (2,)
    """

    a = q_i[1] - q_j[1]
    b = q_j[0] - q_i[0]
    c = - (a * q_i[0] + b * q_i[1])

    p_k = (np.array([[b**2 - a**2, -2 * a * b],
                     [-2 * a * b, a**2 - b**2]]) @ p_0 - 2 * c * np.array([a, b])) / (a**2 + b**2)

    return p_k

# MISC ____________________________________________________________________________________________


def chunk_every(lst:list, chunk_size = 2, offset = 1):
    """Chunk a list into a list of chunk
    `[a,b,c]` -> `[(a,b), (b,c)]`

    Args:
        lst (list): list to chunk
        chunk_size (int, optional): size of the chunks. Defaults to 2.
        offset (int, optional): offset at every chunk. Defaults to 1.

    Returns:
        list: a new list made of chunks `[(chunk),(chunk)]`
    """
    l = [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size-offset)]
    l.pop()
    return l
