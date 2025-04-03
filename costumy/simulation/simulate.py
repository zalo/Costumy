# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
""" 
Script executed within blender to import a body and a pattern cache (pkle)
Will simulate and export an obj
args in order :
body       : obj file to simulate the cloth on (smpl mesh)
mesh_cache : filepath where the cache is (made by costumy.simulation.prepare)
output_path: filepath where the obj will be saved
"""

# Script within blender
import sys
import pickle
import warnings
from pathlib import Path
import bpy

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



# Call this script in a subprocess if you want to make sure nothing will change in the current scene

def simulate_cloth(collider, mesh_for_sim, output_path=None, bake=True, convert_to_mesh=True, place_on_origin=True, angle_based_uv=True) -> bpy.types.Object:
    """Uses a collider and a mesh_for_sim (made from costumy.simulation.prepare) to simulate a Pattern into a garment.
    
    You need to link the output to the current scene collection because it duplicates the collider and operates in a temporary scene
    
    Args:
        collider (bpy.types.Object|str|Path): A path to a mesh or a blender object on which the pattern will drape.
        mesh_for_sim (dict|str|Path): A dict or a fp to a pickled dict  with {vertices,edges,faces,stitches} for blender
        output_path (str|Path, optional): When provided export an obj file to the path. Defaults to None.
        bake (bool, optional): Bake the cloth simulation. Defaults to True.
        convert_to_mesh (bool, optional): Apply modifiers (cloth,weld) once simulation finished. Defaults to True.
        place_on_origin (bool, optional): If convert_to_mesh is true, recenter the mesh at 0,0,0 . Defaults to True.
        angle_based_uv (bool, optional): if true, create UVs using blender's angle based projection. Defaults to True.

    Returns:
        bpy.obj.types: 3D garment (not linked to the current bpy scene)
    """
    # Import OBJ Body
    if isinstance(collider,(str,Path,)):
        collider = import_mesh(collider)

    # Setup a new temporary scene
    bpy.ops.scene.new(type="NEW")
    temp_scene = bpy.context.scene
    temp_scene.name = "costumy_temp"
    temp_scene_collection = bpy.context.collection

    # Set frame to 0
    temp_scene.frame_set(0)
    temp_scene.frame_end = 60

    # Add to scene
    
    # scale a duplicated version to have better cloth sim
    if isinstance(collider,bpy.types.Object):
        temp_scene_collection.objects.link(collider)

        collider.select_set(True)
        bpy.context.view_layer.objects.active = collider

        bpy.ops.object.duplicate()
        collider = bpy.context.active_object
        
        collider.scale = [100,100,100]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
        # Smooth
        for poly in collider.data.polygons:
            poly.use_smooth = True

        # Add collision to body
        collider.modifiers.new(name="collision", type="COLLISION")
    else:
        warnings.warn("Collider is not an object, simulating garment without one (which is not going to make good results)")
    # Add cloth/garment/pattern to scene

    # Already an obj
    if isinstance(mesh_for_sim,bpy.types.Object):
        obj = mesh_for_sim
    else:
        # A pickle file
        if isinstance(mesh_for_sim,(str,Path,)):
            with open(mesh_for_sim, 'rb') as handle:
                mesh_dic = pickle.load(handle)

        # A dict
        elif isinstance(mesh_for_sim,dict):
            mesh_dic = mesh_for_sim
        
        mesh = bpy.data.meshes.new("Garment")
        obj = bpy.data.objects.new( "Garment", mesh)
        stitches = mesh_dic.pop("stitches")

        # Create mesh from dict
        mesh.from_pydata(**mesh_dic)

        # Create vertex group for vertices touching a stitch
        stitches_group = obj.vertex_groups.new( name = 'stitches' )
        stitches_group.add([int(x[0]) for x in stitches]+[int(x[1]) for x in stitches], 1, 'REPLACE' )
    
    
    # Link object to current scene collection
    temp_scene_collection.objects.link(obj)
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # delete floating vertices
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete_loose(use_verts=True, use_edges=False, use_faces=False)
    if angle_based_uv:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='ANGLE_BASED')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    # Shade smooth
    for poly in obj.data.polygons:
        poly.use_smooth = True

    # Add cloth
    cloth = obj.modifiers.new(name = "cloth", type="CLOTH")

    # Physics
    cloth.settings.mass = 1.2 #kg
    cloth.settings.time_scale = 2

    # Sewing options
    cloth.settings.use_sewing_springs = True
    cloth.settings.sewing_force_max = 38

    # Quality options
    cloth.settings.quality = 10
    cloth.collision_settings.collision_quality = 5
    cloth.collision_settings.use_self_collision = True

    # Stiffness
    cloth.settings.tension_stiffness = 20
    cloth.settings.compression_stiffness = 15
    cloth.settings.shear_stiffness = 15
    cloth.settings.bending_stiffness = 0.5

    # Damping 
    cloth.settings.tension_damping= 5
    cloth.settings.compression_damping= 5
    cloth.settings.shear_damping= 5
    cloth.settings.bending_damping = 0.5


    if bake:
        # Cache/bake simulation until specific frame number
        cloth.point_cache.frame_end = 55
        override = {'scene': temp_scene, 'active_object': obj, 'point_cache': cloth.point_cache}
        with bpy.context.temp_override(**override):
            bpy.ops.ptcache.free_bake()
            bpy.ops.ptcache.bake(bake=True)
            temp_scene.frame_set(52)
            #bpy.ops.object.modifier_apply(modifier=cloth.name)

    # Add Weld modifier to merge stitches
    weld = obj.modifiers.new(name = "weld", type="WELD")
    weld.merge_threshold = 1 # meters
    weld.vertex_group = stitches_group.name
    weld.mode = 'CONNECTED'
    weld.loose_edges = True # Only vertex that shares an edges

    for i in bpy.context.scene.objects:
        i.select_set(False)

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if convert_to_mesh:
        bpy.ops.object.modifier_apply(modifier=cloth.name)
        bpy.ops.object.modifier_apply(modifier=weld.name)
        if place_on_origin:
            bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
    if output_path is not None and output_path !="None":
        output_path=Path(output_path)
        if output_path.is_dir():
            output_path = output_path/"garment.obj"
        
        obj.select_set(True)

        bpy.ops.wm.obj_export(
            filepath=str(output_path),
            export_selected_objects=True,
            export_materials = False,
            apply_modifiers = True
        )
    # Delete scene
    bpy.context.window.scene = temp_scene
    bpy.ops.scene.delete()

    return obj

if __name__ == "__main__":
    output_path = Path(sys.argv[-1])
    mesh_cache = Path(sys.argv[-2])
    body_path = Path(sys.argv[-3])

    simulate_cloth(body_path, mesh_cache, output_path)
