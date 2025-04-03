# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""NOT A MODULE
Execute as a subprocess with 2 args :
path to a specification.json
output path for the cache created

Use the output cache (pickle) in blender with b_cloth.py
Its a dict of vertices, points and faces with stitches and transform applied
"""

# This script will crash often
# To get a result out of it, you must run it in a loop
# (a try; except will not work, you need a subprocess to open)
# This problem comes from triangulate (some iterations creates impossible numbers that crashes)

import math
import pickle
import sys
from triangle import triangulate
from costumy.utils.functions import rotate_euler
from costumy.classes import Pattern
from costumy.utils.functions import distance_3D


def create_mesh_cache(pattern:Pattern, output_path, nudge = 0.01):
    """Creates a dict of vertices, edges and faces for blender from a Pattern.
    DO NOT IMPORT THIS : The module that triangulates the interior of the mesh crashes in silence.
    You must run this whole script in a loop until the subrocess can read $$success$$ from print().

    Args:
        pattern (Pattern): GarmentPattern compatible pattern
        output_path (_type_): Where the pickle is written
    """

    pat = pattern
    # Subdivide Edges based on smallest edges in all the pattern
    # Behavior might change to get consistant results across patterns
    smallest_edge = float("inf")
    for p in pat.panels:
       smallest_edge = min(smallest_edge, min(e.length for e in p.edges))
    smallest_edge /=6
    #smallest_edge = max(smallest_edge,1)

    # Triangulate Panels and subdivide
    for p in pat.panels:
        
        segments = []
        vertices = []
        # A point every n distance
        for edge in p.edges:
            n = edge.length // smallest_edge
            #n+= n%2 # always even
            # edges.subpoints does not exists before this
            edge.subpoints = edge.sample(int(n))
            vertices += edge.subpoints
        segments += [(i, i + 1) for i in range(0, len(vertices) - 1)]
        shape = dict(vertices=vertices, segments=segments)

        # Triangulate (this is where the script silence itself sometime)
        
        # `a` is for "maximum area"
        max_area=round(0.5*smallest_edge*smallest_edge,5) + nudge
        p.topology = triangulate(shape, f"pqa{max_area}e")  # triangle based on pattern
        #p.topology = triangulate(shape, f"pqaei")  # triangle based on pattern
        # p.topology = triangulate(shape, "pqa20e")  # large triangles
        #p.topology = triangulate(shape, "pqa1e") # small triangles
        

        # Match triangulated vertices with edges subdivision
        tolerance = 0.001
        for e in p.edges:
            e.matches = []

            # Check if points are very close to an edge subdivion point
            for seg_index in p.topology["segments"]:
                seg_start, seg_end = p.topology["vertices"][seg_index]
                for subpoint in e.subpoints:
                    near_start = all([math.isclose(seg_start[x], subpoint[x], rel_tol=tolerance)for x in [0, 1]])
                    near_end   = all([math.isclose(seg_end[x], subpoint[x], rel_tol=tolerance)for x in [0, 1]])
                    #matching = None
                    # Assign topology point (as an index) to the edge (for stiching later)
                    if near_start and (seg_index[0] not in e.matches):
                        matching = seg_index[0]
                        e.matches.append(seg_index[0])
                    if near_end and (seg_index[1] not in e.matches):
                        matching = seg_index[1]
                        e.matches.append(seg_index[1])
                    #e.matches.append(matching)

            e.matches = list(set(e.matches))  # remove possible duplicate
            # e.matches -> [index to triangulated vertex]


    # vertices, edges, triangles are usefull
    vertices = []
    edges    = []
    faces    = []
    all_stitches = []
    for p in pat.panels:
        
        # Offset indices
        offset = len(vertices)
        for e in p.topology["edges"]: # (1, 2)
            edges.append((e[0]+offset, e[1]+offset))

        for triangle in p.topology["triangles"]: # (1, 2, 3)
            faces.append(tuple([indice+offset for indice in triangle]))

        for e in p.edges: # (1, 2, 3)
            e.matches = [indice+offset for indice in e.matches if indice]

        
        # transform 2D vertices to 3D, offset indexes
        for v in p.topology["vertices"]:
            # NOTE: Panel translation/rotation uses the GarmentPattern specs
            # Which mean they are supposed to be in maya's coordinate system

            # Maya    is X right, Y up, Z foward
            # Blender is X right, Y backward, Z Up
            # Maya -> Blender : (x,y,z) -> (x,z,-y)

            # Maya to Blender coordinate system
            x = p.translation[0]
            y = -p.translation[2]
            z = p.translation[1]

            # Maya to Blender coordinate system
            r = [p.rotation[0], p.rotation[2], p.rotation[1]]

            # Panel is facing your monitor
            v = [v[0],0,v[1]]

            # Rotate panel
            v = rotate_euler(v, r)
            
            # Position the panel
            v = (v[0]+x, v[1]+y, v[2]+z,)
            
            vertices.append(v)

    # Add stitches to edges
    # Otherwise some edges crosses in the stitches
        lowest_point = [*(min(p[i]*1 for p in vertices) for i in range(3))]
        p.lowest_point = lowest_point
        # lowest_point = [*(min(p[i]*1 for p in vertices) for i in range(3))]

    for stitch in pat.stitches:
        # [{panel:edge_#}, {panel:edge_#}]
        panel_A = pat.get_panel(stitch[0]["panel"])
        edge_A  = panel_A.edges[stitch[0]["edge"]]

        panel_B = pat.get_panel(stitch[1]["panel"])
        edge_B  = panel_B.edges[stitch[1]["edge"]]

        # Sort based on distance with smallest position known in the current panel
        a = sorted(edge_A.matches,key=lambda x: distance_3D(vertices[x],panel_A.lowest_point))
        b = sorted(edge_B.matches,key=lambda x: distance_3D(vertices[x],panel_B.lowest_point))
        

        # (Stitch # from panel A , Stitch # from panel B), based on their distance with 0,0,0
        sewing_edges = [(x,y) for x,y in zip(a,b)]
        edges+=sewing_edges
        all_stitches += sewing_edges

    # Data used by blender
    mesh_dic = {"vertices":vertices, "edges":edges, "faces":faces, "stitches":all_stitches}
    
    with open(output_path, 'wb') as handle:
        pickle.dump(mesh_dic, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # HACK: Because triangulate crashes in silence and kills the process
    # other script that needs this features calls the script in a loop (recursive)
    # The subprocess loop is ended whenever "$$success$$" is printed
    # (it was the only workaround that I found)

    print("$$success$$") #do not remove this line

if __name__ == "__main__":
    import sys
    n_attemps = int(sys.argv[-3])
    pat = Pattern().from_json(sys.argv[-2])
    outpat = sys.argv[-1]
    create_mesh_cache(pat,outpat,n_attemps*0.02)