"""Independent analytical oracles, negative tests, conservation and monotonicity."""
import unittest
from dataclasses import replace
import math

from network import Fabric, GB, adjacency, collective, edges, path, integrate_v03, validate_physical
from scenarios import common_memory_system


class PhysicalBounds(unittest.TestCase):
    def test_ring_ports_and_links(self):
        f=Fabric(nodes=8,topology='ring')
        r=validate_physical(f)
        self.assertEqual(r['required_ports_per_node'],2)
        self.assertEqual(r['physical_links'],8)
        self.assertAlmostEqual(r['allocated_link_gbs_per_direction'],128)

    def test_complete_graph_rejected_at_four_ports(self):
        r=collective(Fabric(nodes=8,topology='full'),10240)
        self.assertEqual(r['status'],'REJECT_PORTS')
        self.assertEqual(r['port_and_budget']['required_ports_per_node'],7)

    def test_complete_graph_divides_fixed_wiring_budget(self):
        f=Fabric(topology='full',max_compute_ports=8)
        r=validate_physical(f)
        self.assertEqual(r['physical_links'],28)
        self.assertAlmostEqual(r['allocated_link_gbs_per_direction'],1024/28)
        self.assertAlmostEqual(r['total_allocated_gbs'],1024)

    def test_mesh_edge_count(self):
        self.assertEqual(len(edges(Fabric(topology='mesh',nodes=8))),10)
        self.assertEqual(len(edges(Fabric(topology='mesh',nodes=16))),24)

    def test_mesh_routing(self):
        f=Fabric(nodes=8,topology='mesh')
        self.assertEqual(len(path(f,0,7))-1,4)
        self.assertEqual(len(path(f,0,4))-1,1)

    def test_reject_invalid_parameter(self):
        with self.assertRaises(ValueError):Fabric(total_link_budget_gbs=0)
        with self.assertRaises(ValueError):Fabric(payload_efficiency=1.2)
        with self.assertRaises(ValueError):Fabric(hop_latency_ns=-1)
        with self.assertRaises(ValueError):Fabric(max_compute_ports=0)
        with self.assertRaises(ValueError):Fabric(topology='mesh',nodes=3)
        with self.assertRaises(ValueError):Fabric(max_link_gbs=float('nan'))
        with self.assertRaises(ValueError):Fabric(assumed_link_energy_pj_per_bit=-1)


class CollectiveArithmetic(unittest.TestCase):
    def test_two_node_ring_closed_form(self):
        f=Fabric(nodes=2,topology='ring',max_compute_ports=1,
                 max_link_gbs=10,total_link_budget_gbs=10,payload_efficiency=1,
                 hop_latency_ns=200,network_injection_latency_ns=100)
        amount=1000000
        r=collective(f,amount,algorithm='ring')
        expected=2*(300e-9+amount/2/(10*GB))
        self.assertAlmostEqual(r['latency_us']*1e-6,expected,places=12)
        self.assertAlmostEqual(r['logical_injected_bytes'],2*amount)
        self.assertAlmostEqual(r['link_bytes'],2*amount)
        self.assertEqual(r['stages'],2)

    def test_two_node_recursive_doubling_closed_form(self):
        f=Fabric(nodes=2,topology='ring',max_compute_ports=1,
                 max_link_gbs=10,total_link_budget_gbs=10,payload_efficiency=1,
                 hop_latency_ns=200,network_injection_latency_ns=100)
        amount=1000000
        r=collective(f,amount,algorithm='recursive_doubling')
        expected=300e-9+amount/(10*GB)
        self.assertAlmostEqual(r['latency_us']*1e-6,expected,places=12)
        self.assertEqual(r['stages'],1)
        self.assertEqual(r['logical_injected_bytes'],2*amount)

    def test_ring_volume_independent_of_topology(self):
        for topo in ('ring','mesh','star','full'):
            f=Fabric(topology=topo,max_compute_ports=8)
            r=collective(f,10240)
            self.assertAlmostEqual(r['logical_injected_bytes'],2*(8-1)*10240)
            self.assertGreaterEqual(r['link_bytes'],r['logical_injected_bytes'])

    def test_mesh_optimized_ring_has_unit_hops(self):
        f=Fabric(topology='mesh')
        a=collective(f,10240,optimize_ring=True)
        b=collective(f,10240,optimize_ring=False)
        self.assertEqual(a['wire_amplification'],1)
        self.assertGreater(b['wire_amplification'],1)
        self.assertLess(a['latency_us'],b['latency_us'])

    def test_recursive_doubling_three_stages(self):
        f=Fabric(topology='mesh')
        r=collective(f,10240,algorithm='recursive_doubling')
        self.assertEqual(r['stages'],3)
        self.assertAlmostEqual(r['logical_injected_bytes'],3*8*10240)

    def test_more_link_budget_faster_or_equal(self):
        lo=Fabric(topology='mesh',total_link_budget_gbs=256)
        hi=replace(lo,total_link_budget_gbs=1024)
        self.assertLessEqual(collective(hi,4000000)['latency_us'],
                             collective(lo,4000000)['latency_us'])

    def test_more_hop_delay_increases_latency(self):
        lo=Fabric(topology='mesh')
        hi=replace(lo,hop_latency_ns=lo.hop_latency_ns+1000)
        self.assertGreater(collective(hi,10240)['latency_us'],
                           collective(lo,10240)['latency_us'])

    def test_smaller_efficiency_slower(self):
        f=Fabric(topology='ring')
        self.assertGreater(collective(replace(f,payload_efficiency=.5),10240)['latency_us'],
                           collective(f,10240)['latency_us'])

    def test_more_data_not_faster(self):
        f=Fabric(topology='star',switch_budget_gbs=128)
        self.assertGreater(collective(f,1e7)['latency_us'],collective(f,1e6)['latency_us'])

    def test_energy_unknown_unless_assumed(self):
        r=collective(Fabric(),10240)
        self.assertIsNone(r['assumed_link_energy_j'])
        f=Fabric(assumed_link_energy_pj_per_bit=1)
        a=collective(f,10240)
        self.assertAlmostEqual(a['assumed_link_energy_j'],a['link_bytes']*8e-12)

    def test_not_power_of_two_recursive_rejected(self):
        with self.assertRaises(ValueError):
            collective(Fabric(nodes=6),10240,algorithm='recursive_doubling')

    def test_trace_doesnt_change_timing(self):
        a=collective(Fabric(),10240,save_events=False)
        b=collective(Fabric(),10240,save_events=True)
        self.assertEqual(a['latency_us'],b['latency_us'])
        self.assertTrue(b['sample_events'])

    def test_integration_module_mismatch(self):
        from pathlib import Path
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulator_v0_3'))
        from engine import Workload
        with self.assertRaises(ValueError):
            integrate_v03(Workload(),common_memory_system(),Fabric(nodes=4))

    def test_integration_slower_with_slower_links(self):
        from pathlib import Path
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulator_v0_3'))
        from engine import Workload
        w=Workload(context=2048)
        s=common_memory_system()
        lo=Fabric(topology='mesh',total_link_budget_gbs=128)
        hi=replace(lo,total_link_budget_gbs=1024)
        a=integrate_v03(w,s,lo,algorithm='recursive_doubling')
        b=integrate_v03(w,s,hi,algorithm='recursive_doubling')
        self.assertGreater(a['step_ms'],b['step_ms'])
        self.assertLess(a['conditional_steps_per_second'],b['conditional_steps_per_second'])

if __name__=='__main__':unittest.main()
