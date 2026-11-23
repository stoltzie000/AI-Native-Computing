"""No measured device rates. Every throughput is an E1 conditional scenario.

Runs from the source directory or from repository root. Python standard lib only.
"""
from __future__ import annotations
import json
from dataclasses import asdict, replace
from equal_resources import IsoResources,run_equalized
from constraints import RawLinkHypothesis,same_bandwidth_double_speed,AssumedPower,benchmark_comparability
from package_screen import PackageHeatHypothesis,conditional_best,hidden_overhead_crossover_ms
from sparse_reference import demo as sparse_demo
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulator_v0_3'))
from engine import Workload


def execute():
    resource=IsoResources()
    w=Workload(context=32768)
    nominal=run_equalized(resource)
    sizes={str(c):run_equalized(IsoResources(context=c)) for c in (2048,8192,32768)}
    lowbw=run_equalized(IsoResources(sustained_fraction=.4))
    board=run_equalized(resource,link_gbs=16,link_budget_gbs=128,hop_ns=3000,injection_ns=1000)
    physical_what_if=RawLinkHypothesis(raw_gbits_per_sec_per_lane=64,encoding_fraction=.98,protocol_fraction=.85,
                                    max_unidirectional_lanes_per_port=32,assumed_pj_per_delivered_bit=.3)
    physical_result=physical_what_if.envelope(128,node_max_degree=3,links=10)
    power=AssumedPower(compute_package_w=275,hbm_stack_w=20,module_count=8,stacks_per_module=1,
                      host_w=150,cooling_overhead_fraction=.20,phy_power_w=6.144).report()
    # Raw arithmetic only. Low-bit quality, quantizer structure and compute changes are not validated.
    bit_sensitivity=[]
    reference_bytes=w.weight_bytes+w.kv_step_bytes
    for bits in (16,8,4,2,1):
        ww=replace(w,weight_bits=bits)
        byte_total=ww.weight_bytes+ww.kv_step_bytes
        bit_sensitivity.append({'weight_bits':bits,'weight_gb':ww.weight_bytes/1e9,
                                'kv_step_gb':ww.kv_step_bytes/1e9,
                                'total_gb_per_step':byte_total/1e9,
                                'ideal_speed_relative_to_4bit_weights':reference_bytes/byte_total,
                                'quality_equivalence':'NOT_ESTABLISHED'})
    heat=PackageHeatHypothesis(total_compute_w=2200,hbm_stack_w=20,total_stacks=8,
                               per_package_heat_limit_w=1400,link_phy_w_per_package=0)
    a=[dict(workload='Qwen2.5-32B analytical proxy',context=32768,batch=1,weight_bits=4,kv_bits=16,
            model_quality_verified=False,memory_generation='HBM4',memory_stacks=8,
            measured_timing=False,measured_wall_energy=False) for _ in range(2)]
    return {'schema_version':'0.5','evidence_level':'E1 only',
       'warning':'No new GPU measurements; no physical ASIC, motherboard or PHY measurements. Every throughput is a hypothetical calculation.',
       'reference_vendor_specs':{
         'NVIDIA_Rubin_2026':'288GB HBM4, 22TB/s nominal peak, 3.6TB/s NVLink bandwidth; these are not workload benchmarks',
         'Micron_HBM4':'36GB 12H, greater than 2.8TB/s peak per stack (2.8 used conservatively in scenarios)',
         'UCIe_4_0':'2026 consortium page describes on-package memory links up to 93.75% data efficiency; does not apply to motherboard'},
       'equalized_profiles':nominal,
       'context_sensitivity':sizes,
       'sustained_40_percent':lowbw,
       'board_link_stress':board,
       'weight_precision_traffic_sensitivity':bit_sensitivity,
       'minimum_memory_traffic':{
          'weight_gb':w.weight_bytes/1e9,'kv_step_gb':w.kv_step_bytes/1e9,
          'ideal_70pct_bandwidth_only_steps_per_s':(resource.stacks*resource.peak_gbs_per_stack*resource.sustained_fraction*1e9)/(w.weight_bytes+w.kv_step_bytes),
          'weight_only_reduction_needed_for_2x_traffic_reduction_at_equal_bandwidth':same_bandwidth_double_speed(w.weight_bytes,w.kv_step_bytes,2),
          'disclaimer':'This is a traffic-bound thought experiment. Removing weights or reducing precision can degrade model quality.'},
       'conditional_lane_screen':{'hypothetical_raw_link':asdict(physical_what_if),'result':physical_result,
           'warning':'64 Gbit/s per lane is a chosen hypothetical line-rate, not an inference from UCIe 64 GT/s. 0.3 pJ/bit is an illustrative assumed energy number, NOT a measured board or PHY.'},
       'conditional_power_sensitivity':{'input':'8 compute packages x 275W + 8 HBM x 20W + 150W host + assumed 6.144W dynamic link + 20% cooling allowance','result':power},
       'conditional_package_heat':conditional_best(nominal['rows'],heat),
       'hidden_central_package_overhead_threshold_ms':hidden_overhead_crossover_ms(nominal['rows'][0],nominal['rows'][1]),
       'exact_zero_block_sparse_functional_demo':sparse_demo(),
       'benchmark_readiness':benchmark_comparability(a[0],a[1]),
       'missing_for_E4':['equivalent task-quality measurements','matched measured GPU trace','physical interconnect design','package floorplan','realistic HBM+compute+PHY power','clocked RTL or FPGA measurement','working physical hardware and wall power meter','confidence intervals']}

if __name__=='__main__':
    print(json.dumps(execute(),indent=2,sort_keys=True,allow_nan=False))
