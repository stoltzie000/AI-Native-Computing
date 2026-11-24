import csv
import os
import tempfile
import unittest
from analyze_delivery import analyze,interval
class DiagnosticAnalysisTests(unittest.TestCase):
    def run_rows(self,entries):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'obs.csv')
            with open(path,'w',newline='',encoding='utf-8') as f:
                w=csv.writer(f)
                w.writerow(['session_id','variant','started_at_utc','ended_at_utc','delivery_outcome'])
                w.writerows(entries)
            return analyze(path)
    def test_unknown_not_success(self):
        v=self.run_rows([['1','30s','','','unknown']])['30s']
        self.assertIsNone(v['observed_timeout_rate'])
        self.assertEqual(v['unknown'],1)
    def test_group_exposure(self):
        v=self.run_rows([
          ['1','30s','2026-11-24T17:00:00Z','2026-11-24T17:30:00Z','success'],
          ['2','30s','2026-11-24T17:30:00Z','2026-11-24T18:00:00Z','timeout'],
          ['3','120s','','','unknown']])
        self.assertEqual(v['30s']['observed_timeout_rate'],.5)
        self.assertEqual(v['30s']['timeout_per_observed_hour'],1.)
        self.assertIsNone(v['120s']['observed_timeout_rate'])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            self.run_rows([['1','30s','','','success'],['1','60s','','','success']])
    def test_reversed_time_rejected(self):
        with self.assertRaises(ValueError):
            self.run_rows([['1','30s','2026-11-24T18:00:00Z','2026-11-24T17:00:00Z','timeout']])
    def test_zero_sample_undefined(self):
        self.assertIsNone(interval(0,0))
        self.assertEqual(interval(0,1)[0],0.)
        self.assertGreater(interval(0,1)[1],.5)
if __name__=='__main__': unittest.main()
