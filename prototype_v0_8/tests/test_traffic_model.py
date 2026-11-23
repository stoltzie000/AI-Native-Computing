import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from traffic_model import TrafficScenario,cycle_lower_bound

class TrafficTests(unittest.TestCase):
    def test_base_case(self):
        x=TrafficScenario()
        self.assertAlmostEqual(x.original_gb,26.465)
        self.assertEqual(x.best_case_bandwidth_speedup,1)
    def test_target_twofold(self):
        x=TrafficScenario()
        threshold=x.required_zero_fraction(2)
        self.assertGreater(threshold,.74)
        self.assertLess(threshold,.741)
        self.assertAlmostEqual(TrafficScenario(zero_activation_fraction=threshold).best_case_bandwidth_speedup,2)
    def test_metadata_can_erase_gain(self):
        x=TrafficScenario(zero_activation_fraction=.5,metadata_gb=9)
        self.assertLess(x.best_case_bandwidth_speedup,1)
    def test_zero_fraction_one_has_finite_kv_limit(self):
        x=TrafficScenario(zero_activation_fraction=1)
        self.assertAlmostEqual(x.best_case_bandwidth_speedup,26.465/8.59)
    def test_fsm_lower_bound(self):
        a=cycle_lower_bound(4,4)
        b=cycle_lower_bound(4,2)
        c=cycle_lower_bound(4,0)
        self.assertEqual([a["issued_reads"],b["issued_reads"],c["issued_reads"]],[16,8,0])
        self.assertEqual([a["minimum_fsm_cycles"],b["minimum_fsm_cycles"],c["minimum_fsm_cycles"]],[50,34,18])
    def test_zero_all_memory_is_unbounded_math_not_measured_speed(self):
        x=TrafficScenario(weight_gb=1,kv_gb=0,zero_activation_fraction=1)
        self.assertEqual(x.gated_gb,0)
        self.assertEqual(x.best_case_bandwidth_speedup,float("inf"))
    def test_reject_invalid_inputs(self):
        with self.assertRaises(ValueError):TrafficScenario(zero_activation_fraction=1.1)
        with self.assertRaises(ValueError):TrafficScenario(weight_gb=0)
        with self.assertRaises(ValueError):cycle_lower_bound(4,5)
if __name__=="__main__":unittest.main()
