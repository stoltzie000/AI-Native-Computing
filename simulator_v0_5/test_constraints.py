import math
import unittest
from constraints import RawLinkHypothesis, same_bandwidth_double_speed, decode_traffic, AssumedPower, benchmark_comparability


class TestConstraints(unittest.TestCase):
    def test_unity_traffic(self):
        self.assertEqual(decode_traffic(40,20),60)
    def test_no_weights(self):
        self.assertEqual(decode_traffic(40,20,0),20)
    def test_no_state(self):
        self.assertEqual(decode_traffic(40,20,1,0),40)
    def test_both_zero(self):
        self.assertEqual(decode_traffic(40,20,0,0),0)
    def test_invalid_fraction(self):
        with self.assertRaises(ValueError):decode_traffic(10,2,1.2)
    def test_invalid_nan(self):
        with self.assertRaises(ValueError):decode_traffic(math.nan,2)
    def test_twofold_weight_reduction(self):
        r=same_bandwidth_double_speed(20,10)
        self.assertAlmostEqual(r['allowed_weight_fraction'],.25)
        self.assertAlmostEqual(r['minimum_weight_traffic_reduction_fraction'],.75)
    def test_unachievable_by_weights_only(self):
        r=same_bandwidth_double_speed(1,10)
        self.assertFalse(r['possible_by_weight_reduction_only'])
    def test_no_kv_requires_half_weight(self):
        self.assertAlmostEqual(same_bandwidth_double_speed(20,0)['allowed_weight_fraction'],.5)
    def test_invalid_factor(self):
        with self.assertRaises(ValueError):same_bandwidth_double_speed(20,0,1)
    def test_lanes_exact(self):
        a=RawLinkHypothesis(64,1,1,16)
        self.assertEqual(a.needed_one_way_lanes(128),16)
    def test_lanes_with_overhead(self):
        a=RawLinkHypothesis(64,.98,.85,32,.3)
        r=a.envelope(128,3,10)
        self.assertEqual(r['one_way_lanes_per_link'],20)
        self.assertEqual(r['total_physical_unidirectional_lanes'],400)
        self.assertEqual(r['busiest_compute_node_lanes'],120)
        self.assertAlmostEqual(r['minimum_aggregate_link_phy_w_at_full_load'],6.144)
    def test_reject_lanes(self):
        self.assertEqual(RawLinkHypothesis(32,1,.8,16).envelope(128,3,10)['status'],'REJECT_ASSUMED_LANE_PORT')
    def test_lane_power_unknown(self):
        self.assertIsNone(RawLinkHypothesis(64,1,1,20).envelope(128,2,5)['minimum_aggregate_link_phy_w_at_full_load'])
    def test_invalid_lane_fraction(self):
        with self.assertRaises(ValueError):RawLinkHypothesis(64,1.1,1,20)
    def test_pj_per_bit_to_w(self):
        a=RawLinkHypothesis(8,1,1,1,1)
        self.assertAlmostEqual(a.envelope(1,1,1)['minimum_aggregate_link_phy_w_at_full_load'],.016)
    def test_power_explicit_assumed_only(self):
        r=AssumedPower(200,20,8,1,host_w=100,cooling_overhead_fraction=.1,phy_power_w=10,allowed_system_w=2000).report()
        self.assertAlmostEqual(r['assumed_lower_envelope_w'],(1600+160+100+10)*1.1)
        self.assertEqual(r['status'],'REJECT_ASSUMED_POWER')
    def test_unknown_power(self):
        r=AssumedPower(100,10,8,1).report()
        self.assertIsNone(r['assumed_lower_envelope_w'])
        self.assertEqual(r['status'],'UNVERIFIED_POWER_ENVELOPE')
    def test_power_nonexceed(self):
        r=AssumedPower(100,10,8,1,phy_power_w=10,allowed_system_w=2000).report()
        self.assertEqual(r['status'],'UNVERIFIED_POWER_ENVELOPE')
    def test_negative_power(self):
        with self.assertRaises(ValueError):AssumedPower(100,-1,8,1)
    def test_benchmark_reject(self):
        a=self.record()
        b={**a,'memory_generation':'HBM3E'}
        self.assertEqual(benchmark_comparability(a,b)['status'],'REJECT_MATCHED_COMPARISON')
    def test_benchmark_quality(self):
        a=self.record()
        self.assertEqual(benchmark_comparability(a,a)['status'],'BLOCK_QUALITY_UNVERIFIED')
    def test_benchmark_timing(self):
        a={**self.record(),'model_quality_verified':True}
        self.assertEqual(benchmark_comparability(a,a)['status'],'BLOCK_NO_PAIRED_TIMING')
    def test_benchmark_energy(self):
        a={**self.record(),'model_quality_verified':True,'measured_timing':True}
        self.assertEqual(benchmark_comparability(a,a)['status'],'BLOCK_ENERGY_COMPARISON')
    def test_benchmark_ready_not_proven(self):
        a={**self.record(),'model_quality_verified':True,'measured_timing':True,'measured_wall_energy':True}
        self.assertEqual(benchmark_comparability(a,a)['status'],'READY_FOR_STATISTICAL_REVIEW_NOT_PROVEN')
    def test_incomplete_benchmark(self):
        with self.assertRaises(ValueError):benchmark_comparability({}, {})

    @staticmethod
    def record():
        return {'workload':'X','context':32768,'batch':1,'weight_bits':4,'kv_bits':16,
                'model_quality_verified':False,'memory_generation':'HBM4','memory_stacks':8,
                'measured_timing':False,'measured_wall_energy':False}
