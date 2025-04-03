""" cmorph.py 
see https://mb-lab-community.github.io/MB-Lab.github.io/
and https://github.com/Upliner/CharMorph 
"""

import random
from math import radians
import bpy
from costumy.classes import Body
from costumy.data.addons import CharMorph as cmorph_addon
from costumy.utils import blender_utils as bun
# Char Morph is a fork of MB-Lab.
# It is faster and proposes some interesting features
# It also give two extra meshes, that are CC BY (but not implemented here)

#NOTE: The values were defined quickly
# Using a rig with IK and translation may give better control

# rotation value in Euler
jitter_limits = {
    # Joint Name    minimum       maximum         
    "spine.001" : [(-1,-1,-1),   (1,1,1)], #spine
    "spine.004" : [(-3,-3,-1),   (3,3,1)], #neck
    "spine.005" : [(-5, -3, -1), (5,3,1)], #head

    # Left side
    "shoulder.L": [(-5,-1,-5),   (5,1,5)],
    "upper_arm.L":[(-15,0,-30),  (20,0,5)],
    "forearm.L" : [(0,0,0),      (14,0,0)],
    "hand.L"    : [(-10,-30,-10),(10,10,10)],

    "thigh.L"   :[(-10,-1,-5),  (10,1,5)],
    "shin.L"    :[(0,0,0),      (0,0,5)],
    "foot.L"    :[(-10,-1,-5),  (10,1,5)],
}

# Right Side
temp = jitter_limits.copy()
for _key, _limits in temp.items():
    if _key.endswith(".L"):
        new_key = _key.removesuffix(".L")+".R"
        new_limits = [_limits[1], _limits[0]]
        jitter_limits[new_key] = new_limits


class Cmorph(Body):
    """
    Cmorph 
    Experimental class using mb-lab bodies (AGL3) with CharMorph Add-on

    see https://github.com/Upliner/CharMorph and https://mb-lab-community.github.io/MB-Lab.github.io/
    """
    def __init__(self,age=0,mass=0,tone=0, base_model="mb_male", measurement_definition = None) -> None:
        """Init a `Body` instance using [CharMorph](https://github.com/Upliner/CharMorph). Currently only supports 

        Args:
            age (int, optional):  Factor between -1.0 and 1.0 affecting age  related morphs. Defaults to 0.
            mass (int, optional): Factor between -1.0 and 1.0 affecting mass related morphs. Defaults to 0.
            tone (int, optional): Factor between -1.0 and 1.0 affecting tone related morphs. Defaults to 0.
            base_model (str, optional): 3D model name (mb_female, mb_male). Defaults to "mb_male".
            measurement_definition ((str|Path), optional): measurement definition json file name or abs path. Defaults to None.
        """

        if measurement_definition is None:
            measurement_definition = f"cmorph_{base_model}.json"
        super().__init__(measurement_definition)
        self.base_model = base_model
        self._age = age
        self._mass = mass
        self._tone = tone
        self.gender = {"mb_male":"male", "mb_female":"female"}[self.base_model]

    @property
    def height(self):
        #Cmorh will use the armature position first because it it more accurate
        if self.armature is None:
            raise RuntimeError("No armature found for this body, cant get the height")
        return self.armature.data.bones["spine.006"].tail_local.z

    @property
    def morphs(self) -> dict:
        """Current charmorph morphs"""
        if self.object is not None:
            bun.select(self.object)
            return cmorph_addon.file_io.morphs_to_data()["morphs"]


    @property
    def age(self):
        return self._age
    
    @age.setter
    def age(self,value):
        if self.object is not None:
            self._age = value
            bun.select(self.object)
            bpy.data.window_managers["WinMan"].charmorphs.meta_age = self._age
        else:
            print("Cant set the age, body's objet not found. Did you use setup() first ?")
    
    @property
    def tone(self):
        return self._tone
    
    @tone.setter
    def tone(self,value):
        if self.object is not None:
            self._tone = value
            bun.select(self.object)
            bpy.data.window_managers["WinMan"].charmorphs.meta_tone = self._tone
        else:
            print("Cant set the tone, body's objet not found. Did you use setup() first ?")
    

    @property
    def mass(self):
        return self._mass
    
    @mass.setter
    def mass(self,value):
        if self.object is not None:
            self._mass = value
            bun.select(self.object)
            bpy.data.window_managers["WinMan"].charmorphs.meta_mass = self._mass
        else:
            print("Cant set the mass, body's objet not found. Did you use setup() first ?")
    

    def setup(self):
        try:
            cmorph_addon.register()
        except ValueError:
            # Already registered
            pass

        # setup basic options
        wm = bpy.data.window_managers["WinMan"]
        wm.charmorph_ui.base_model        = self.base_model
        wm.charmorph_ui.import_cursor_z   = False

        # Create object
        bpy.ops.charmorph.import_char() # pylint: disable=no-member
        self.object = bpy.context.active_object
        bun.select(self.object)
        # setup "main key shapes"
        bpy.data.window_managers["WinMan"].charmorphs.meta_age = self._age
        bpy.data.window_managers["WinMan"].charmorphs.meta_mass = self._mass
        bpy.data.window_managers["WinMan"].charmorphs.meta_tone = self._tone

        # add simple bones (rig)
        # Gaming : Only the bones
        bpy.data.window_managers["WinMan"].charmorph_ui.rig = 'gaming'
        bpy.ops.charmorph.rig() # pylint: disable=no-member
        self.armature = self.object.modifiers["charmorph_rig"].object

    def randomize(self, strength=0.25):
        """Randomize the body morphology"""
        bpy.data.window_managers["WinMan"].charmorph_ui.randomize_strength = strength
        bpy.ops.charmorph.randomize() # pylint: disable=no-member

        # Body should be remesured
        self._measures = None
        self._references = None

    def clear_pose(self):
        """Set the pose bones rotation to 0"""
        for bone in self.armature.pose.bones:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = [0,0,0]

    def jitter_pose(self, strength=0.25) -> None:
        """Set the rotation of some predefined bones randomly within predefined range of value

        Args:
            strength (float, optional): How strong the rotation is. Defaults to 0.25.
        """
        for key, limits in jitter_limits.items():
            bone:bpy.types.PoseBone
            bone = self.armature.pose.bones[key]

            # Set rotation to euler
            bone.rotation_mode = "XYZ"
        
            #Assign random rotation within limits
            for i in range(3):
                r = radians(random.uniform(limits[0][i], limits[1][i])*strength)
                bone.rotation_euler[i] = r
