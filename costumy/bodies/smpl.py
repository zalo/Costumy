import random
import bpy
from costumy.classes import Body
import costumy.utils.blender_utils as bun


class SMPL(Body):
    """SMPL (Restrictive licence, non commercial only)
    You must install the smpl_blender_addon and respect the licence to use
    
    https://smpl.is.tue.mpg.de/
    """
    
    def __init__(self, shapes = [0,0,0,0,0,0,0,0,0,0], gender="female") -> None:
        """Initialize an SMPL body. 
        SMPL is under a restrictive licence and must be installed manually.
        See docs/installation.md and https://smpl.is.tue.mpg.de/

        Args:
            shapes (list, optional): List of SMPL body parameters. Defaults to [0,0,0,0,0,0,0,0,0,0].
            gender (str, optional): "male" or "female". Defaults to "female".
        """
        super().__init__("smpl.json")
        self.object = None
        self.shapes = shapes
        self.armature = None
        self.gender = gender
    
    @classmethod
    def from_random_shapes(cls, gender="female"):
        """Init an SMPL body from random shapes between -2.5 and 2.5"""
        shapes = [random.uniform(-2.5,2.5) for x in range(0,10)]
        return SMPL(shapes=shapes,gender=gender)

    @property
    def height(self):
        if self.object is not None:
            bbox = self.object.bound_box
            h =  max([x[2] for x in bbox]) - min([x[2] for x in bbox]) 
            return round(h,8)

    def setup(self):
        # Activate the smpl if not already present
        super().setup()
        try:
            from costumy.data.addons.smpl_blender_addon import register
            register()
        except ValueError:
            # This Error is expected because an Add-on can only be registered once
            pass
        bpy.data.window_managers["WinMan"].smpl_tool.smpl_gender = self.gender
        bpy.ops.scene.smpl_add_gender()

        # Create SMPL with blender add-on
        body = bpy.context.active_object
        self.object = body

        # Set body shapes
        # Shape Keys (blendshapes, or the Tensor shape)
        shape_keys = body.data.shape_keys.key_blocks
        for i, shape in enumerate(self.shapes):
            #Must change min max range too or value is clamped
            #Skip the first shape (index 0)
            shape_keys[i+1].value =  shape
            shape_keys[i+1].slider_max = shape
            shape_keys[i+1].slider_min = shape
            
        # Update joints
        bpy.ops.object.smpl_snap_ground_plane()
        bpy.ops.object.smpl_update_joint_locations()

        # Scale the armature to match the pattern scale
        self.armature:bpy.types.Object = [x for x in self.object.modifiers if x.type=="ARMATURE"][0].object
