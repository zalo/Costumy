# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
""" 
measure.py  
file with functions made to measure 3D bodies using a specific json structure (measurements_definitions.json)
"""
import bpy
import json
import math
import mathutils
from costumy.measurer.methods import measure_bisect, measure_length, get_vertex_in_group, measure_path
from costumy.utils.blender_utils import select

# FIXME hardcoded scales
# The model in 3D should be in real units. A human should be around 1.6 meters in blender (in height)
# The measures and references are scaled for two different reasons

# The measurements are converted into milimeters (mm) for FreeSewing (so multiplied by 1000).
# The references are scaled by 100 because blender simulation is harder to configure for small objects than big ones
# See https://blenderartists.org/t/blender-physics-real-world-scale-problems-solutions/1512780

def measure_with_measurements_definitions(target, measurements_definition_json, armature = None, duplicate_first = True):
    """Measures a mesh in blender using a measurements_definition.json file.

    Args:
        target (bpy.types.Object): Mesh to measure
        measurements_definition_json (str|Path): File path to the measurment.json file
        armature (bpy.types.Armature, optional): When None, measurements using bones to orient bisect try to use the target Armature. Defaults to None.
        duplicate_first (bool, optional): Duplicate the mesh before measuring and then deletes it. The bisect modifies the geometry. Defaults to True.

    Raises:
        TypeError: Invalid object to measure (must be a mesh)

    Returns:
        dict: Measurments in mm
    """
    measured = {}
    if target is None:
        raise TypeError("Target must be a mesh object")
    with open(measurements_definition_json,"r",encoding="utf8") as f:
        data = json.load(f)

    # Try to get an Armature if none
    if armature is None:
        try:
            armature = [x for x in target.modifiers if x.type=="ARMATURE"][0].object
        except:
            armature = None
    
    if duplicate_first:
        select(target)
        bpy.ops.object.duplicate()
        target = bpy.context.active_object

        # Removes and apply shape keys if they can be found
        if target.data.shape_keys:
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

    for key, measure_def in data["measures"].items():
        # Length
        if measure_def["method"] == "length":
            measure = measure_length(target,measure_def["vertices"])

        elif measure_def["method"] == "path":
            measure = measure_path(target,measure_def["vertices"])

        # Circumference (using bisect)
        elif measure_def["method"] == "bisect":

            # MASK
            isolated = []
            if (mask:=measure_def.get("mask")):
                for i in mask:
                    # Add the vertex from a group (like a skinning group)
                    if isinstance(i,str):
                        isolated +=(get_vertex_in_group(target,i, treshold=0.1))
                    # Add the vertex as an indice
                    elif isinstance(i,bpy.types.MeshVertex):
                        isolated.append(i)
            # POSITION & NORMAL
            verts = [target.data.vertices[x] for x in measure_def["vertices"]]

            plane_pos = verts[0].co
            if len(verts)==3:
                plane_n = mathutils.geometry.normal([x.co for x in verts])
            else:
                norm = measure_def.get("normal")
                if len(norm)==1 and isinstance(norm,list): norm=norm[0]
                try:
                    # "joint"
                    if isinstance(norm,str):
                        plane_n = armature.pose.bones[norm].vector

                    # ["joint1", "joint2"]
                    elif isinstance(norm,list) and len(norm)==2:
                        # normal based on joint direction to an other joint 

                        # Might need to change for head - head or smt like that. tail-tail works for smpl
                        plane_n = armature.pose.bones[norm[0]].tail - armature.pose.bones[norm[1]].tail
                    
                    # [0,0,1]
                    elif isinstance(norm,list):
                        plane_n = norm

                except:
                    print("Unable to get the armature or the bone of specified mesh")
                    continue
            measure = measure_bisect(target, plane_pos, plane_n, isolated)

        # Keep the value in a dic
        measured[key] = float(measure*1000)
    if duplicate_first:
        bpy.data.objects.remove(target)
    return measured


def get_references_with_measurements_definitions(target, measurements_definition_json):
    """Make a reference dict used to align patterns in 3D space. Includes the bounds of the mesh.
    Everything is in blender coordinate system.

    Args:
        target (bpy.types.Object): Mesh to get references from
        measurements_definition_json (path|str): filepath to a measurement_definition.json

    Returns:
        dict: positions and bounds of certain points in the mesh
    """
    
    with open(measurements_definition_json,"r",encoding="utf8") as f:
        data = json.load(f)

    references = {}
    # multiply by world matrix to get global coord, like a mesh scaled by its rig
    for key, value in data["references"].items():
        if value["method"] == "position":
            references[key]= list(target.data.vertices[value["vertices"][0]].co *100)
    
    # Find maximum and minimum panel positions
    # In front of the body, should be a negative value
    references["bound_front"]= round(min([x[1] for x in target.bound_box])*100,4)
    # behind the body, should be a positive value
    references["bound_back"] = round(max([x[1] for x in target.bound_box])*100,4)

    return references
        

def trace_measurements_definition(target, measurements_definitions_json):
    with open(measurements_definitions_json,"r") as f:
        data = json.load(f)
        
    obj = select(target)[0]
    bpy.ops.object.mode_set(mode = 'OBJECT')

    for key, value in data["measures"].items():
        vlist = value["vertices"]
        coords = []
        for v in vlist:
            coords.append([x for x in obj.data.vertices[v].co])
            obj.data.vertices[v].select = True

        # make a new curve
        crv = bpy.data.curves.new('crv', 'CURVE')
        crv.dimensions = '3D'

        # make a new spline in that curve
        spline = crv.splines.new(type='POLY')

        # a spline point for each point
        spline.points.add(len(coords)-1) # theres already one point by default

        # assign the point coordinates to the spline points
        for p, new_co in zip(spline.points, coords):
            p.co = (new_co + [1.0]) # (add nurbs weight)

        # make a new object with the curve
        objc = bpy.data.objects.new(key, crv)
        bpy.context.scene.collection.objects.link(objc)
        objc.show_in_front = True