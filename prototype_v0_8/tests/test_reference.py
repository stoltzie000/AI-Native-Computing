import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference import Config, evaluate, signed


class Tests(unittest.TestCase):
    def test_known_dense_output(self):
        m = [[1 + 4*r + c for c in range(4)] for r in range(4)]
        result = evaluate(m, [2, -1, 3, 0])
        self.assertEqual(result["sums"], [9, 25, 41, 57])
        self.assertEqual(result["requested_reads"], 12)
        self.assertEqual(result["skipped_reads"], 4)
        self.assertEqual(result["requested_coordinates"], [(r, c) for r in range(4) for c in (0,1,2)])

    def test_all_zero_activations_skip_all_reads(self):
        m = [[-128, 127, 1, -1]] * 4
        result = evaluate(m, [0, 0, 0, 0])
        self.assertEqual(result["sums"], [0]*4)
        self.assertEqual(result["requested_reads"], 0)
        self.assertEqual(result["skipped_reads"], 16)

    def test_zero_weights_do_not_count_as_activation_skip(self):
        m = [[0]*4 for _ in range(4)]
        result = evaluate(m, [1,2,3,4])
        self.assertEqual(result["requested_reads"], 16)

    def test_signed_and_overflow(self):
        m = [[-128]*4 for _ in range(4)]
        self.assertEqual(evaluate(m, [-128]*4, Config(accum_bits=16))["sums"], [-32768]*4)
        self.assertEqual(signed(65535,16), -1)

    def test_bad_input_and_config(self):
        with self.assertRaises(ValueError):
            evaluate([[0]*4]*4, [0,0])
        with self.assertRaises(ValueError):
            evaluate([[0]*4]*3, [0]*4)
        with self.assertRaises(ValueError):
            Config(size=0)
        with self.assertRaises(ValueError):
            Config(accum_bits=15)
        with self.assertRaises(ValueError):
            signed(True,8)

    def test_randomized_dense_oracle_and_request_coordinates(self):
        rng = random.Random(6022026)
        for n in (1,2,4,8):
            for trial in range(160):
                w = [[rng.randrange(-128,128) for _ in range(n)] for _ in range(n)]
                x = [rng.choice([0,0,0,rng.randrange(-128,128)]) for _ in range(n)]
                z = evaluate(w,x,Config(size=n,accum_bits=32))
                independent = [sum(w[r][c]*x[c] for c in range(n)) for r in range(n)]
                coords = [(r,c) for r in range(n) for c in range(n) if x[c]]
                self.assertEqual(z["sums"], independent)
                self.assertEqual(z["requested_coordinates"], coords)
                self.assertEqual(z["skipped_reads"]+z["requested_reads"], n*n)

    def test_savings_are_not_speedup_claims(self):
        for active in range(5):
            x = [1]*active+[0]*(4-active)
            z = evaluate([[r+c for c in range(4)] for r in range(4)],x)
            self.assertEqual(z["requested_reads"],4*active)
            self.assertEqual(z["skipped_reads"],16-4*active)


if __name__ == "__main__":
    unittest.main()
