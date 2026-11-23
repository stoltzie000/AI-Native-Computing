import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from memory_tiling import Tiling,estimate

class TilingTests(unittest.TestCase):
    def test_same_useful_weights_different_burst_count(self):
        a=estimate(Tiling(row_tile=4))
        b=estimate(Tiling(row_tile=64))
        self.assertEqual(a["useful_bytes"],b["useful_bytes"])
        self.assertEqual(a["useful_bytes"],128)
        self.assertEqual((a["requests"],b["requests"]),(32,2))
        self.assertEqual((a["transferred_bytes"],b["transferred_bytes"]),(2048,128))
    def test_utilization(self):
        self.assertAlmostEqual(estimate(Tiling(row_tile=4))["burst_utilization"],1/16)
        self.assertEqual(estimate(Tiling(row_tile=64))["burst_utilization"],1)
    def test_zero_activation_no_memory(self):
        x=estimate(Tiling(active_columns=0))
        self.assertEqual(x["requests"],0)
        self.assertEqual(x["transferred_bytes"],0)
        self.assertIsNone(x["burst_utilization"])
    def test_same_burst_larger_row_tiles(self):
        for rows in (4,8,16,32,64):
            x=estimate(Tiling(row_tile=rows))
            self.assertEqual(x["useful_bytes"],128)
            self.assertGreaterEqual(x["transferred_bytes"],x["useful_bytes"])
    def test_lower_bound_not_fixed_clock_comparison(self):
        a=estimate(Tiling(row_tile=4))
        b=estimate(Tiling(row_tile=64))
        self.assertGreater(a["idealized_total_cycles"],b["idealized_total_cycles"])
        self.assertTrue(b["idealized_total_cycles"]>0)
    def test_pipeline_not_slower_in_idealized_model(self):
        for rows in (4,8,16,32,64):
            a=estimate(Tiling(row_tile=rows,pipelined=True))
            b=estimate(Tiling(row_tile=rows,pipelined=False))
            self.assertLessEqual(a["idealized_total_cycles"],b["idealized_total_cycles"])
    def test_reject_conflicts(self):
        with self.assertRaises(ValueError):Tiling(total_rows=63,row_tile=4)
        with self.assertRaises(ValueError):Tiling(multiplier_lanes=5)
        with self.assertRaises(ValueError):Tiling(active_columns=5)
        with self.assertRaises(ValueError):Tiling(bytes_per_weight=0)
if __name__=="__main__":unittest.main()
