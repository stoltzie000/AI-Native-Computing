import math
import unittest
from physical_limits import min_sram_area_mm2, reticle_footprint_equivalents


class SRAMAreaTests(unittest.TestCase):
    def test_12gb_requires_more_than_two_reticles(self):
        self.assertGreater(reticle_footprint_equivalents(12), 2)
        self.assertLess(reticle_footprint_equivalents(12), 3)

    def test_48gb_four_times_12gb(self):
        self.assertAlmostEqual(min_sram_area_mm2(48), 4 * min_sram_area_mm2(12))

    def test_single_reticle_impossible_for_12gb_at_reference_density(self):
        self.assertGreater(min_sram_area_mm2(12), 858)

    def test_invalid_density_rejected(self):
        for val in (0, -1, float('nan'), float('inf')):
            with self.subTest(val=val), self.assertRaises(ValueError):
                min_sram_area_mm2(12, val)


if __name__ == '__main__':
    unittest.main()
