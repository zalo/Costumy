# Costumy. Copyright (c) 2024 CDRIN. GNU GPL-3.0 (see LICENSE file)
 
import unittest
import importlib

class TestSum(unittest.TestCase):
    def setUp(self):
        pass

    def test_optional_deps(self):
        """Test optionnal dependencies for the Pattern class, but required for 3D related features"""
        self.assertIsNotNone(importlib.util.find_spec("bpy"))      #simulation.simulate
        self.assertIsNotNone(importlib.util.find_spec("triangle")) #simulation.prepare
    
    def test_garment_on_nothing(self):
        from costumy.bodies import SMPL
        from costumy.designs import Aaron
        b = SMPL()
        b.setup()
        a = Aaron.from_template_measures().new_pattern()
        b.dress_up(a,False)
        


if __name__ == "__main__":
    unittest.main()
