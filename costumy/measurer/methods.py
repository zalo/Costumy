# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
""" 
methods.py
file with measurements techniques (like bisect) for measurer.py.
"""
import bpy
import math
from typing import List
from costumy.utils.functions import chunk_every

from costumy.utils import blender_utils as bun

def get_vertex_in_group(target,group_name,treshold=0.4)-> List[bpy.types.MeshVertex]:
    vg_idx = target.vertex_groups[group_name].index

    verts = []
    for v in target.data.vertices:
      for g in v.groups:
          if g.group == vg_idx:
              if g.weight>=treshold:
                  verts.append(v)
    return verts



def measure_length(target:bpy.types.Object, vertices:list) -> float:
    """Measure the position between mutliple vertices (list of index or vertex)"""
    positions = []
    for v in vertices:
        # Indices
        if isinstance(v, int):
            positions.append(target.data.vertices[v].co)
        elif isinstance(v, bpy.types.MeshVertex):
            positions.append(v.co)
        else:
            raise TypeError("Invalid type for vertice")

    total = 0
    for couple in chunk_every(positions):
        total+= math.dist(couple[0],couple[1])
    return total



def measure_path(target:bpy.types.Object, vertices:list) -> float:
    """Mesure a line following the object shape by connecting vertices with new edges, cutting the mesh faces.
    THE MESH WILL BE MODIFIED/CUTTED

    Args:
        obj (bpy.types.Object): Object to cut and measure
        vertices (list): List of vertice index or vertices

    Returns:
        float: Lenght of the new line created
    """
    # Must divide selection in pairs of 2
    # Because otherwise operator requires selection history (selection order)
    # Which requires bmesh

    if not len(vertices)==2:
        all_total = 0
        for i in chunk_every(vertices,2):
            all_total+=measure_path(target,i)
        return all_total
    
    #set active object
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bun.select(target)
    
    # Deselect all
    bun.deselect_all_comp(target)

    # Select vertices
    for v in vertices:
        # Indices
        if isinstance(v, int):
            target.data.vertices[v].select = True
        elif isinstance(v, bpy.types.MeshVertex):
            v.select = True
        else:
            raise TypeError("Invalid type for vertice")
        
    bpy.ops.object.mode_set(mode = 'OBJECT')

    #cut
    bpy.ops.object.mode_set(mode = 'EDIT')
    cut = bpy.ops.mesh.vert_connect_path()
    if "CANCELED" in cut: raise RuntimeError("Vertex path measurement failed")
    #measure
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    total = 0
    edges = [e for e in target.data.edges if e.select]
    verts = target.data.vertices
    
    for e in edges: 
        total += math.dist(verts[e.vertices[0]].co, verts[e.vertices[1]].co)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    return total


def measure_bisect(target:bpy.types.Object, position=(0,0,0), normal=(0,0,1), isolated_vertices=None) -> float:
    """Measure the perimiter of a mesh by cutting it with a plane.
    THE MESH WILL BE MODIFIED/CUTTED
    Use the isolated_vertices arg to restric the cut within those (ex: cut the chest without the arms)

    Args:
        obj (bpy.types.Object): Object to cut and measure
        position (tuple, optional): position of the slice. Defaults to (0,0,0).
        normal (tuple, optional): normal of the slice. Defaults to z up (0,0,1).
        isolated_vertices (list, optional): List of vertex index/vertex instance to isolate. Defaults to None.

    Returns:
        float: circumference
    """
    #set active object
    bpy.ops.object.mode_set(mode = 'OBJECT')
    #bpy.context.view_layer.objects.active = target
    bun.select(target)
    for v in target.data.vertices:
        if isolated_vertices is None or len(isolated_vertices)==0:
            v.select = True
            continue
        #if a mask is given, select only vertices of said mask
        v.select = (v.index in isolated_vertices) or (v in isolated_vertices)
    bpy.ops.object.mode_set(mode = 'OBJECT')

    #cut
    bpy.ops.object.mode_set(mode = 'EDIT')
    cut = bpy.ops.mesh.bisect(plane_co=position, plane_no=normal, use_fill=False, clear_inner=False, clear_outer=False, threshold=0, xstart=0, xend=0, ystart=0, yend=0, cursor=5)
    if "CANCELED" in cut: raise RuntimeError("Bisect measurement failed")
    #measure
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    total = 0
    edges = [e for e in target.data.edges if e.select]
    verts = target.data.vertices
    
    for e in edges: 
        total += math.dist(verts[e.vertices[0]].co, verts[e.vertices[1]].co)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    return total
