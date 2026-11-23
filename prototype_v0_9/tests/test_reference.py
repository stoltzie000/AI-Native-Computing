import random,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reference import Config,run_dense_and_column_fetch,transferred_bytes,signed

class Tests(unittest.TestCase):
    def test_dense(self):
        r=run_dense_and_column_fetch([[r*4+c+1 for c in range(4)] for r in range(4)],[2,-1,3,0])
        self.assertEqual(r["sums"],[9,25,41,57])
        self.assertEqual(r["requested_columns"],[0,1,2])
        self.assertEqual(r["column_requests"],3)
        self.assertEqual(r["elementwise_requests"],12)
        self.assertEqual(r["column_major"][:4],[1,5,9,13])
    def test_half_zero(self):
        r=run_dense_and_column_fetch([[1]*4 for _ in range(4)],[0,2,0,4])
        self.assertEqual(r["sums"],[6]*4)
        self.assertEqual((r["column_requests"],r["fetched_weights"],r["skipped_weights"]),(2,8,8))
    def test_all_zero_no_fetch(self):
        r=run_dense_and_column_fetch([[127]*4 for _ in range(4)],[0]*4)
        self.assertEqual(r["sums"],[0]*4)
        self.assertEqual(r["column_requests"],0)
    def test_sign_wrap(self):
        r=run_dense_and_column_fetch([[-128]*4 for _ in range(4)],[-128,-128,0,0],Config(accum_bits=16))
        self.assertEqual(r["sums"],[-32768]*4)
    def test_burst_granularity(self):
        z=transferred_bytes(4,2,1,1)
        self.assertEqual((z["column_fetch_bytes"],z["element_fetch_bytes"]),(8,8))
        z=transferred_bytes(4,2,1,32)
        self.assertEqual((z["column_fetch_bytes"],z["element_fetch_bytes"],z["useful_weight_bytes"]),(64,256,8))
        z=transferred_bytes(4,2,1,64)
        self.assertEqual(z["column_fetch_bytes"],128)
    def test_64b_burst_does_not_equal_actual_hbm(self):
        z=transferred_bytes(4,4,1,64)
        self.assertEqual(z["column_fetch_bytes"],256)
        self.assertEqual(z["useful_weight_bytes"],16)
    def test_randomized_signed_oracle(self):
        rng=random.Random(91919)
        for n in (1,2,4,8):
            for _ in range(160):
                w=[[rng.randrange(-128,128) for _ in range(n)] for _ in range(n)]
                x=[rng.choice([0,0,rng.randrange(-128,128)]) for _ in range(n)]
                r=run_dense_and_column_fetch(w,x,Config(n=n,accum_bits=32))
                expected=[sum(w[row][c]*x[c] for c in range(n)) for row in range(n)]
                self.assertEqual(r["sums"],expected)
                self.assertEqual(r["fetched_weights"]+r["skipped_weights"],n*n)
                self.assertEqual(r["elementwise_requests"],n*r["column_requests"])
    def test_reject_invalid(self):
        with self.assertRaises(ValueError):Config(n=0)
        with self.assertRaises(ValueError):run_dense_and_column_fetch([[0]*4]*4,[0]*3)
        with self.assertRaises(ValueError):transferred_bytes(4,5)
        with self.assertRaises(ValueError):signed(True,8)
if __name__=="__main__":unittest.main()
