import unittest
from dataclasses import replace
from model import DecodeWorkload, Architecture, analyze, generic_roofline, GIB
from scenarios import architectures


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.w = DecodeWorkload()
        self.a = Architecture('single', 1, 32, 1000, 100)

    def test_reference_attention_geometry(self):
        self.assertEqual(self.w.hidden_size, self.w.query_heads * self.w.head_dim)
        self.assertEqual(self.w.kv_bytes_per_context_token, 262144)

    def test_reference_kv_cache_32k(self):
        self.assertEqual(self.w.kv_resident_bytes / GIB, 8)

    def test_reference_kv_cache_8k(self):
        self.assertEqual(replace(self.w, context=8192).kv_resident_bytes / GIB, 2)

    def test_weight_storage_decimal(self):
        self.assertAlmostEqual(self.w.weight_bytes / 1e9, 17.875)

    def test_weight_metadata_not_ignored(self):
        w = replace(self.w, weight_metadata_fraction=0)
        self.assertAlmostEqual(w.weight_bytes / 1e9, 16.25)

    def test_capacity_checked(self):
        out = analyze(self.w, replace(self.a, bulk_gb_per_module=20))
        self.assertEqual(out['status'], 'REJECT_CAPACITY')
        self.assertIsNone(out['optimistic_tokens_per_second'])

    def test_capacity_includes_scratch(self):
        w = replace(self.w, scratch_gb=8)
        self.assertFalse(analyze(w, self.a)['fits_memory'])

    def test_decode_kv_io_scales_with_context(self):
        shorter = replace(self.w, context=4096)
        self.assertLess(shorter.decode_kv_bytes_per_step, self.w.decode_kv_bytes_per_step)
        self.assertLess(shorter.operations_per_step, self.w.operations_per_step)

    def test_batch_reuses_weights(self):
        batched = replace(self.w, batch=2)
        self.assertEqual(batched.decode_weight_bytes_per_step, self.w.decode_weight_bytes_per_step)
        self.assertEqual(batched.decode_kv_bytes_per_step, 2 * self.w.decode_kv_bytes_per_step)

    def test_more_bandwidth_improves_memory_bound_model(self):
        w = replace(self.w, context=4096)
        slow = analyze(w, replace(self.a, bulk_gbs_per_module=500))
        fast = analyze(w, replace(self.a, bulk_gbs_per_module=1000))
        self.assertGreater(fast['optimistic_tokens_per_second'], slow['optimistic_tokens_per_second'])

    def test_faster_compute_cannot_hurt(self):
        slow = analyze(self.w, replace(self.a, tops_per_module=0.5))
        fast = analyze(self.w, replace(self.a, tops_per_module=1))
        self.assertGreaterEqual(fast['optimistic_tokens_per_second'], slow['optimistic_tokens_per_second'])

    def test_fast_placement_enforces_fast_capacity(self):
        a = Architecture('fast-too-small', 1, 200, 1000, 100, fast_gb_per_module=5,
                         fast_gbs_per_module=5000, weight_fast_fraction=1)
        self.assertEqual(analyze(self.w, a)['status'], 'REJECT_CAPACITY')

    def test_fabric_has_latency_penalty(self):
        a = Architecture('mesh', 4, 32, 1000, 40, fabric_gbs=200, fabric_latency_us=0)
        b = replace(a, fabric_latency_us=10)
        t1 = analyze(self.w, a)['optimistic_step_ms']
        t2 = analyze(self.w, b)['optimistic_step_ms']
        self.assertGreater(t2, t1)

    def test_conditional_power_not_invented(self):
        self.assertIsNone(analyze(self.w, self.a)['conditional_energy_j_per_token'])
        with_power = replace(self.a, assumed_system_watts=100)
        r = analyze(self.w, with_power)
        self.assertAlmostEqual(r['conditional_energy_j_per_token'], 100 * r['optimistic_step_ms'] / 1000)

    def test_generic_work_unit(self):
        self.assertEqual(generic_roofline(1e12, 1e9, 10, self.a)['status'], 'CONDITIONAL_ROOFLINE_ONLY')
        self.assertFalse(generic_roofline(1, 1, 1000, self.a)['fits_memory'])

    def test_invalid_values_rejected(self):
        for kwargs in ({'context': 0}, {'kv_heads': 6}, {'head_dim': 127}, {'weight_bits': float('nan')}, {'batch': 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.w, **kwargs)
        for kwargs in ({'bulk_gbs_per_module': 0}, {'modules': 2}, {'weight_fast_fraction': .5},
                       {'bandwidth_utilization': 1.1}, {'tops_per_module': float('nan')}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.a, **kwargs)

    def test_scenarios_all_evaluate(self):
        for a in architectures():
            with self.subTest(a=a.name):
                self.assertIn(analyze(self.w, a)['status'], ['REJECT_CAPACITY', 'CONDITIONAL_ROOFLINE_ONLY'])


if __name__ == '__main__':
    unittest.main()
