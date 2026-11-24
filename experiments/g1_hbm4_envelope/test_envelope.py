import math
import unittest
from envelope import ControllerEnvelope, research_example


class HBMEnvelopeTests(unittest.TestCase):
    def test_published_data_pin_equation(self):
        c = ControllerEnvelope(8, 36, 2048, 10)
        s = c.screen(weight_traffic_gb=17.875, state_traffic_gb=8.590)
        self.assertEqual(s["nominal_capacity_gb"], 288)
        self.assertEqual(s["hbm_data_pins_at_package_boundary"], 16384)
        self.assertEqual(s["controller_peak_tb_s"], 20.48)
        self.assertAlmostEqual(s["memory_only_min_time_ms_at_peak"],
                               26.465 / 20.48, places=12)
        self.assertEqual(s["physical_gate"], "OPEN_PDK_PHY_PACKAGE_IO_POWER_THERMAL_UNMEASURED")
        self.assertFalse(s["actual_measurement_supplied"])
        self.assertIsNone(s["memory_only_scenario_steps_per_s"])
        self.assertTrue("PACKAGE_FEASIBILITY_UNKNOWN" in s["capacity_status"])

    def test_fractional_sensitivity_only_conditional(self):
        c = ControllerEnvelope(8,36,2048,10,usable_fraction=.7,
                               reserved_capacity_fraction=.1)
        s = c.screen(weight_traffic_gb=17.875, state_traffic_gb=8.590)
        self.assertAlmostEqual(s["scenario_bandwidth_gb_s"], 14336.0)
        self.assertAlmostEqual(s["memory_only_scenario_steps_per_s"], 14336/26.465)
        self.assertAlmostEqual(s["assumed_usable_capacity_gb"], 259.2)
        self.assertEqual(s["capacity_status"], "BLOCK_RESIDENCY_AND_PACKAGE_FEASIBILITY_UNKNOWN")
        self.assertNotEqual(s["physical_gate"], "PASS")

    def test_capacity_rejection_only_where_assumed_headroom(self):
        c = ControllerEnvelope(8,36,2048,10,reserved_capacity_fraction=.25)
        fail = c.screen(weight_traffic_gb=2,state_traffic_gb=8,resident_gb=225)
        just = c.screen(weight_traffic_gb=2,state_traffic_gb=8,resident_gb=216)
        self.assertEqual(fail["capacity_status"], "REJECT_ASSUMED_CAPACITY")
        self.assertEqual(just["capacity_status"], "UNVERIFIED_PHY_PACKAGE_AND_THERMAL")
        self.assertIn("OPEN",just["physical_gate"])

    def test_reject_invalid_configuration_and_false_measurement(self):
        for kwargs in (
            {"stacks":0}, {"stacks":3.5}, {"stacks":True},
            {"data_pins_per_stack":0}, {"controller_gbps_per_pin":0},
            {"usable_fraction":0}, {"usable_fraction":1.3},
            {"reserved_capacity_fraction":-.1}, {"reserved_capacity_fraction":1.5},
            {"measured_achieved_bandwidth_gb_s":math.nan},
            {"measured_achieved_bandwidth_gb_s":-1},
        ):
            cfg=dict(stacks=8,capacity_gb_per_stack=36,
                     data_pins_per_stack=2048,controller_gbps_per_pin=10)
            cfg.update(kwargs)
            with self.assertRaises(ValueError,msg=repr(kwargs)):
                ControllerEnvelope(**cfg)
        c=ControllerEnvelope(8,36,2048,10)
        for x,y in ((-1,1),(1,-1),(0,0),(math.inf,1)):
            with self.assertRaises(ValueError):
                c.screen(weight_traffic_gb=x,state_traffic_gb=y)
        with self.assertRaises(ValueError):
            c.screen(weight_traffic_gb=1,state_traffic_gb=1,resident_gb=-1)
        c=ControllerEnvelope(8,36,2048,10,measured_achieved_bandwidth_gb_s=25000)
        with self.assertRaises(ValueError):
            c.screen(weight_traffic_gb=1,state_traffic_gb=1)

    def test_vendor_peak_is_specification_not_measurement(self):
        e=research_example()
        p=e["controller_spec_envelope"]
        rubin=e["rubin_peak_comparator_only"]
        self.assertAlmostEqual(rubin["controller_peak_fraction_of_vendor_peak"],20.48/22)
        self.assertIsNone(rubin["gpu_measured_tokens_per_second"])
        self.assertFalse(rubin["quality_matched"])
        self.assertFalse(p["actual_measurement_supplied"])
        self.assertIn("NO_ACCEPTANCE",e["decision"])

    def test_unit_consistency_and_monotonicity(self):
        low=ControllerEnvelope(4,36,2048,10)
        high=ControllerEnvelope(8,36,2048,10)
        kwargs={"weight_traffic_gb":17.875,"state_traffic_gb":8.590}
        a=low.screen(**kwargs); b=high.screen(**kwargs)
        self.assertEqual(b["controller_peak_gb_s"],2*a["controller_peak_gb_s"])
        self.assertAlmostEqual(b["memory_only_min_time_ms_at_peak"],
                               a["memory_only_min_time_ms_at_peak"]/2)
        c=high.screen(weight_traffic_gb=17.875,state_traffic_gb=17.180)
        self.assertLess(c["memory_only_max_steps_per_s_at_peak"],
                        b["memory_only_max_steps_per_s_at_peak"])

if __name__=="__main__":
    unittest.main()
