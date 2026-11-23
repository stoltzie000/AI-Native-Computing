import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reference import PEConfig,calculate,signed

class ReferenceTests(unittest.TestCase):
    def test_signed_bounds(self):
        self.assertEqual([signed(x,8) for x in (0,127,128,255,256,-1)],[0,127,-128,-1,0,-1])
    def test_known_fixture_for_all_lanes(self):
        rows=[list(range(i*4+1,i*4+5)) for i in range(4)]
        for lanes in (1,2,4,8,16):
            with self.subTest(lanes=lanes):
                z=calculate(rows,[2,-1,3,0],True,PEConfig(lanes=lanes))
                self.assertEqual(z["sums"],[9,25,41,57])
                self.assertEqual(z["issued_multiplies"],16)
                self.assertEqual(z["active_compute_cycles"],16//lanes)
                self.assertEqual(z["controller_cycles_including_start_done"],2+16//lanes)
    def test_skip_all_lanes(self):
        for lanes in (1,4,16):
            z=calculate([[0]*4 for _ in range(4)],[0,-1,127,-128],False,PEConfig(lanes=lanes))
            self.assertEqual(z["sums"],[0]*4)
            self.assertEqual(z["issued_multiplies"],0)
            self.assertEqual(z["controller_cycles_including_start_done"],2)
    def test_reject_false_zero_certificate(self):
        with self.assertRaises(ValueError):
            calculate([[0,0,0,1]]+[[0]*4 for _ in range(3)],[0]*4,False)
    def test_reject_geometry_and_bad_type(self):
        for lanes in (0,3,5,17,-1):
            with self.subTest(lanes=lanes),self.assertRaises(ValueError):PEConfig(lanes=lanes)
        with self.assertRaises(ValueError):PEConfig(acc_width=15)
        with self.assertRaises(ValueError):calculate([[0]*4 for _ in range(4)],[0]*4,1)
    def test_randomized_independent_dot_reference(self):
        rng=random.Random(322234)
        for n in (2,4,8):
            for lanes in (1,n,n*n):
                cfg=PEConfig(block_size=n,lanes=lanes,acc_width=16)
                for _ in range(60):
                    w=[[rng.randrange(-128,128) for _ in range(n)] for _ in range(n)]
                    x=[rng.randrange(-128,128) for _ in range(n)]
                    z=calculate(w,x,True,cfg)
                    expected=[signed(sum(a*b for a,b in zip(row,x)),16) for row in w]
                    self.assertEqual(z["sums"],expected)
                    self.assertEqual(z["issued_multiplies"],n*n)
                    self.assertEqual(z["active_compute_cycles"],n*n//lanes)
if __name__=="__main__":unittest.main()
