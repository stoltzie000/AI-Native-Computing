"""Functional correctness vs independent serial matrix-vector reference."""
import unittest
import random
from functional_microkernel import demo, matvec_reference, ring_allreduce, sharded_matvec


class Microkernel(unittest.TestCase):
    def test_reference_identity(self):
        self.assertEqual(matvec_reference([[1,0],[0,1]],[5,-7]),[5,-7])

    def test_ring_one_node(self):
        r=ring_allreduce([[1.0,2.0]])
        self.assertEqual(r['vectors'],[[1,2]])
        self.assertEqual(r['messages'],0)

    def test_ring_four_nodes(self):
        partials=[[float(i+j) for j in range(8)] for i in range(4)]
        r=ring_allreduce(partials)
        expected=[sum(v[k] for v in partials) for k in range(8)]
        self.assertEqual(r['vectors'],[expected]*4)
        self.assertEqual(r['messages'],24)
        self.assertEqual(r['transmitted_bytes'],24*2*8)

    def test_multishard_against_serial(self):
        rng=random.Random(1024)
        for modules in (1,2,4,8):
            rows=8
            matrix=[[rng.uniform(-1,1) for _ in range(19)] for _ in range(rows)]
            vector=[rng.uniform(-1,1) for _ in range(19)]
            v=sharded_matvec(matrix,vector,modules)
            self.assertTrue(v['all_modules_equal'])
            self.assertLess(v['max_abs_error'],1e-12)

    def test_invalid_ring_width(self):
        with self.assertRaises(ValueError):ring_allreduce([[1],[2]])

    def test_invalid_matvec_shape(self):
        with self.assertRaises(ValueError):matvec_reference([[1,2],[3]],[1,1])

    def test_invalid_shard(self):
        with self.assertRaises(ValueError):sharded_matvec([[1.]]*3,[2.],2)

    def test_deterministic_demo(self):
        a,b=demo(),demo()
        self.assertEqual(a,b)
        self.assertEqual(a['modules'],4)
        self.assertEqual(a['max_abs_error'],0)


if __name__=='__main__':unittest.main()
