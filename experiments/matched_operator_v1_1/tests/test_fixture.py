import unittest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fixture import make_cases, exact_oracle, write_memh, canonical, ROWS, COLS

class FixtureTest(unittest.TestCase):
    def test_shapes(self):
        x=make_cases()
        self.assertEqual((x['rows'],x['cols']),(ROWS,COLS))
        self.assertGreaterEqual(len(x['cases']),10)
        self.assertEqual(len({c['name'] for c in x['cases']}),len(x['cases']))
        for c in x['cases']:
            self.assertEqual(c['expected_int32'],exact_oracle(c['weights_row_major'],c['vector']))

    def test_required_controls(self):
        x={c['name']:c for c in make_cases()['cases']}
        self.assertEqual(x['all_zero_vector']['active_cols'],0)
        self.assertEqual(x['half_active']['active_cols'],2)
        self.assertEqual(x['dense_random']['active_cols'],4)
        self.assertTrue(all(all(y==0 for y in x['all_zero_vector']['expected_int32']) for _ in range(1)))

    def test_exact_outputs_within_fp32_integer_range(self):
        for c in make_cases()['cases']:
            self.assertLess(max(map(abs,c['expected_int32'])),2**24)

    def test_generator_deterministic(self):
        self.assertEqual(canonical(make_cases()),canonical(make_cases()))

    def test_memh_layout(self):
        with TemporaryDirectory() as t:
            x=make_cases()
            write_memh(x,Path(t))
            c=x['cases'][0]
            b=(Path(t)/f"{c['name']}_weights.hex").read_text().splitlines()
            for col in range(COLS):
                for r in range(ROWS):
                    self.assertEqual(int(b[col*ROWS+r],16),c['weights_row_major'][r][col]&255)

    def test_reject_shape(self):
        with self.assertRaises(ValueError): exact_oracle([[1]*COLS]*(ROWS-1),[1]*COLS)

    def test_reject_values(self):
        with self.assertRaises(ValueError): exact_oracle([[1]*COLS]*ROWS,[128,0,0,0])
        with self.assertRaises(ValueError): exact_oracle([[1]*COLS]*ROWS,[True,0,0,0])

if __name__=='__main__':unittest.main()
