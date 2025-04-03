# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""
aaron.py   
file with the Aaron(Design) class (Freesewing sleevless shirt) 
https://freesewing.org/docs/designs/aaron
"""
from costumy.classes import Design, Pattern

# The idea is that every design might require some very specific, manually defined, operations
# That way if a specific design needs to align itself in a fancy way (like a skirt) it can overide the align_panels method

# this is just to avoid having a long Aaron class
class aaron_definitions:
    """Manually Predefined values used for Aaron design"""
    required_measurements = {
        "biceps",
        "chest",
        "hips",
        "hpsToWaistBack",
        "neck",
        "shoulderSlope",
        "shoulderToShoulder",
        "waistToHips",
        "waistToArmpit"
    }
    
    optional_measurements = {
        "highBust"
    }

    # min, default, max
    options = {
        # fit
        "hipsEase" :    (0, 0.08,  0.2),     
        "stretchFactor":(0, 0.05, 0.15), 
        
        # Style
        "armholeDrop"  :(0, 0.1, 0.75),
        "backlineBend" :(0.25, 0.5, 1),
        "chestEase"    :(0, 0.075, 0.2),
        "lengthBonus"  :(-0.2, 0.1, 0.6),
        "necklineBend" :(0.4, 1, 1),
        "necklineDrop" :(0, 0.2, 0.35),
        "shoulderStrapPlacement":(0.2, 0.4, 0.8),
        "shoulderStrapWidth":(0.1, 0.15, 0.4),
        #"armholeDepth":0.15,
    }

    styles = {
        "default":{},
        "croptop" : 
        {
            "lengthBonus": -0.13,
            "necklineBend": 0.62,
            "necklineDrop": 0.16,
            "shoulderStrapWidth": 0.1,
            "shoulderStrapPlacement": 0.45,
            "armholeDrop": 0.06,
            "stretchFactor": 0.005
        },

        "sport":{
            "lengthBonus": 0.25,
            "armholeDrop": 0.184,
            "backlineBend": 0.545,
            "chestEase": 0.089,
            "necklineBend": 0.4,
            "necklineDrop": 0.225,
            "shoulderStrapPlacement": 0.458,
            "shoulderStrapWidth": 0.234,
            "armholeDepth": 0.058,
            "hipsEase": 0.099,
            "stretchFactor": 0.05,
        }
    }


    # Stitching based on freesewing ID
    # Negative values are from unfolding the panels
    # Use pattern.as_plot to see the freesewingID (numbers in parenthese)
    stitches = [
        (("front", -3), ("back", 3)),  # left side  (0 -> 2)
        (("front", 3),  ("back", -3)), # right side (2 -> 0)
        (("front", 5),  ("back", -5)), # right shoulder
        (("front", -5), ("back", 5)),  # left shoulder
    ]

    rotation = {
        "front" : (0,0,0,), "back": (0,180,0)
    }

    # Unfold the panel "Front" at edge 0
    unfold = {"front" : 0, "back": 0}


class Aaron(Design):
    """
    Aaron is a child of the `Design` class.

    It can be used to create sleevless shirts using freesewing.
    https://freesewing.org/docs/designs/aaron

    ```python
    from costumy.designs import Aaron
    a = Aaron.from_template_measures() # or Aaron(measurements)
    pattern = a.new_pattern()
    ```

    """

    required_measurements = aaron_definitions.required_measurements
    optional_measurements = aaron_definitions.optional_measurements
    options_range         = aaron_definitions.options
    stitches              = aaron_definitions.stitches
    rotation              = aaron_definitions.rotation
    styles                = aaron_definitions.styles
    panels_to_unfold      = aaron_definitions.unfold

    @classmethod
    def align_panels(cls, pattern:Pattern, references):
        neck_front = (references["neck"][0], references["bound_front"], references["neck"][2])
        neck_back  = (references["neck"][0], references["bound_back"],  references["neck"][2])
        
        # Set Rotation of panels
        for p in pattern.panels:
            p.rotation = cls.rotation[p.name]

        p = pattern["front"]

        # Align neck with edge located at collar (point between -6 and 6)
        edges = [e for e in p.edges if e.freesewing_ID in (-6,6,)]

        if len(edges) == 1:
            # Only one edge represent the freseewing line #6 
            collar = edges[0].center
        else:
            # The freesewing line #6 is made of multiple edges
            # Use the lowest point in y since we expect the collar center to be low
            points = [e.p0 for e in edges] + [e.p1 for e in edges]
            points.sort(key=lambda point : point.y) 
            collar = points[0] #lowest in y

        pattern["front"].align_translation(collar, neck_front)
        pattern["back"].align_translation(collar, neck_back)
