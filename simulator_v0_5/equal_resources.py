"""Controlled equal-memory & compute *hypotheses*. Imports earlier E1 simulators.

Standalone centralized vs 2/4/8 distributed memory-compute layouts share exactly
8 HBM4 stacks, 288GB, 22.4TB/s nominal and 1600 synthetic TOPS.
No actual design has been physically implemented. This experiment deliberately
removes the 'more HBM than the GPU' confound from the older v0.4 comparison.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from dataclasses import replace
import sys
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulator_v0_3'))
sys.path.insert(0,str(ROOT/'simulator_v0_4'))
from engine import System, Memory, Workload, simulate
from network import Fabric, integrate_v03


@dataclass(frozen=True)
class IsoResources:
    stacks:int=8
    capacity_gb_per_stack:float=36
    peak_gbs_per_stack:float=2800
    total_compute_tops:float=1600
    sustained_fraction:float=.70
    compute_fraction:float=1.0
    context:int=32768
    tiles:int=16

    def __post_init__(self):
        if type(self.stacks) is not int or self.stacks<1:raise ValueError('stacks positive integer')
        if type(self.context) is not int or self.context<1:raise ValueError('context positive integer')
        if type(self.tiles) is not int or self.tiles<1:raise ValueError('tiles positive integer')
        for n in ('capacity_gb_per_stack','peak_gbs_per_stack','total_compute_tops','sustained_fraction','compute_fraction'):
            x=getattr(self,n)
            if not isinstance(x,(float,int)) or isinstance(x,bool) or not 0 < x <= 1e12:raise ValueError(n)
        if self.sustained_fraction>1 or self.compute_fraction>1:raise ValueError('fraction > 1')


def system_for(n:int,resource:IsoResources) -> System:
    if type(n) is not int or n not in (1,2,4,8) or resource.stacks % n:
        raise ValueError('supported module counts are 1,2,4,8 dividing stack count')
    s=resource.stacks//n
    return System(name=f'Equal-HBM4-envelope {n} compute package(s) x {s} HBM4 stacks',
                  modules=n,
                  bulk=Memory(s*resource.capacity_gb_per_stack,
                              s*resource.peak_gbs_per_stack,banks=16,
                              sustained_fraction=resource.sustained_fraction),
                  compute_tops_per_module=resource.total_compute_tops/n,
                  compute_fraction=resource.compute_fraction,
                  tiles_per_phase=resource.tiles,
                  fabric_gbs=1e12 if n>1 else 0,
                  fabric_latency_us=0,
                  provenance='Same total resource budget, all compute utilization and electrical viability hypothetical')


def run_equalized(resource:IsoResources, *, link_gbs:float=128, link_budget_gbs:float=1024,
                  hop_ns:float=120, injection_ns:float=80) -> dict:
    workload=Workload(context=resource.context)
    out=[]
    for n in (1,2,4,8):
        system=system_for(n,resource)
        if n==1:
            raw=simulate(workload,system)
            result={'status': 'SIMULATED_ENVELOPE' if raw['status']=='SIMULATED' else raw['status'],
                    'conditional_steps_per_second':raw.get('conditional_steps_per_second'),
                    'step_ms':raw.get('decode_step_ms'),
                    'base_memory_compute_ms':raw.get('decode_step_ms'),
                    'all_collectives_ms':0.0,'reference_method':'v0.3 sequential layer schedule'}
        else:
            topo='ring' if n==2 else 'mesh'
            f=Fabric(nodes=n,topology=topo,max_link_gbs=link_gbs,total_link_budget_gbs=link_budget_gbs,
                     hop_latency_ns=hop_ns,network_injection_latency_ns=injection_ns)
            result=integrate_v03(workload,system,f,algorithm='recursive_doubling')
        out.append({'packages':n,'hbm_stacks_per_package':resource.stacks//n,
                    'total_hbm_stacks':resource.stacks,
                    'total_nominal_memory_bandwidth_GBs_per_second':resource.stacks*resource.peak_gbs_per_stack,
                    'total_hypothetical_compute_TOPS':resource.total_compute_tops,
                    'result':result})
    return {'evidence':'E1 conditional analytical, no measured silicon','resource':resource.__dict__,
            'all_packages_share_memory_compute_budget':True,'rows':out}


def include_clocks_and_interface_overhead(result:dict, *, pad_ms:float=0.0):
    # Do not silently add system overhead in simulator itself.
    if pad_ms<0:raise ValueError('pad_ms nonnegative')
    # This is a forward sensitivity function only; no measured overhead is supplied.
    return [{'packages':r['packages'], 'steps_per_s_with_extra_overhead':(
        round(1000/(r['result']['step_ms']+pad_ms),5) if r['result'].get('step_ms') else None)} for r in result['rows']]
