"""Independent invariants, arithmetic oracle and negative engineering tests."""
import json
import math
import unittest
from dataclasses import replace

from engine import GB, GIB, Memory, System, Workload, simulate
from scenarios import reference_systems, research_systems
from run_experiments import run


class WorkloadTests(unittest.TestCase):
    def test_qwen_kv_per_token(self):
        self.assertEqual(Workload().kv_bytes_per_token, 262144)

    def test_kv_8k_is_2gib(self):
        w = Workload(context=8192)
        self.assertEqual(w.kv_resident_bytes, 2*GIB)

    def test_kv_32k_is_8gib(self):
        self.assertEqual(Workload().kv_resident_bytes, 8*GIB)

    def test_after_step_capacity_includes_one_more_kv(self):
        w = Workload(context=8192)
        self.assertEqual(w.kv_resident_after_step_bytes - w.kv_resident_bytes,
                         w.kv_bytes_per_token * w.batch)

    def test_weight_metadata(self):
        self.assertAlmostEqual(Workload().weight_bytes/GB,17.875)

    def test_invalid_geometry(self):
        with self.assertRaises(ValueError): Workload(hidden=1234)

    def test_negative_or_nan_input(self):
        with self.assertRaises(ValueError): Workload(context=-1)
        with self.assertRaises(ValueError): Workload(parameters=float('nan'))
        with self.assertRaises(ValueError): Workload(weight_bits=0)

    def test_invalid_fraction(self):
        with self.assertRaises(ValueError): Workload(pre_attention_fraction=1)
        with self.assertRaises(ValueError): Workload(attention_output_fraction=.99)

    def test_batch_increases_kv(self):
        a,b = Workload(batch=1), Workload(batch=3)
        self.assertEqual(b.kv_step_bytes, 3*a.kv_step_bytes)
        self.assertEqual(b.kv_resident_bytes, 3*a.kv_resident_bytes)


class SystemsAndSimulation(unittest.TestCase):
    def setUp(self):
        self.w = Workload()
        self.single = System('oracle',1,Memory(100,1000,banks=1),100,tiles_per_phase=1)

    def test_invalid_fast_residency_without_memory(self):
        with self.assertRaises(ValueError):
            System('bad',1,Memory(100,100),100,kv_fast_fraction=.5)

    def test_invalid_module_count(self):
        with self.assertRaises(ValueError):
            System('bad',0,Memory(100,100),100)

    def test_invalid_memory_fraction(self):
        with self.assertRaises(ValueError):
            Memory(2,500,sustained_fraction=1.5)

    def test_missing_fabric_rejected(self):
        with self.assertRaises(ValueError):
            System('bad',2,Memory(100,100),100)

    def test_single_node_no_fabric(self):
        r=simulate(self.w,self.single)
        self.assertEqual(r['total_fabric_bytes_gb'],0)
        self.assertEqual(r['number_of_collective_operations'],0)

    def test_single_tile_exact_reference_oracle(self):
        # For one bank, one tile, one module, one layer and no latency,
        # every phase is a non-overlapping memory-then-compute operation.
        w=Workload(layers=1,parameters=1e6,context=8,batch=1,scratch_gb=0)
        s=System('oracle',1,Memory(5,5,banks=1),20,tiles_per_phase=1)
        r=simulate(w,s)
        expected = (w.weight_bytes + w.kv_step_bytes)/(5*GB) + (
            w.dense_ops_per_layer + w.attention_ops_per_layer)/(20e12)
        self.assertAlmostEqual(r['decode_step_ms']/1000,expected,places=9)

    def test_layout_rejects_fractional_query_heads(self):
        s=replace(research_systems()[1], modules=16)
        r=simulate(self.w,s)
        self.assertEqual(r['status'],'REJECT_LAYOUT')

    def test_shorter_context_faster(self):
        r_small=simulate(Workload(context=2048),self.single)
        r_big=simulate(Workload(context=32768),self.single)
        self.assertGreater(r_small['conditional_steps_per_second'],r_big['conditional_steps_per_second'])

    def test_too_small_bulk(self):
        s=replace(self.single,bulk=Memory(1,1000,banks=1))
        self.assertEqual(simulate(self.w,s)['status'],'REJECT_CAPACITY')

    def test_too_small_fast(self):
        s=replace(self.single,fast=Memory(.01,1000),kv_fast_fraction=1)
        self.assertEqual(simulate(self.w,s)['status'],'REJECT_CAPACITY')

    def test_no_memory_overcommit_in_reference(self):
        for s in reference_systems():
            self.assertEqual(simulate(self.w,s)['status'],'SIMULATED')

    def test_all_bytes_count_once(self):
        r=simulate(self.w,self.single)
        self.assertAlmostEqual((r['total_bulk_bytes_gb']+r['total_fast_bytes_gb'])*GB,
                               self.w.weight_bytes+self.w.kv_step_bytes,delta=1000)

    def test_replication_above_kv_heads(self):
        w=Workload(query_heads=40,kv_heads=8)
        s=System('40node',40,Memory(10,100),10,fabric_gbs=1,tiles_per_phase=1)
        r=simulate(w,s)
        self.assertEqual(r['status'],'SIMULATED')
        self.assertEqual(r['kv_replication'],5)
        self.assertAlmostEqual((r['total_bulk_bytes_gb']+r['total_fast_bytes_gb'])*GB,
                               w.weight_bytes+5*w.kv_step_bytes,delta=1000)

    def test_higher_bandwidth_is_never_slower(self):
        high=replace(self.single,bulk=Memory(100,2000,banks=1))
        self.assertLess(simulate(self.w,high)['decode_step_ms'],
                        simulate(self.w,self.single)['decode_step_ms'])

    def test_higher_compute_is_never_slower(self):
        w=Workload(parameters=1e7,context=10)
        low=replace(self.single,compute_tops_per_module=.01)
        high=replace(self.single,compute_tops_per_module=1)
        self.assertLess(simulate(w,high)['decode_step_ms'], simulate(w,low)['decode_step_ms'])

    def test_hot_bank_is_slower(self):
        s=research_systems()[1]
        a=simulate(self.w,s)
        b=simulate(self.w,replace(s,bank_mapping='hot_bank'))
        self.assertLess(b['conditional_steps_per_second'],a['conditional_steps_per_second'])

    def test_more_fabric_latency_is_slower(self):
        s=research_systems()[1]
        slow=replace(s,fabric_latency_us=s.fabric_latency_us+20)
        self.assertLess(simulate(self.w,slow)['conditional_steps_per_second'],
                        simulate(self.w,s)['conditional_steps_per_second'])

    def test_four_module_collective_count(self):
        s=research_systems()[0]
        r=simulate(self.w,s)
        self.assertEqual(r['number_of_collective_operations'],2*self.w.layers)
        self.assertGreater(r['total_fabric_bytes_gb'],0)

    def test_round_robin_vs_hotspot_transfer_volume_same(self):
        s=research_systems()[1]
        a=simulate(self.w,s);b=simulate(self.w,replace(s,bank_mapping='hot_bank'))
        self.assertEqual(a['total_bulk_bytes_gb'],b['total_bulk_bytes_gb'])
        self.assertEqual(a['number_of_memory_transactions'],b['number_of_memory_transactions'])

    def test_fast_shifts_memory_traffic_without_reducing_total(self):
        s=research_systems()[2]
        r=simulate(self.w,s)
        self.assertGreater(r['total_fast_bytes_gb'],0)
        self.assertGreater(r['total_bulk_bytes_gb'],0)
        self.assertAlmostEqual((r['total_fast_bytes_gb']+r['total_bulk_bytes_gb'])*GB,
                               self.w.weight_bytes+self.w.kv_step_bytes, delta=1000)

    def test_single_module_sequential_lower_bound(self):
        r=simulate(self.w,self.single)
        self.assertGreaterEqual(r['decode_step_ms'],r['global_roofline_lower_ms'])

    def test_tiling_has_no_traffic_change(self):
        one=simulate(self.w,self.single)
        many=simulate(self.w,replace(self.single,tiles_per_phase=16))
        self.assertEqual(one['total_bulk_bytes_gb'],many['total_bulk_bytes_gb'])
        self.assertGreater(many['number_of_memory_transactions'],one['number_of_memory_transactions'])

    def test_trace_does_not_change_calculated_time(self):
        a=simulate(self.w,self.single)
        b=simulate(self.w,self.single,record_first_layer=True)
        self.assertEqual(a['decode_step_ms'],b['decode_step_ms'])
        self.assertEqual([x['phase'] for x in b['first_layer_events']],
                         ['pre_attention_projection','attention_KV_read_write','attention_output_projection','MLP'])

    def test_sustained_bw_sensitivity(self):
        s=research_systems()[1]
        low=replace(s,bulk=replace(s.bulk,sustained_fraction=.2))
        self.assertLess(simulate(self.w,low)['conditional_steps_per_second'],
                        simulate(self.w,s)['conditional_steps_per_second'])

    def test_reference_vendor_peaks_from_scenarios(self):
        a=reference_systems()
        self.assertEqual([x.bulk.capacity_gb for x in a],[32,141,288])
        self.assertEqual([x.bulk.gb_per_second for x in a],[1792,4800,8000])

    def test_deterministic_report(self):
        a=json.dumps(run(),sort_keys=True,allow_nan=False)
        b=json.dumps(run(),sort_keys=True,allow_nan=False)
        self.assertEqual(a,b)


if __name__=='__main__': unittest.main()
