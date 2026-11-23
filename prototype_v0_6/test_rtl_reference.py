import random
import unittest
from rtl_reference import signed8,dense,step_reference,fixture

class ReferenceTests(unittest.TestCase):
    def test_fixture(self):self.assertEqual(fixture()['expected']['sums'],[9,25,41,57])
    def test_skip(self):
        r=step_reference([[0]*4 for _ in range(4)],[3,4,5,6],False)
        self.assertEqual(r['compute_cycles'],0)
        self.assertEqual(r['sums'],[0]*4)
    def test_reject_illegal_skip(self):
        with self.assertRaises(ValueError):step_reference([[1]*4 for _ in range(4)],[1]*4,False)
    def test_signed8(self):self.assertEqual(signed8(255),-1)
    def test_signed8_boundary(self):self.assertEqual(signed8(128),-128)
    def test_reject_out_of_range(self):
        with self.assertRaises(ValueError):signed8(256)
    def test_reject_bad_shape(self):
        with self.assertRaises(ValueError):dense([[1,2]],[1,2])
    def test_negative_weights(self):
        r=[[0]*4 for _ in range(4)]
        r[0][:2]=[-3,5]
        self.assertEqual(step_reference(r,[2,-1,3,0],True)['sums'][0],-11)
    def test_random_oracle(self):
        rng=random.Random(6)
        for _ in range(100):
            m=[[rng.randint(-128,127) for _ in range(4)] for _ in range(4)]
            x=[rng.randint(-128,127) for _ in range(4)]
            calc=step_reference(m,x,True)
            self.assertEqual(calc['sums'],[sum(m[i][j]*x[j] for j in range(4)) for i in range(4)])
            self.assertEqual(calc['multiplies'],16)
    def test_delay_table(self):
        r=fixture()['expected']
        self.assertEqual(r['controller_cycles_from_start_to_done'],18)
    def test_nonboolean_skip(self):
        with self.assertRaises(ValueError):step_reference([[0]*4 for _ in range(4)],[1]*4,0)
