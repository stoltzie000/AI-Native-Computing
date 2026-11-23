import unittest
from package_screen import PackageHeatHypothesis,conditional_best,hidden_overhead_crossover_ms
from equal_resources import IsoResources,run_equalized

class HeatTests(unittest.TestCase):
    def test_total_heat_conserved(self):
        a=PackageHeatHypothesis(2200,20,8,1400,0)
        for n in (1,2,4,8):
            x=a.evaluate(n)
            self.assertAlmostEqual(x['partial_heat_w_per_package']*n,2360)
    def test_one_package_rejected(self):
        a=PackageHeatHypothesis(2200,20,8,1400,0)
        self.assertEqual(a.evaluate(1)['status'],'REJECT_ASSUMED_PACKAGE_HEAT')
    def test_two_packages_not_rejected(self):
        a=PackageHeatHypothesis(2200,20,8,1400,0)
        self.assertEqual(a.evaluate(2)['status'],'ONLY_ASSUMPTION_LEVEL_NONREJECTION')
    def test_unknown_phy_does_not_pass(self):
        a=PackageHeatHypothesis(2200,20,8,1400)
        self.assertEqual(a.evaluate(2)['status'],'UNKNOWN_PHY_AND_OTHER_HEAT')
    def test_reject_phy_including_overhead(self):
        a=PackageHeatHypothesis(2200,20,8,1400,300)
        self.assertEqual(a.evaluate(2)['status'],'REJECT_ASSUMED_PACKAGE_HEAT')
    def test_select_fastest_conditional(self):
        a=PackageHeatHypothesis(2200,20,8,1400,0)
        r=run_equalized(IsoResources())
        self.assertEqual(conditional_best(r['rows'],a)['best_conditional_packages'],2)
    def test_no_package_survives(self):
        a=PackageHeatHypothesis(2200,20,8,100,0)
        r=run_equalized(IsoResources())
        self.assertIsNone(conditional_best(r['rows'],a)['best_conditional_packages'])
    def test_extra_delay_crossover_positive(self):
        r=run_equalized(IsoResources())['rows']
        self.assertGreater(hidden_overhead_crossover_ms(r[0],r[1]),0)
        self.assertLess(hidden_overhead_crossover_ms(r[0],r[1]),0.1)
    def test_invalid_package_count(self):
        a=PackageHeatHypothesis(2200,20,8,1400,0)
        with self.assertRaises(ValueError):a.evaluate(3)
    def test_negative_phy(self):
        with self.assertRaises(ValueError):PackageHeatHypothesis(2200,20,8,1400,-2)
    def test_zero_power_for_link_allowed(self):
        self.assertEqual(PackageHeatHypothesis(2200,20,8,1400,0).evaluate(4)['status'],'ONLY_ASSUMPTION_LEVEL_NONREJECTION')
