import unittest
from dataclasses import replace
from equal_resources import IsoResources,system_for,run_equalized,include_clocks_and_interface_overhead


class EqualizedTests(unittest.TestCase):
    def test_total_resources_equal(self):
        r=IsoResources()
        all_=[system_for(n,r) for n in (1,2,4,8)]
        for a in all_:
            self.assertAlmostEqual(a.bulk.capacity_gb*a.modules,288)
            self.assertAlmostEqual(a.bulk.gb_per_second*a.modules,22400)
            self.assertAlmostEqual(a.compute_tops_per_module*a.modules,1600)
    def test_per_module_configuration(self):
        a=system_for(4,IsoResources())
        self.assertEqual(a.bulk.capacity_gb,72)
        self.assertEqual(a.bulk.gb_per_second,5600)
        self.assertEqual(a.compute_tops_per_module,400)
    def test_invalid_count(self):
        with self.assertRaises(ValueError):system_for(3,IsoResources())
    def test_invalid_stacks(self):
        with self.assertRaises(ValueError):system_for(8,IsoResources(stacks=4))
    def test_invalid_context(self):
        with self.assertRaises(ValueError):IsoResources(context=-1)
    def test_equal_run(self):
        x=run_equalized(IsoResources())
        self.assertEqual(len(x['rows']),4)
        self.assertTrue(all(y['result']['status']=='SIMULATED_ENVELOPE' for y in x['rows']))
    def test_distribution_is_slower_in_current_model(self):
        x=run_equalized(IsoResources())
        rates=[r['result']['conditional_steps_per_second'] for r in x['rows']]
        self.assertTrue(all(a>b for a,b in zip(rates,rates[1:])))
    def test_two_contexts(self):
        small=run_equalized(IsoResources(context=2048))
        large=run_equalized(IsoResources(context=32768))
        for x,y in zip(small['rows'],large['rows']):
            self.assertGreater(x['result']['conditional_steps_per_second'],y['result']['conditional_steps_per_second'])
    def test_bandwidth_sensitivity(self):
        orig=run_equalized(IsoResources())
        slow=run_equalized(IsoResources(sustained_fraction=.4))
        for x,y in zip(orig['rows'],slow['rows']):
            self.assertGreater(x['result']['conditional_steps_per_second'],y['result']['conditional_steps_per_second'])
    def test_layer_overhead_never_increases_rate(self):
        x=run_equalized(IsoResources())
        with_latency=include_clocks_and_interface_overhead(x,pad_ms=.25)
        for row,mod in zip(x['rows'],with_latency):
            self.assertLess(mod['steps_per_s_with_extra_overhead'],row['result']['conditional_steps_per_second'])
    def test_invalid_latency(self):
        with self.assertRaises(ValueError):include_clocks_and_interface_overhead({'rows':[]},pad_ms=-.1)
    def test_invalid_utilization(self):
        with self.assertRaises(ValueError):IsoResources(sustained_fraction=1.1)
    def test_reject_bandwidth_zero(self):
        with self.assertRaises(ValueError):IsoResources(peak_gbs_per_stack=0)
    def test_single_package_no_collectives(self):
        r=run_equalized(IsoResources())['rows'][0]
        self.assertEqual(r['result']['all_collectives_ms'],0)
    def test_slow_board_link_hurts_distributed_only(self):
        r=IsoResources()
        fast=run_equalized(r)
        slow=run_equalized(r,link_gbs=16,link_budget_gbs=128,hop_ns=3000,injection_ns=1000)
        self.assertEqual(fast['rows'][0]['result']['conditional_steps_per_second'],slow['rows'][0]['result']['conditional_steps_per_second'])
        self.assertLess(slow['rows'][-1]['result']['conditional_steps_per_second'],fast['rows'][-1]['result']['conditional_steps_per_second'])

if __name__=='__main__':unittest.main()
