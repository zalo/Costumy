# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""
DEPRICATED
## specification.py

A python class used to create json file that matches the structure of
https://github.com/maria-korosteleva/Garment-Pattern-Generator

A specification contains a signle `Pattern`.
Mostly a helper/wrapper.
"""



class Specification:
    """
    ## Specification
    DEPRICATED

    This class is a representation of a specification.json used by the garment-pattern tools
    It is the highest item (Specification has pattern, pattern has pannels)

    It does not support parameters and all of the settings yet, but is good enough to be used

    Args:
        pattern (`Pattern`): Pattern instance
        units_in_meter (int, optional): indicates how many units used for pattern specification fits in 1 meter. Defaults to 300.
        curvature_coords (str, optional): Describes the way cordinates of the curvature control points are specified in this template. ("relative" or "absolute").
    """
    def __init__(self,pattern,units_in_meter=100, curvature_coords="relative"):
        """init"""

        self.pattern = pattern
        """`Pattern` instance"""

        self.units_in_meter = units_in_meter
        """indicates how many units used for pattern specification fits in 1 meter. Defaults to 100."""

        self.curvature_coords = curvature_coords
        """Describes the way cordinates of the curvature control points are specified in this template.
        Allowed values:
        * "relative" -- Coordinates are given in local edge frame theating an edge as vector (1, 0)
        * "absolute" -- Coordinated are given in world frame, the same coordinate space as panel vertices.
        The chosen convention has to be used for all edge curvature specifications in the pattern!
        """

    def as_json(self):
        """Data representation of the specification as a json (This is the one you should save as a file)

        Returns:
            dic: the whole specification.json (pattern, properties, parameters, parameters order, constraints, constraints order)
        """
        relative = self.curvature_coords=="relative"

        dic = {
            "pattern" : self.pattern.as_json(relative),
            "properties":
            {
                "curvature_coords": self.curvature_coords,
                "normalize_panel_translation": False,
                "units_in_meter": self.units_in_meter,
                "normalized_edge_loops": True
            },
            "parameters":{},
            "parameter_order":[],
            "constraints":{},
            "constraint_order":[]

            }

        return dic
