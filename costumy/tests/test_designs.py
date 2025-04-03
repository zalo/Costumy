# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
import json
import unittest
import subprocess

from importlib import resources
from pathlib import Path

from costumy.designs import Aaron
from costumy.utils.functions import generate_freesewing_pattern

class TestSum(unittest.TestCase):
    def setUp(self):
        base = Path(str(resources.files("costumy").joinpath("")))
        self.mjs_path = (base/"node"/"generate_pattern.mjs")

        self.example_settings = {
            "measurements": {
                "biceps": 335,            "chest": 1080,
                "hips": 980,              "hpsToWaistBack": 550,
                "neck": 420,              "shoulderSlope": 16,
                "shoulderToShoulder": 465,"waistToHips": 145
            },"units":"metric","sa": 10}

    def test_NodeScriptExists(self):
        """Test if required ressources exists"""
        self.assertTrue(self.mjs_path.exists(), "Missing generate_pattern.mjs")
    
    def test_NodeCanCreatePattern(self):
        """Test if freesewing process returns an output starting like an svg and has a 'd' element """
        # Convert dic to json
        json_data = json.dumps(self.example_settings, indent=4)
        
        # Create the subprocess and pipe the JSON data to the Node.js script
        process = subprocess.Popen(['node', str(self.mjs_path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        process_out = process.communicate(input=json_data.encode())[0].decode()

        # Check if output looks like an svg with some shapes
        if (not process_out.startswith("<?xml")) and (not 'd="M' in process_out):
            self.fail("Invalid output from freesweewing/node.js (this test is a bit naive)")

    def test_AaronDesign(self):
        """Test if Aaron shirt can be created"""

        # From measurements_definitions
        a = Aaron.from_template_measures()
        generate_freesewing_pattern(a.measurements)
 
        # From local simple settings
        a = Aaron(measurements=self.example_settings["measurements"])
        generate_freesewing_pattern(a.measurements)
        
    def test_AaronClass(self):
        """Test for the Aaron Designs"""
        # Random styles and options
        a = Aaron.from_template_measures()
        a.new_pattern(a.random_style)
        a.new_pattern(a.default_options)

        # Random options may create unvalid patterns that cant be stitched
        #a.new_pattern(a.random_options)

        # Missing measurements
        incomplete_measurements = self.example_settings["measurements"].copy()
        incomplete_measurements.pop("biceps")

        # Test if error when missing measurements
        with self.assertRaises(RuntimeError):
            a = Aaron(incomplete_measurements)
            a.new_pattern(complete_missing_measures=False)

        # Test if warning when .pattern is None
        with self.assertWarns(UserWarning):
            a = Aaron.from_template_measures().pattern
        
        a = Aaron.from_template_measures()
        a.new_pattern()
        
        # Align pattern panels from class
        Aaron.align_panels(a.pattern,{"neck":[0,0,0],"bound_front":0,"bound_back":0})
        
        self.assertEqual(len(a.pattern.panels),2, f"Aaron is supposed to have 2 panels, not {len(a.pattern.panels)}")
        self.assertEqual(len(a.pattern.stitches),4, f"Aaron is supposed to have 4 stitches, not {len(a.pattern.stitches)}")


if __name__ == "__main__":
    unittest.main()
