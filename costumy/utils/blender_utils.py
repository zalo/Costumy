# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)

import bpy
from pathlib import Path
from math import radians
import math
def get_object(hint):
    """Get a single blender object from hint

    Args:
        hint (str|Object): Name of the object or object itself

    Raises:
        TypeError: if hint is not string or Object

    Returns:
        Object: Blender Object
    """

    if isinstance(hint, bpy.types.Object):
        return hint

    elif isinstance(hint,str):
        return bpy.data.objects[hint]
    
    else:
        raise TypeError("Hint should be a string or a bpy object")

def get_objects(hint):
    """Get a list of blender objects from hint

    Args:
        hint (str|Object|Collection|array): Name or Object (may be a list) or Collection

    Raises:
        TypeError: if hint is not correct type

    Returns:
        Object: list of Blender Objects
    """

    # if its a collection of object, get its children
    if isinstance(hint, bpy.types.Collection):
        return hint.objects[:] 
        #hint.all_objects to include objects in subcollection

    # if hint is a list of hints, return list of obj
    if isinstance(hint, (list,tuple,set) ):
        return [get_object(obj) for obj in hint]
    
    # if hint is not a list, return it inside a list
    else:
        return [get_object(hint)]

def select(objects):
    """select all objects in the scene, making the last one active"""
    objects = get_objects(objects)
    for obj in bpy.data.objects:
        if obj in objects:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        else:
            obj.select_set(False)
    return objects

def deselect_all_comp(target):
    """Unselect all Faces, Edges and vertices of current target (in Object Mode)"""
    select(target)
    # Deselect all
    for v in target.data.vertices:
        v.select = False
    for e in target.data.edges:
        e.select = False
    for f in target.data.polygons:
        f.select = False

def duplicate_evaluated_object(obj):
    """Duplicate an object with a mesh and apply modifiers to the duplicated version"""
    deg = bpy.context.evaluated_depsgraph_get()
    eval_mesh = obj.evaluated_get(deg).data.copy()
    new_obj = bpy.data.objects.new(obj.name + "_duplicated", eval_mesh)

    bpy.context.collection.objects.link(new_obj)

    for o in bpy.context.selected_objects:
        o.select_set(False)

    new_obj.matrix_world = obj.matrix_world
    new_obj.select_set(True)
    bpy.context.view_layer.objects.active = new_obj
    return new_obj


def simple_render(obj, output_path):
    # Input
    out_image = Path(output_path)

    C = bpy.context

    # #Clear current scene
    # for d in bpy.data.objects:
    #     bpy.data.objects.remove(d)

    # Add camera, centered and in front
    cam = bpy.data.cameras.new("RenderCam")
    cam.type = 'ORTHO'

    # Add camera as an object in the scene
    cam_obj = bpy.data.objects.new("RenderCam",cam)
    C.scene.collection.objects.link(cam_obj)
    cam_obj.location[1] = -1
    cam_obj.rotation_euler[0] = radians(90)

    # Change active camera to newly created one
    C.scene.camera = cam_obj


    # Import mesh

    #bpy.ops.object.shade_smooth()
    select(obj)
    bpy.ops.view3d.camera_to_view_selected()

    # Renderer options
    C.scene.render.engine = 'BLENDER_WORKBENCH'
    C.scene.display.shading.studio_light = 'basic.sl'
    C.scene.display.shading.show_object_outline = True

    # Render File options 
    C.scene.render.image_settings.color_mode = 'RGBA'
    C.scene.render.image_settings.compression = 50
    C.scene.render.film_transparent = True
    C.scene.render.resolution_x = 500*2
    C.scene.render.resolution_y = 500*2

    # render image
    C.scene.render.filepath = str(out_image)
    bpy.ops.render.render(write_still=True)



def draw_curve(coords, radius=0.05, color=(1,1,1,1,), name = "curve", cyclic = False):
    """Draws a curves in the scene at the given coords"""
    # make a new curve
    crv = bpy.data.curves.new('crv', 'CURVE')
    crv.dimensions = '3D'

    # make a new spline in that curve
    spline = crv.splines.new(type='NURBS')

    # a spline point for each point
    spline.points.add(len(coords)-1) # theres already one point by default

    # assign the point coordinates to the spline points
    for p, new_co in zip(spline.points, coords):
        p.co = (list(new_co) + [1.0]) # (add nurbs weight)

    # make a new object with the curve
    objc = bpy.data.objects.new(name, crv)

    # Set curve for pretty display
    objc.data.bevel_depth = radius
    objc.data.splines[0].use_cyclic_u = cyclic
    objc.color = color

    # Add to scene collection
    bpy.context.scene.collection.objects.link(objc)
    return objc


def import_mesh(path) -> bpy.types.Object:
    """Import an obj mesh into blender

    Args:
        path (str): Path to the obj file

    Returns:
        str: Name of the imported mesh within blender
    """
    # There are other functions to import an obj into blender
    # I found that using ops.wm.obj_import was faster
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path, "not found")
    
    if path.suffix==".obj":
        bpy.ops.wm.obj_import(filepath=str(path), up_axis = "Y", forward_axis = "NEGATIVE_Z") #pylint: disable=no-member

    elif path.suffix==".ply":
        bpy.ops.wm.ply_import(filepath=str(path),import_colors="SRGB") #pylint: disable=no-member
        # PLY Vertex Color attribute might be named Col instead of Color,
        # rename to Color for more consistent voxelize calls

    elif path.suffix==".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
        #return bpy.context.object
        
    else:
        raise NotImplementedError(path.suffix, " Blender might support the format, but was not implemented in this script")
    return bpy.data.objects[bpy.context.selected_objects[0].name]
