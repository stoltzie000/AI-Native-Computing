import random, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference import Config, evaluate, signed, tile_comparison

class ReferenceTests(unittest.TestCase):
    def test_full_workload(self):
        cfg = Config()
        w = [[(r * 7 + c) % 255 - 128 for c in range(4)] for r in range(64)]
        z = evaluate(w, [2, 0, -1, 0], cfg)
        self.assertEqual(z["requests"], 2)
        self.assertEqual(z["fetched_weights"], 128)
        self.assertEqual(z["skipped_weights"], 128)
        self.assertEqual(z["mac_cycles"], 32)
        self.assertEqual(z["conditional_burst_bytes"], 128)
        self.assertEqual(z["burst_utilization"], 1)
        self.assertEqual(z["sums"], [signed(row[0] * 2 - row[2], 32) for row in w])

    def test_two_lane(self):
        w = [[1, 2, 3, 4] for _ in range(64)]
        z = evaluate(w, [0, 3, 0, -1], Config(lanes=2))
        self.assertEqual(z["sums"], [2] * 64)
        self.assertEqual(z["mac_cycles"], 64)
        self.assertEqual(z["requests"], 2)

    def test_no_activations_and_undefined_utilization(self):
        z = evaluate([[1] * 4 for _ in range(64)], [0] * 4)
        self.assertEqual(z["sums"], [0] * 64)
        self.assertEqual(z["conditional_burst_bytes"], 0)
        self.assertIsNone(z["burst_utilization"])

    def test_burst_comparison_same_useful_data(self):
        a = tile_comparison()
        self.assertEqual([x["requests"] for x in a], [32, 16, 8, 4, 2])
        self.assertEqual([x["conditional_transfer_bytes"] for x in a], [2048,1024,512,256,128])
        self.assertEqual({x["useful_weight_bytes"] for x in a}, {128})
        self.assertEqual({x["active_compute_cycles"] for x in a}, {32})

    def test_data_width_16_memory(self):
        w = [[-5, 10] for _ in range(16)]
        z = evaluate(w, [1, 2], Config(rows=16, cols=2, lanes=4, data_bits=16, acc_bits=32))
        self.assertEqual(z["sums"], [15] * 16)
        self.assertEqual(z["useful_bytes"], 64)
        self.assertEqual(z["conditional_burst_bytes"], 128)

    def test_randomized_independent_dense_oracle(self):
        rng = random.Random(11012026)
        for rows in (4, 8, 16, 64):
            for lanes in (2, 4):
                for acc in (16, 32):
                    cfg = Config(rows=rows, lanes=lanes, acc_bits=acc)
                    for _ in range(90):
                        w = [[rng.randint(-128, 127) for _ in range(4)] for _ in range(rows)]
                        x = [rng.choice([0, 0, rng.randint(-128, 127)]) for _ in range(4)]
                        got = evaluate(w, x, cfg)
                        expected = [signed(sum(w[r][c] * x[c] for c in range(4)), acc) for r in range(rows)]
                        self.assertEqual(got["sums"], expected)
                        self.assertEqual(got["fetched_weights"] + got["skipped_weights"], rows*4)

    def test_invalid_geometry(self):
        for opts in ({"lanes":3}, {"rows":0}, {"data_bits":1}, {"acc_bits":12}, {"minimum_burst_bytes":0}):
            with self.subTest(opts=opts), self.assertRaises(ValueError):
                Config(**opts)
        with self.assertRaises(ValueError):
            evaluate([[0]*4 for _ in range(63)], [0]*4)

if __name__ == "__main__": unittest.main()
