import random
import unittest
from sparse_reference import dense_reference,pack_exact_zero_blocks,sparse_exact_mv,demo

class BlockSparseTests(unittest.TestCase):
    def test_demo_exact(self):
        x=demo()
        self.assertTrue(x['exact_vector_equality'])
        self.assertEqual(x['zero_blocks'],3)
    def test_sparse_bytes(self):
        x=demo();self.assertEqual(x['dense_weight_bytes'],1024)
        self.assertEqual(x['packed_weight_and_metadata_bytes'],261)
    def test_exact_reduction(self):
        self.assertGreater(demo()['weight_traffic_saving_fraction'],.74)
    def test_all_zero(self):
        m=[[0.0]*8 for _ in range(8)]
        p=pack_exact_zero_blocks(m,4)
        self.assertEqual(p.skipped_blocks,4)
        self.assertEqual(sparse_exact_mv(p,[1]*8),[0.0]*8)
    def test_all_nonzero_not_worth_it(self):
        m=[[1.0]*8 for _ in range(8)]
        p=pack_exact_zero_blocks(m,4)
        self.assertLess(p.saved_fraction,0)
    def test_random_sparse_exact(self):
        rng=random.Random(17)
        for n in (8,16):
            b=4
            for _ in range(15):
                matrix=[[0.0]*n for _ in range(n)]
                for i in range(0,n,b):
                    for j in range(0,n,b):
                        if rng.random()<.6:continue
                        for a in range(i,i+b):
                            for c in range(j,j+b):matrix[a][c]=rng.randint(-10,10)
                vec=[rng.randint(-4,4) for _ in range(n)]
                p=pack_exact_zero_blocks(matrix,b)
                self.assertEqual(dense_reference(matrix,vec),sparse_exact_mv(p,vec))
    def test_nonrectangular(self):
        with self.assertRaises(ValueError):pack_exact_zero_blocks([[1,2],[1]],1)
    def test_unaligned(self):
        with self.assertRaises(ValueError):pack_exact_zero_blocks([[1]*7 for _ in range(8)],4)
    def test_invalid_vector(self):
        p=pack_exact_zero_blocks([[1]*8 for _ in range(8)],4)
        with self.assertRaises(ValueError):sparse_exact_mv(p,[1]*9)
    def test_nonfinite(self):
        with self.assertRaises(ValueError):pack_exact_zero_blocks([[float('nan')]*8 for _ in range(8)],4)
