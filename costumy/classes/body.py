# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""body.py
File for the `Body` class.
"""

import copy
from pathlib import Path
from importlib import resources
import bpy
from costumy.measurer.measure import measure_with_measurements_definitions, get_references_with_measurements_definitions
from costumy.classes import Design, Pattern
import costumy.utils.blender_utils as bun

class _paths:
    base = Path(str(resources.files("costumy").joinpath("")))
    mdef = base/"data"/"measurements_definitions"

class Body:
    """
    The `Body` class is the base class for other bodies. It does not work directly.
    Bodies offers simple ways to get measurements and references point to drape garment ontop of.

    """

    def __init__(self, measure_definitions) -> None:
        """Init a `Body` class, meant to be use by class inerithing this one.
        The measure_definitions can be the name of a file located in `costumy/data/measurements_definitions` or a full path to an other json
        
        Args:
            measure_definitions (str|Path): name(str) of a measurements_definitions.json or its full Path

        """        

        # If file name, check costumy/data/measurements_definitions
        if isinstance(measure_definitions,str):
            measure_definitions = Path(_paths.mdef/measure_definitions)
        else:
            measure_definitions = Path(measure_definitions)
        
        self._measures_definitions = measure_definitions
        """Path to a measurement definition json"""

        if not self._measures_definitions.exists():
            raise FileNotFoundError(f"No measurement definition json found for {self._measures_definitions}")
        
        self._measures = {}
        self._references = {}

        self.object:bpy.types.Object = None
        """Body's blender Object"""
        self.armature:bpy.types.Object = None
        """Body's armature Object"""

        self.pattern:Pattern= None
        """Copy of the last Pattern used in body.dressup"""

        self.garment:bpy.types.Object = None
        """Garment created by body.dressup"""

    def setup(self) -> None:
        """Setup the body (Add the current body in the current bpy scene)"""
        pass
        #bpy.ops.wm.read_homefile()
        #raise NotImplementedError()

    @property
    def references(self) -> dict:
        """ Dict of various usefull points/positions in blender coordinates
        made from measurer and defined by the measurement_definition json.
        """
        # self._references should be reset to None whenever the body changes (like randomize)
        if not self._references:
            self._references = get_references_with_measurements_definitions(self.object,self._measures_definitions)
        return self._references

    @property
    def measures(self) -> dict:
        """Dict of Measures in mm defined by the measurement_definitions.json"""
        # self._measures should be reset to None whenever the body changes (like randomize)
        if not self._measures:
            self.armature.data.pose_position = 'REST'
            self._measures = measure_with_measurements_definitions(self.object,
                                                                   self._measures_definitions,
                                                                   duplicate_first=True,
                                                                   armature=self.armature
                                                                   )
            self.armature.data.pose_position = 'POSE'
        return self._measures

    @property
    def weight(self) -> float:
        """EXPERIMENTAL: Approximative weight in kg of `self.object` assuming its density is 1010kg/m³"""
        current_selection = bpy.context.selected_objects

        # Select object for bpy ops
        bun.select(self.object)

        # Add rigid body temporary
        bpy.ops.rigidbody.object_add()
        bpy.ops.rigidbody.mass_calculate(material='Custom', density=1010) # density in kg/m^3

        # save mass info and remove rigidbody
        bun.select(self.object)
        mass = self.object.rigid_body.mass
        bpy.ops.rigidbody.object_remove()

        # Reselect old selection
        bun.select(current_selection)
        return mass

    @property
    def height(self) -> float:
        """EXPERIMENTAL:
        Approximative height of `self.object` in meters.
        The body should be standing (a-pose or t-pose), not sitting/laying/bending

        NOTE:
            This may not be accurate because it depends on the subclass implementation.
            It also depends on the pose. Having legs a bit apart will change the height a bit.
            Sitting or bending will make the height really bad.

        NOTE:
            The height could be implemented in self.measure or self.references too, there might be a missmatch

        """
        #NOTE: Units are different from measurements (height in meters vs measures in mm)
        # Should fix or add a convention
        #Unlike measures, height is pretty fast to get, so recalculate it every time
        raise NotImplementedError("This body subclass does not support height yet")

    def dress_up(self,pattern:Pattern, drape=True) -> None:
        """EXPERIMENTAL: Make a garment from a pattern and place it on the current body. Usefull to render human with clothes

        makes a copy of the given pattern first, align it if its from a Design, and defines `self.pattern` and `self.garment`

        Args:
            pattern (Pattern): Pattern to make a garment
            drape (bool, optional): If false, garment is not simulated but still placed in 3D, great for quick debbuging. Defaults to True.
        """
        if self.object is None :
            raise RuntimeError(f"No object to dress up. Did you forget do to {self.__class__.__name__}.setup() ?")
        if pattern.source is not None:
            if issubclass(pattern.source, Design):
                # Design was made from a pattern, we can align it
                pattern.source.align_panels(pattern,self.references)

        self.pattern:Pattern = copy.deepcopy(pattern)
        if drape:
            self.garment = self.pattern.as_garment(self.object,convert_to_mesh=True,place_on_origin=False, bake=True)
            self.garment.scale = [0.01,0.01,0.01]
        else:
            self.garment = self.pattern.as_garment(self.object,convert_to_mesh=False,place_on_origin=False, bake=False)
            self.garment.scale = [0.01,0.01,0.01]
        bpy.context.collection.objects.link(self.garment)

    def render_preview(self, output_path) -> None:
        """EXPERIMENTAL: Quick front face and ortographic viewport render of the current body, with its garment if any"""
        for item in bpy.context.scene.objects:
            if item in (self.garment, self.object,):
                item.hide_render = False
                item.hide_viewport = False
            else:
                item.hide_render = True
                item.hide_viewport = True

        bun.simple_render(self.object, output_path)

    def as_obj(self,output_path) -> None:
        """Export the body mesh as an obj"""
        bun.select(self.object)
        bpy.ops.wm.obj_export(filepath=output_path, apply_modifiers=True,export_selected_objects=True)