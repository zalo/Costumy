# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
import unittest
import os
from pathlib import Path
from importlib import resources

from costumy import classes as c
from costumy.utils import functions as fun

class TestSum(unittest.TestCase):
    def setUp(self):
        """setup"""
        base = Path(str(resources.files("costumy").joinpath("")))

        self.inputSVG = str(base/"data"/"examples"/"_doc_InkscapeSVG.svg")
        self.inputJSON = str(base/"data"/"examples"/"_doc_Specification.json")

    def test_RessourcesExists(self):
        """Test required files exists for tests"""
        self.assertTrue(os.path.exists(self.inputSVG),"Missing _doc_InkscapeSVG.svg")
        self.assertTrue(os.path.exists(self.inputJSON),"Missing _doc_Specification.json")

    def test_Cubic2Quad(self):
        """Test Cubic2Quad, ensure it returns the only correct value"""
        self.assertNotEqual(fun.Cubic2Quad("M 0 0 C 10 0 15 10 15 15 Z"),"", "Cubic2Quad failed and might be missing. Did you run npm install ?")
        self.assertEqual(fun.Cubic2Quad("M 0 0 C 10 0 15 10 15 15 Z"),"M 0 0 Q 15 0 15 15 L 0 0 Z", "Cubic2Quad failed simple cubic approximation")
        self.assertEqual(fun.Cubic2Quad("M 0 0 C 1000 0 1500 1000 1500 1500",tolerance=5000),"M 0 0 Q 1500 0 1500 1500 Z", "Cubic2Quad failed cubic approximation with tolerance")


    def test_PatternCreation(self):
        """Test pattern creation as svg and json, from file and str"""
        svg = """<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="-10,-10,42.0,21.192" ><path id="PointAwayFromOrigin" d="M 0.0 1.0 L 1.0 1.0 L 0.5 0.0  L 0.0 1.0Z" stroke="gray" fill="gray" fill-opacity="0.1" stroke-width="0.5" /><path id="CurveAwayFromOrigin" d="M 0.0 1.1920000000000002 L 1.0 1.1920000000000002 L 1.0 0.19200000000000017 Q 0.5 -0.20799999999999974 0.0 0.19200000000000017   L 0.0 1.1920000000000002Z" stroke="gray" fill="gray" fill-opacity="0.1" stroke-width="0.5" /></svg>"""
        json = '{"pattern":{"panels":{"PointAwayFromOrigin":{"translation":[0,0,0],"rotation":[0,0,0],"vertices":[[0,-0.5],[-0.5,0.5],[0.5,0.5]],"edges":[{"endpoints":[0,1]},{"endpoints":[1,2]},{"endpoints":[2,0]}]},"CurveAwayFromOrigin":{"translation":[0,0,0],"rotation":[0,0,0],"vertices":[[-0.5,-0.404],[-0.5,0.596],[0.5,0.596],[0.5,-0.404]],"edges":[{"endpoints":[0,1]},{"endpoints":[1,2]},{"endpoints":[2,3]},{"endpoints":[3,0],"curvature":[0.5,0.4]}]}},"stitches":[],"panel_order":["PointAwayFromOrigin","CurveAwayFromOrigin"]},"properties":{"curvature_coords":"relative","normalize_panel_translation":false,"units_in_meter":100,"normalized_edge_loops":true},"parameters":{},"parameter_order":[],"constraints":{},"constraint_order":[]}'
        
        try:
            c.Pattern()
            c.Pattern.from_test_svg()
        except Exception:
            self.fail("cant create a pattern from class examples")

        # From Files
        try:
            c.Pattern.from_json(self.inputJSON)
            c.Pattern.from_svg(self.inputSVG,cubic_to_quad=True)
        except Exception:
            self.fail("cant create a pattern from files")

        # From strings
        try:
            c.Pattern.from_svg(svg,cubic_to_quad=False)
            c.Pattern.from_json(json)
        except Exception:
            self.fail("cant create a pattern from strings")

    def test_PanelAttribute(self):
        """Test baisc panel creation and attribute"""
        pattern = c.Pattern().from_svg(self.inputSVG,cubic_to_quad=True)
        panel : c.Panel = pattern.panels[0]
        self.assertIsInstance(panel,c.Panel)
        
        # sun of panels center should be around 0
        self.assertAlmostEqual(panel.center[0] + panel.center[1], 0)

    def test_rounding(self):
        """Test if point can be rounded"""
        a = c.Point(10.564,10.22220)
        a = round(a)
        self.assertEqual(a.x,11,"Cant round point")

    def test_Point(self):
        """Test general Point operations"""
        a = c.Point(0,0)
        b = c.Point(1,2)
        
        # Get points
        self.assertEqual(a, a,"failed Point equality")
        self.assertEqual(a.x, a[0], "failed get item")
        self.assertEqual(b.x, b[0], "failed get item")
        self.assertEqual(b.y, b[1], "failed get item")
        self.assertEqual(sum([b.x,b.y]),sum([*b]),"failed point as *list")

        # Point operations
        self.assertEqual(a,       a,            "failed Point equality")
        self.assertEqual(-b,  c.Point(-1,-2),   "failed Point negative")
        self.assertEqual(a-b, c.Point(-1,-2),   "failed point substraction")
        self.assertEqual(a+b, c.Point(1,2),     "failed point addition")
        self.assertEqual(a*b, c.Point(0,0),     "failed point multiplication")
        
        # Against other type
        self.assertEqual(b*2, c.Point(2,4),     "failed point mutliplication with int")
        self.assertEqual(b/2, c.Point(0.5,1),   "failed point division with int")

        # Unpacking
        bx, by = b
        self.assertEqual(bx,b.x,   "failed point unpacking")
        self.assertEqual(by,b.y,   "failed point unpacking")

        # Reflection
        self.assertEqual(a,             a.reflection((0,0),(1,1)),   "failed point reflection")
        self.assertEqual(c.Point(-1,2), b.reflection((0,0),(0,1)),   "failed point reflection")
        self.assertEqual(c.Point(1,-2), b.reflection((0,0),(1,0)),   "failed point reflection")
        self.assertEqual(c.Point(2,1), b.reflection((0,0),(0.5,0.5)),"failed point reflection")
        
    def test_Line(self):
        """Test line creation and some generic functions"""
        
        # Basic methods of creation
        c.Line(c.Point(0,0), c.Point(10,0))
        c.Line((10,0), (20,0))
        c.Line([-10,100], [1.056, 10])

        # Must fail (too many value for a point)
        with self.assertRaises(ValueError):
            c.Line([0,0,0], [0])

        # Must fail (wrong type)
        with self.assertRaises(TypeError):
            c.Line(1,2,3,4)
        
        # Line <--> Curve
        aline = c.Line((0,0),(0,1))
        acurve = c.Curve((0,0),(0,1),(0,0))
        self.assertIsInstance(aline.as_curve(), c.Curve)
        self.assertIsInstance(acurve.as_line(), c.Line)

        # Sampling
        self.assertEqual(len(aline.sample(10)),11)
        self.assertEqual(len(acurve.sample(10)),11)
        
        # Endpoints swaps
        aline.endpoints = [19,20]
        self.assertEqual(19, aline.endpoints[0])

        aline.swap_endpoints()
        self.assertEqual(20, aline.endpoints[0])


if __name__ == "__main__":
    unittest.main()
