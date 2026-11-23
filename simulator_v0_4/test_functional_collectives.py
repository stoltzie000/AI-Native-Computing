import unittest,math,random
from functional_collectives import recursive_doubling_sum,demo

class Correctness(unittest.TestCase):
    def test_exact_integer_known_vector(self):
        v=[[1,2,3],[10,20,30],[100,200,300],[1000,2000,3000]]
        got,n=recursive_doubling_sum(v)
        self.assertEqual(got,[[1111,2222,3333]]*4)
        self.assertEqual(n,8)
        self.assertEqual(v[0],[1,2,3])

    def test_random_sizes_against_independent_sum(self):
        rng=random.Random(20261123)
        for nodes in (2,4,8,16):
            for width in (1,7,37):
                v=[[rng.uniform(-10,10) for _ in range(width)] for _ in range(nodes)]
                result,msgs=recursive_doubling_sum(v)
                expected=[math.fsum(v[j][i] for j in range(nodes)) for i in range(width)]
                self.assertEqual(msgs,nodes*int(math.log2(nodes)))
                for row in result:
                    for a,b in zip(row,expected):self.assertAlmostEqual(a,b,places=11)

    def test_reject_unsupported_layout(self):
        for vectors in ([], [[1]], [[1],[2],[3]], [[1,2],[2]], [[],[]]):
            with self.assertRaises(ValueError):recursive_doubling_sum(vectors)

    def test_deterministic_demonstration(self):
        self.assertEqual(demo(),demo())
        self.assertLess(demo()['max_absolute_error'],1e-12)
        self.assertEqual(demo()['messages'],24)

if __name__=='__main__':unittest.main()
