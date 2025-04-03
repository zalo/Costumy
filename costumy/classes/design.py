# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""
design.py
File with the Design base class.
"""
import json
import random
import difflib
import warnings
import importlib
from pathlib import Path

import svg.path as sv
from costumy.classes import Pattern, Point, Panel
from costumy.utils import functions as fun

class paths:
    """Paths used in this script"""

    base = Path(str(importlib.resources.files("costumy").joinpath("")))
    """Current directory: costumy"""

    measure_example = base / "data" / "measurements_sets" / "Ghislain.json"
    """Measurement used by default when a Design is made with `from_reference_measurements()`"""

    measurements_sets = list(Path(base/"data"/"measurements_sets").glob("*.json"))
    """List of measurements.json for completing missing measurements"""


# I think this could have been some kind of factory ? I'm not too familiar with the concept
class Design:
    """
    The Design class should be used as a parent class only.
    A Design is used to create patterns from body measurements and freesewing.
    Each different Design requires manual work to define stuff like stiches and cleaning process.

    This system could be much better, but this is just for a Proof of concept.
    """

    required_measurements:set = None
    """minimal required measures to get a pattern from freesewing"""

    optional_measurements:dict = None
    """optionnal measurements that affects the freesewing pattern"""

    options_range:dict = None
    """Range of options manually defined {"hipsEase":(0, 0.08,  0.2)} or {"name":(min, default, max)} """

    stitches:list = None
    """List of stitches based on freesewing ID and panels names [ (("front", -3), ("back", 3)),]"""

    rotation:dict = None
    """Dict of panels and their rotation values {"front":(0,0,0)}"""

    styles:dict = None
    """Dict of styles (presets of options). {"croptop":{"option_name":1.5}}"""

    panels_to_unfold = None
    """Dict of panels to unfold with the edge index {"front":0}"""

    def __init__(self, measurements:dict = None):
        """New Design instance"""

        self.measurements = measurements
        """Current set of measurement"""

        self._pattern:Pattern      = None
        """Private variable for self.Pattern"""

    @classmethod
    def from_template_measures(cls):
        """Makes a Design using template measurements"""
        with open(paths.measure_example,"r",encoding="utf8") as f:
            return cls(json.load(f)["measurements"])

    @property
    def missing_measurements(self) -> set:
        """list of measurments name that are required but missing from `self.measurements`"""
        # diff between measurements and required measurements
        return set(self.required_measurements) - set(self.measurements.keys())

    @property
    def isolated_measurments(self) -> dict:
        """Returns the measurments from `self.measurements` only if they are required.

        Helpfull to exclude optional measurements that may affect the output design
        (like the breast size)

        Raises:
            KeyError : Missing required measurements
        """
        try :
            return {key:self.measurements[key] for key in self.required_measurements}
        except KeyError as er:
            msg = f"Missing {(n:=len(self.missing_measurements))} required measurement{'s'[:n^1]}"
            raise KeyError(msg) from er

    @property
    def default_options(self) -> dict:
        """Default Options for pattern style"""
        return {k:self.options_range[k][1] for k in self.options_range}

    @property
    def random_options(self) -> dict:
        """Random options within handefined range of options. Usefull for new_pattern(). Can create really bad pattern still"""
        k = {}
        for option_name, option_range in self.options_range.items():
            k[option_name] = random.uniform(option_range[0],option_range[2])
        return k

    @property
    def random_style(self) -> str:
        """Random name from current styles"""
        return self.styles[random.choice(list(self.styles.keys()))]

    @property
    def pattern(self)->Pattern:
        """Last Pattern generated with self.new_pattern()"""
        if self._pattern is None:
            warnings.warn(f"You should use {self.__class__.__name__}.new_pattern() first")
        return self._pattern

    def complete_measurments(self, include_optional = True):
        """Fills the missing measurements from self.measurements using closest match from costumy/measurements_sets"""
        # Should it fill any missing measurements, or just the required ?
        # Be carefull cause a body might not have breast

        # Deduce missing measurments from example settings
        # Compare between know values and example set to find closest
        best_match = None
        lowest_difference = float("inf")
        for m_example_path in paths.measurements_sets:
            with open(m_example_path,"r",encoding="utf8") as f:
                m_example = json.load(f)["measurements"]
                current_difference = 0
                # check how close each measures are
                for known_m_name, known_m_value in self.measurements.items():
                    current_difference+= abs(m_example[known_m_name] - known_m_value)

                if current_difference < lowest_difference:
                    best_match = m_example
                    lowest_difference = current_difference
        # Fill missing measurements
        # NOTE: currently will only filling required measurements
        # Could include breasts as an option, or smth
        for missing in self.missing_measurements:
            if missing in self.optional_measurements:
                if not include_optional: continue
            self.measurements[missing] = best_match[missing]
        return self.measurements

    def new_pattern(self, options=None, tolerance=0.8, complete_missing_measures = True) -> Pattern:
        """Creates a new pattern based on self.measurements. Returns and defines `self._pattern`.\n
        Default behavior will create a pattern using default options and uses as many measures from self.measurements

        ```
        #Create a pattern of choosen style:
        self.new_pattern(options="croptop")

        #Create a pattern with a random style :
        self.new_pattern(options=self.random_style)

        #Create a pattern with random options (might make some ugly or impossible patterns):
        self.new_pattern(options=self.random_options)
        ```

        Args:
            options (dict|str, optional): set of options {str:float} or name of a style within self.styles.keys(). Defaults to None ("default").
            tolerance (float, optional): Tolerance for Cubic2Quad. High value = Less details, less curves. Defaults to 0.8.
            complete_missing_measures (bool, optional): When true, missing measures are replaced with closest known match. Defaults to True.

        Raises:
            RuntimeError: When measurements are missing and `complete_missing_measures` is False

        Returns:
            Pattern: 2D Pattern from Freesewing based on the options and measurements
        """
        # Use current measurements or complete them
        measures = self.measurements
        if self.missing_measurements:
            warnings.warn(f"{len(self.missing_measurements)} required measurements are missing.")
            if complete_missing_measures:
                print("complete_missing_measures: Using closest match for missing measurements")
                measures = self.complete_measurments()
            else:
                raise RuntimeError(f"The following measurements are missing but required:\n{self.missing_measurements}")

        # Options is a style name
        if isinstance(options,str):

            # Option was not found in styles
            if options not in self.styles:
                # Raise an error and display all styles or the closest style name
                helper = f"Available styles are {[k for k in self.styles.keys()]}"

                # Similar options
                close_matches = difflib.get_close_matches(options, list(self.styles.keys()))
                if len(close_matches)>0:
                    helper = f"Did you mean '{close_matches[0]}' ?"
                raise KeyError(f"Style '{options}' not found in {self.__class__.__name__}.styles. {helper}")
            else:
                options = self.styles.get(options)

        # No options given
        if options is None:
            options = self.default_options

        # Name of a style (option preset) given
        # Generate a freesewing SVG with the options
        svg = fun.generate_freesewing_pattern(measurements=measures, options=options)
        self._pattern = self._process_pattern(svg, tolerance=tolerance)
        self._map_stitches()
        self._pattern.source = self.__class__
        return self._pattern

    @classmethod
    def align_panels(cls,pattern:Pattern, references:dict) -> Pattern:
        """Define the `translation` and `rotation` of the `pattern.panels`
        based on the current design and a reference dict (see `Body.references`).

        ```
        # This will only work with subclasses the Design class
        pattern = Design.from_template_measures().new_pattern()

        pattern.align_panels(references)
        # or
        Design.align_panels(pattern, references)

        ```

        Args:
            pattern (Pattern): Pattern to modify the panels attributes. Technicaly the Pattern should match the current Design
            references (dict): Dict of references positions like {"neck":(0,0,1), "bound_front":0}. Most likely Body.references
        """
        # This should be implemented by the instances
        raise NotImplementedError()


    def _map_stitches(self):
        """Map stitches using the edges freesewing ID."""
        for stitch in self.stitches:
            a = self._pattern.get_panel(stitch[0][0])
            a_s = [e for e in a.edges if e.freesewing_ID == stitch[0][1]]

            b = self._pattern.get_panel(stitch[1][0])
            b_s = [e for e in b.edges if e.freesewing_ID == stitch[1][1]]


            if len(a_s) != len(b_s):
                raise RuntimeError(f"Stitch {stitch} requires equal amount of edges on both panels, not {len(a_s)} edges and {len(b_s)}")

            for a_edge, b_edge in zip(a_s,b_s):
                parsed_stitch = [
                    { "panel" :stitch[0][0] ,  "edge": a.edges.index(a_edge)},
                    { "panel" :stitch[1][0] ,  "edge": b.edges.index(b_edge)}
                ]
                self._pattern.stitches.append(parsed_stitch)

    def _process_pattern(self,svg, tolerance = 1):
        """ Cleanup the freesewing svg pattern, unfolding and fusing lines.
        Was tested only with Aaron.
        """
        
        f = fun.ImportFreeSewingSVG(svg)
        rescale = 0.1 # Freesewing mm -> Costumy cm
        pattern = Pattern()

        for name, svg in f.items():
            name = name.split(".")[-1]
            # scale svg for better cubic2quad results
            svg = fun.multiply_svg(svg, rescale)

            fs_svg = sv.parse_path(svg)

            svg = fun.ConvertFakeCubic(svg, tolerance) #try to remove
            svg_quad = fun.Cubic2Quad(svg, tolerance)

            # Make a panel with transformed svg
            panel = Panel.from_svg(svg_quad,name)

            # The panel instance is in cartesian space
            # The freesewing panel is in svg space

            # We offset and flip the panel to be in svg space
            # Otherwise we wont be able to deduce the freesewing ID's for stitches
            panel.scale([1,-1])
            panel.move(panel.offset_in_svg)         # center
            panel.straighten_curves()               # less curves
            panel.remake_vertices()                 # ensure good structure

            # find stitches based on freesewing
            fs_map = {}
            # e is an svg line from sv.parse lib
            for fs_id, e in enumerate(fs_svg):
                ep = e.point(0.5) # point at the center of e
                fs_map[fs_id] = [Point(e.start.real,e.start.imag), Point(ep.real,ep.imag), Point(e.end.real,e.end.imag)]

            # Find what edge belongs to what freesewing ID based on proximity
            for e in panel.edges:
                smallest_distance = float("inf")
                e.freesewing_ID = None

                # Find the freesewing edge
                # with the closest start point, middle point and end point
                for fs_id, fs_points in fs_map.items():
                    dist = 0
                    dist += fun.get_distance_between(e.p0,      fs_points[0])
                    dist += fun.get_distance_between(e.center,  fs_points[1])
                    dist += fun.get_distance_between(e.p1,      fs_points[2])

                    if dist<smallest_distance:
                        smallest_distance = dist
                        e.freesewing_ID = fs_id

            # Unfold panels |] -> [|]
            if panel.name in self.panels_to_unfold:
                panel.unfold(self.panels_to_unfold[panel.name])

            # We move and flip the panel back into cartesian space
            panel.move(panel.offset_in_cartesian)
            panel.scale([1,-1])
            panel.normalize_edge_order()
            panel.straighten_curves()              # less curves
            panel.unsplit_lines()                # fuse long straight lines
            panel.remake_vertices()                 # ensure good structure

            pattern.panels.append(panel)


        return pattern
