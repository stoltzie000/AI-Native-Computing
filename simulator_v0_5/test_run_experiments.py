import unittest
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('v05_execute',Path(__file__).with_name('run_experiments.py'))
_mod=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
execute=_mod.execute

class FullReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=execute()
    def test_clearly_e1(self):self.assertEqual(self.r['evidence_level'],'E1 only')
    def test_no_measured_benchmark(self):self.assertEqual(self.r['benchmark_readiness']['status'],'BLOCK_QUALITY_UNVERIFIED')
    def test_quantization_quality_not_assumed(self):
        self.assertTrue(all(a['quality_equivalence']=='NOT_ESTABLISHED' for a in self.r['weight_precision_traffic_sensitivity']))
    def test_4bit_identity(self):
        row=next(x for x in self.r['weight_precision_traffic_sensitivity'] if x['weight_bits']==4)
        self.assertAlmostEqual(row['ideal_speed_relative_to_4bit_weights'],1)
    def test_1bit_near_double_in_traffic_only(self):
        row=next(x for x in self.r['weight_precision_traffic_sensitivity'] if x['weight_bits']==1)
        self.assertGreater(row['ideal_speed_relative_to_4bit_weights'],2)
    def test_optimal_bandwidth_bound_dominates_model(self):
        top=self.r['minimum_memory_traffic']['ideal_70pct_bandwidth_only_steps_per_s']
        self.assertTrue(all(row['result']['conditional_steps_per_second']<=top for row in self.r['equalized_profiles']['rows']))
    def test_all_scenarios_equal_stacks(self):
        self.assertTrue(all(row['total_hbm_stacks']==8 for row in self.r['equalized_profiles']['rows']))
    def test_no_claim_hardware_verified(self):
        self.assertTrue(any('physical' in s for s in self.r['missing_for_E4']))
