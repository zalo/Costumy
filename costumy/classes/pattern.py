# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
"""
pattern.py

File with the Pattern class used to create 2D clothing patterns.
It's the core of costumy.
"""
import sys
import json
import warnings
import subprocess
import tempfile
import pickle

from pathlib import Path
from importlib import resources

from costumy.utils import functions as fun
from costumy.classes.panel import Panel

# Importing two optionnal module directly in the functions :
# from costumy.simulation.simulate import simulate_cloth
# import matplotlib.pyplot as plt

class _paths:
    base = Path(str(resources.files("costumy").joinpath("")))
    prepare_process = base/"simulation"/"prepare.py"


class Pattern:
    """Pattern
    This class is the representation of a clothing pattern, it groups `Panel` instances.
    Ex: A Tshirt pattern would be made of 2 panels (front and back).
    """
    def __init__(self) -> None:
        """Init a `Pattern` instance"""

        self.stitches = []
        """List of stitches, to be filled manually later in the json itself"""

        self.panels: list[Panel] = []
        """list of `Panel` instances within the pattern"""

        self.source = None
        """Experimental: Source of the pattern, either a Design, a string or a path"""

    #  FROM ______________________________________________________________________

    @classmethod
    def from_test_svg(cls):
        """Creates a `Pattern` with one Panel from an hardcoded SVG string.
        The panel is shaped as an arrow pointing toward the SVG's coordinate system origin (top left of screen).
        The panel has commun issue to test features like `unsplit_lines`.
        """
        _svg = """<?xml version="1.0" encoding="UTF-8"?><svg><path d="M 0,0 V 58.3 L 21.6,37.5 C 36.1,52.8 55.5,72.7 65.7,81.4 76,90 89.9,75.2 81.5,65.7 73,56.1 52.2,36.6 37.9,21.8 L 60.6,0 Z"/></svg>"""
        #d = "M 0,0 V 58.3 L 21.6,37.5 C 36.1,52.8 55.5,72.7 65.7,81.4 76,90 89.9,75.2 81.5,65.7 73,56.1 52.2,36.6 37.9,21.8 L 60.6,0 Z"
        pattern = Pattern.from_svg(_svg,cubic_to_quad=True,tolerance=50)
        return pattern

    @classmethod
    def from_svg(cls,svg, cubic_to_quad=False, tolerance = 10, remove_fake_cubic=False):
        """Creates a `Pattern` instance using a SVG.

        ```python
        pattern = Pattern.from_svg("shirt.svg")
        pattern.normalize_edge_order()

        # Visualize the pattern with normalized edges order
        pattern.as_plot()

        # Add stitches based on the normalized edges order
        pattern.add_stitch("front", 1, "back", 1)

        # Export the pannel and its stitches
        full_json = pattern.as_json()

        with open("nice_shirt.json", "w") as f:
            json.dump(full_json, f)

        ```

        Args:
            svg (str): path to svg file or svg as a string
            cubic_to_quad (bool, optional): If True, converts the values to absolute and approximate bezier curves using `functions.Cubic2Quad()`. Default to False.
            tolerance (float, optional): How aggressive the cubic_to_quad approximation is. A large value mean less curves. Defaults to 10.
            remove_fake_cubic (bool, optional): If true, replaces cubic curves with quadratic curves if it has no effect on the shape.

        Returns:
            Pattern : Pattern with panels made from svg
        """
        pattern = Pattern()

        for name, svg in fun.ImportSVG(svg).items():

            if remove_fake_cubic:
                svg = fun.ConvertFakeCubic(svg,tolerance)
            if cubic_to_quad:
                svg = fun.Cubic2Quad(svg, tolerance= tolerance)

            pattern.panels.append(Panel.from_svg(svg,name))

        return pattern

    @classmethod
    def from_json(cls, data):
        """Creates a `Pattern` instance from a specification.json (GarmentPattern)

        Args:
            data (str|Path|dict): filepath or json data as a string or a dict

        Returns:
            Pattern: Pattern with panels and properties from a json.

        Raises:
            ValueError: Wrong filepath or invalid json string
        """
        if isinstance(data,(str,Path,)):
            fp = Path(data)
            if fp.exists():
                with open(fp,"r",encoding="utf8") as f:
                    data = json.load(f)
            elif isinstance(data, str):
                data = json.loads(data)
        if not isinstance(data,dict):
            raise TypeError("Invalid input data. Must be a json filepath, json string or dict")

        pattern = cls()

        isRelative = data["properties"]["curvature_coords"]=="relative"
        pattern.stitches = data["pattern"]["stitches"]

        for panel_name, panel_data in data["pattern"]["panels"].items():
            p = Panel.from_json(panel_data, panel_name, curvature_is_relative=isRelative)

            pattern.panels.append(p)

        return pattern

    #  AS ______________________________________________________________________
    def as_json(self, curvature_is_relative=True) -> dict:
        """Returns the pattern as a dict. Includes the panels, stitches and some properties.

        The output can be used with `Pattern.from_json()`.

        The dict is compatible with GarmentPattern specification.json (v1)

        Args:
            curvature_is_relative (bool, optional): When true, the curvature is converted into relative scale. Defaults to True.

        Returns:
            dict: Pattern as a dict
        """
        #if serialize_stitches:
        #    stitches = self.serialized_stitches
        #else:
        #    stitches = self.stitches

        panels = {
            "panels"    : {p.name:p.as_json(curvature_is_relative) for p in self.panels},
            "stitches"  : self.stitches,
            "panel_order": self.panel_order
        }

        # NOTE: Hardcoded values for now cause the properties only matters for GarmentPattern
        # Used to have a Specification class, but now importing a json wont preserve it's property

        dic = {
            "pattern" : panels,

            # Properties does not affect costumy
            # but will affect GarmentPattern scripts
            "properties":
            {
                "curvature_coords": ["absolute","relative"][curvature_is_relative], # relative if true
                "normalize_panel_translation": False,
                "units_in_meter": 100,
                "normalized_edge_loops": True
            },

            # Leave those empty, used by GarmentPatternGenerator only
            "parameters":{},
            "parameter_order":[],
            "constraints":{},
            "constraint_order":[]

            }


        return dic

    def as_svg(self, full_svg=True, minimal= False) -> str:
        """Returns the pattern as a SVG. Panels are side by side and labeled.
        The stitches and transforms are not inclued within the SVG content.

        Args:
            full_svg (bool, optional): If True, returns a complete svg, ready to save as a file. Defaults to True.
            minimal (bool, optional): If True, keeps only the panel outline (no text or href element). Defaults to False.

        Returns:
            str: svg file as text or svg group element.
        """

        svgstr= []
        position = 0
        max_height = 0

        for panel in self.panels:

            panel_svg = panel.as_svg(full_svg=False, minimal=minimal)
            svg_group = fun.gWrapper(panel_svg, (position,0), "Panel")
            svgstr.append(svg_group)

            position += panel.width + 10
            max_height = max(max_height, panel.height)

        final = "".join(svgstr)

        if full_svg:
            svg = fun.svgWrapper(final,viewBoxMaximum=(position, max_height))
        else:
            svg = fun.gWrapper(final, className="Pattern")

        return svg

    def as_svg_debug(self, full_svg=True, show_curve_points=False, freesewing_id=False) -> str:
        """Returns a detailed representation of the pattern as an SVG. Panels are side by side and labeled.
        The stitches and transforms are not inclued within the SVG content.

        Args:
            full_svg (bool, optional): When true, returns a complete svg (as a string). When false, only returns a svg `group`. Defaults to True.
            show_curve_points (bool, optional): if True, draw control points of quadratic curves. Defaults to False.
            freesewing_id (bool, optional): If True, displays the freesewing ID on edges if available. Defaults to False.

        Returns:
            str: debug svg or content to put inside an svg
        """
        svgstr= []
        position = 0
        maxHeight = 0

        for panel in self.panels:

            shape = panel.as_svg_debug(show_curve_points=show_curve_points,freesewing_id=freesewing_id)
            group = fun.gWrapper(shape,(position,0),"DebugPanel")
            svgstr.append(group)

            position += panel.width+10
            maxHeight = max(maxHeight,panel.height)
        final = "".join(svgstr)
        if full_svg:
            svg = fun.svgWrapper(final,viewBoxMaximum=(position,maxHeight))
        else:
            svg = fun.gWrapper(final,className="Pattern")
        return svg

    def as_svg_stack(self, full_svg = True) -> str:
        """Experimental - Create a SVG of the panels in a Stacked version (all panels ontop of eachother)

        Args:
            full_svg (bool, optional): When true, returns a full svg, otherwise only the content like path. Defaults to True.

        Returns:
            str: Stacked svg or content to put inside an svg
        """
        svgstr= []

        max_height = 0
        max_width = 0
        for panel in self.panels:
            shape = panel.as_svg(minimal=True)
            group = fun.gWrapper(shape,(0,0),"DebugPanel")
            svgstr.append(group)
            max_height = max(max_height,panel.height)
            max_width  = max(max_height,panel.width)
        final = "".join(svgstr)
        if full_svg:
            svg = fun.svgWrapper(final,viewBoxMaximum=(max_width,max_height))
        else:
            svg = fun.gWrapper(final,className="Pattern")
        return svg

    def as_plot(self, filepath=None) -> None:
        """EXPERIMENTAL: Creates a matplotlib plot representing the pattern for debugging.

        filepath (str, optionnal): Filepath to save the plot. If None, displays the plot instead.

        """

        # This is a better solution than .as_svg_debug() because the graphs are in cartesian
        # So there is no need to flip and normalize everything all the time.

        # Matplotlib is only used here, so I import it just if this function is used
        try :
            import matplotlib.pyplot as plt # pylint: disable=import-error
        except ImportError:
            warnings.warn("Matplotlib is not installed")
            return

        n_panels = len(self.panels)
        for n, panel in enumerate(self.panels):
            if n_panels ==2:
                # side by side
                plt.subplot(1,2, n+1)
            else:
                # Rows and cols
                plt.subplot(2, (n_panels//2 + n_panels%2), n+1)

            plt.xticks([0])
            plt.yticks([0])
            #plt.figure(n+1)
            plt.grid(True)
            plt.gca().set_aspect('equal')
            i = 0
            plt.text(panel.center.x, panel.center.y, panel.name)
            for e in panel.edges:
                points = e.sample(5)
                plt.plot([p.x for p in points], [p.y for p in points],
                         color=fun.colors[i%len(fun.colors)],
                         linewidth=3)

                if e.freesewing_ID is not None:
                    plt.text(e.center.x, e.center.y, f"{i} ({e.freesewing_ID})")
                else:
                    plt.text(e.center.x, e.center.y, i)
                i+=1
            plt.tight_layout()

        # Save to a file or display plot
        if filepath is not None or "":
            filepath = Path(filepath)
            if filepath.is_dir():
                filepath = filepath / "pattern_as_plot.svg"
            plt.savefig(filepath, bbox_inches='tight')
        else:
            plt.show()

    def as_garment(self, collider, output_path=None, bake=True, convert_to_mesh=True, place_on_origin=True, angle_based_uv=True):
        """Creates a 3D garment using blender and the current pattern. It should have stitches and panels with translation.

        The collider should be in real scale (a human would be 1.6 meters, not 1600 meters)

        Args:
            collider (bpy.types.Object|str|Path): A path to a mesh or a blender object on which the pattern will drape.
            output_path (str|Path, optional): When provided export an obj file to the path. Defaults to None.
            bake (bool, optional): Bake the cloth simulation. Defaults to True.
            convert_to_mesh (bool, optional): Apply modifiers (cloth,weld) once simulation finished. Defaults to True.
            place_on_origin (bool, optional): If convert_to_mesh is true, recenter the mesh at 0,0,0 . Defaults to True.
            angle_based_uv (bool, optional): if true, create UVs before drapping the garment. Defaults to True.


        Returns:
            bpy.types.Object: 3D garment
        """
        # Import here only because Pattern does not use blender bpy expect for this
        from costumy.simulation.simulate import simulate_cloth

        # Create a temporary directory in temp files
        with tempfile.TemporaryDirectory(prefix="costumy_") as temp_dir:

            pickle_path  = Path(temp_dir)/"pattern.pkle"
            json_path  = Path(temp_dir)/"pattern.json"
            #output_path = Path(output_path).absolute().resolve()


            mesh_for_sim, n_attemps = self._make_mesh_for_sim(pickle_path, json_path)
            print(f"costumy: Mesh ready for sim (took {n_attemps} attemps)")
            garment = simulate_cloth(collider,
                                     mesh_for_sim,
                                     output_path=str(output_path),
                                     bake=bake,
                                     convert_to_mesh=convert_to_mesh,
                                     place_on_origin=place_on_origin,
                                     angle_based_uv=angle_based_uv
                                     )
            return garment


    # METHODS___________________________________________________________________

    def _make_mesh_for_sim(self, temp_pickle_path, temp_json_path, n_attemps = 0):
        # HACK triangulation in loop (silent crash from triangle.py)
        # This functions calls a separate python instance with a script
        # until the script prints a specific line
        # The script crashes in silence, without returning an error and cant be try:except
        n_attemps+=1
        if n_attemps>=40:
            raise RecursionError("Failed mesh conversion too many times (40 attemps)")

        # Write the pattern as a json to be reopenned by the other script
        # But just once, during the first attemp
        if n_attemps==1:
            with open(temp_json_path,"w", encoding="utf8") as f:
                json.dump(self.as_json(),f)

        cmd_args = [sys.executable,
                    str(_paths.prepare_process),
                    str(n_attemps),
                    str(temp_json_path),
                    str(temp_pickle_path)]

        with subprocess.Popen(cmd_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True) as process:
            process.poll()
            output = process.stdout.readline()
            if output:
                txt = output.strip().decode("utf-8").strip()
                # The process did not crash !
                # End the recursive calls by returning the pattern ready for sim
                if txt == "$$success$$":
                    with open(temp_pickle_path,"rb") as f:
                        mesh_for_sim = pickle.load(f)
                        return mesh_for_sim, n_attemps

        # Call the same function again (recursive)
        # Meaning the function will loop until it returns something else than itself
        return self._make_mesh_for_sim(temp_pickle_path, temp_json_path, n_attemps)

    def remove_panels(self,*args):
        """Remove specified panels from current pattern.panels and related stitches.

        Args:
            args (str|Panel): Panels instance or panel name(s) to remove from the pattern.

        """
        new_stitches = []

        selected_panels = []

        for a in args:
            # Is a panel from current pattern
            if isinstance(a, Panel):
                if a in self.panels:
                    selected_panels.append(a)

            # Is a panel name
            elif isinstance(a, str):
                selected_panels.append(self.get_panel(a))

            else :
                raise TypeError("args are either Panel istances or panel names")

        selected_panels_names = [x.name for x in selected_panels]

        # Only keep stitches with no mention of selected panels
        for stitch in self.stitches:
            if any([(x["panel"] in selected_panels_names) for x in stitch]):
                continue
            new_stitches.append(stitch)

            # if (not stitch[0]["panel"] in selected_panels_names ) and ( not stitch[1]["panel"] in selected_panels_names):
            #     new_stitches.append(stitch)
        for name in selected_panels_names:
            self.panels.pop(self.panel_order.index(name))

        self.stitches = new_stitches

    def get_panel(self,panel_name) -> Panel:
        """Return a panel based on its name"""
        return self.panels[self.panel_order.index(panel_name)]

    def normalize_edge_order(self):
        """Calls `Panel.normalize_edge_order` on self.panels"""
        for panel in self.panels:
            panel.normalize_edge_order()

    def align_panels(self, references):
        """Experimental: Set the panels translation and rotation using a dict of positions.

        WARNING:
            Only works if pattern was made from a design (`self.source` is a Design instance)

            It calls `self.source.align_panels(self, reference)`

        Args:
            references (dict): reference dict, most likely from `Body.references`
        """
        # NOTE:This is for convinence but it display a flaw in my code structure.
        # The Designs should be replaced with some kind of Pattern Factory
        # I cant import Design to check because it would make a circular import too.

        if (self.source is None) or isinstance(self.source,(str,Path)):
            print("This function only works on patterns made from a Design")
        self.source.align_panels(self,references)

    def add_stitch(self,panel_a:str,edge_a:int,panel_b:str,edge_b:int):
        """EXPERIMENTAL: add a stitch in `Pattern.stitches`.

        You should add a stitch at the very end of your pipeline, just before
        making a 3d garment. The stitches are very dependent on the edge index and panels name
        so any modification on them would most likely break the previous stitches.

        Args:
            panel_a (str): Name of the first panel
            edge_a (int): Edge index for panel_a to stitch with panel_b
            panel_b (str): Name of the second panel
            edge_b (int): Edge index of panel_b to stitch with panel_a
        """

        # NOTE: This is juste a quick implementation
        # I was working on a better one that would keep tracks of
        # stitches when changed and allowed direct references to edges

        # if isinstance(panel_a,str):
        #     panel_a = self.get_panel(panel_a)

        # if isinstance(panel_b,str):
        #     panel_b = self.get_panel(panel_b)

        # if isinstance(edge_a,(Line,Curve,)):
        #     edge_a = panel_a.edges.index(edge_a)

        # if isinstance(edge_b,(Line,Curve,)):
        #     edge_b = panel_b.edges.index(edge_a)

        stitch = [
            {"panel":panel_a, "edge":edge_a},
            {"panel":panel_b, "edge":edge_b},
            ]

        if stitch not in self.stitches:
            self.stitches.append(stitch)


    # @property
    # def serialized_stitches(self):

    #     stitches = []
    #     for s in self.stitches:
    #         # s = [{},{}]
    #         # check stitch_a, stitch_b
    #         stitch_for_json = []
    #         for i in s:
    #             panel = i["panel"]
    #             edge  = i["edge"]
    #             # if panel name, get panel
    #             if isinstance(panel,str):
    #                 panel = self.get_panel(panel)

    #             # Check if panel is in pattern
    #             if panel not in self.panels :
    #                 raise ValueError(f"Panel {panel} not found in current Pattern for the stitch {s}")

    #             panel_name = panel.name

    #             # If edge is an Line or Curve
    #             if isinstance(edge,(Line,Curve,)):
    #                 edge_index = panel.edges.index(edge)
    #             # If edge is an index, ensure it exists
    #             elif isinstance(edge,int):
    #                 edge_index = edge
    #                 edge = panel.edges[edge]
    #             else:
    #                 raise TypeError(f"Invalid edge type, must be an index, a curve or a line, not {type(edge)}")

    #             # Now we have a panel instance and an edge_index
    #             stitch_for_json.append({"panel":panel_name, "edge":edge_index})
    #         stitches.append(stitch_for_json)

    #     return stitches

    # PROPERTIES _________________________________________________________________
    @property
    def panel_order(self) -> list:
        """list of the pattern's panels names in order"""
        return [panel.name for panel in self.panels]

    def __getitem__(self, key) -> Panel:
        # Get a panel
        # with Pattern["name"] or Pattern[index]

        if isinstance(key,str):
            return self.get_panel(key)
        elif isinstance(key,int):
            return self.panels[key]


