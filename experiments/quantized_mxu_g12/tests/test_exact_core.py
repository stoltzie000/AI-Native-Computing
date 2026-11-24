import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from exact_core import grouped_acc

class ExactCoreTests(unittest.TestCase):
    def test_zeros(self):
        r=grouped_acc([0]*64, [[1]*64], [0]*8, [[0]*2])
        self.assertEqual(r.accumulators,(0,))
        self.assertEqual(r.dropped_groups,0)
    def test_signed_and_scale(self):
        r=grouped_acc([-3]*64, [[7]*64,[-7]*64],[0]*8, [[16]*2,[16]*2])
        self.assertEqual(r.accumulators,(-1344,1344))
    def test_negative_shift_drops(self):
        r=grouped_acc([127]*64, [[127]*64], [10]*8, [[7]*2])
        self.assertEqual(r.accumulators,(0,))
        self.assertEqual(r.dropped_groups,8)
    def test_exact_shift_zero(self):
        r=grouped_acc([1]*64, [[1]*64],[9]*8, [[7]*2])
        self.assertEqual(r.accumulators,(64,))
    def test_48bit_intermediate(self):
        r=grouped_acc([127]*64, [[127]*64], [0]*8, [[0]*2])
        self.assertEqual(r.accumulators,(64*127*127*(1<<16),))
        self.assertGreater(r.accumulators[0], 2**31)
    def test_shape_rejected(self):
        with self.assertRaises(ValueError):grouped_acc([0]*63,[[0]*64],[0]*8,[[0]*2])
        with self.assertRaises(ValueError):grouped_acc([0]*64,[[0]*62],[0]*8,[[0]*2])
    def test_bad_range_rejected(self):
        with self.assertRaises(ValueError):grouped_acc([-129]*64,[[0]*64],[0]*8,[[0]*2])
        with self.assertRaises(ValueError):grouped_acc([0]*64,[[0]*64],[40]*8,[[0]*2])
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):grouped_acc([True]*64,[[0]*64],[0]*8,[[0]*2])
if __name__=='__main__':unittest.main()
