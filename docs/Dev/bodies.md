---
title: Implementing new bodies
---

!!! Warning
    This is an advanced feature and this page is pretty chaotic.  
    You will have more succes if you are familiar with Blender's API, Costumy's code and 3D meshes.

## Introduction

Costumy bodies are subclasses of `costumy.classes.body`. They are in not fleshed out in feature but provide an easier way to use Patterns and Designs. They are especially usefull for garment creation and simulation, serving as measurments source and collider.

Bodies are expected to always keep the same amount of vertices. The body shape should only change by moving existing vertices. In other words, the bodies should change with blendshapes/shapekeys/sclupting.

!!! NOTE
    You **dont have to** implement a new body subclass if you :

    - Have a mesh that cant or wont change morphology (doesnt have shapekeys)
    - Want to drape a pattern only once or twice on your own mesh
    
    The bodies subclasses are usefull when you have an automatic pipeline or a large set of characters

## How to Implement a new body

To add a 3D body in `costumy.bodies` you can do the following:

<div class="annotate" markdown>

1. Create a new [measurments definitons](measures.md) in `costumy/data/measurments_definitions/`
2. Add a python file in `costumy/bodies/`. Name it like you want, but keep it lowercase.
3. Use the template below within your new python file

    ```python title="mybod.py"

    import bpy
    from costumy.classes import Body
    import costumy.utils.blender_utils as bun

    # Name the class like your file but with a capital letter
    class Mybod(Body):
        
        def __init__(self, ) -> None:
            # You can add other args like the gender
            
            super().__init__("mybod.json") # (1)!
            
            self.object = None
            self.armature = None

        def setup(self):
            # The setup function should create a new object within the current blender scene
            # You might use an add-on, a .blend file, whatever you want
            # it must define self.object to object that holds the body mesh, and an armature if any

            # ex: Adding the body from a obj file
            self.object = bun.import_mesh("mybod.obj")
        
        # then you can add function you want
        # like a randomisation method

    ```

4. Add an import statement in `costumy/bodies/__init__.py` like `from .mybod import Mybod`

</div>

1. This should be the name of the `measurment definition` file made in step 1.

You did it !
