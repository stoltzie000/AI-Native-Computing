"""Generate deterministic physically bounded *envelope* experiments only."""
import json
from dataclasses import replace
from network import Fabric, collective, integrate_v03
from scenarios import configurations, common_memory_system
from functional_collectives import demo
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulator_v0_3'))
from engine import Workload


def board_stress():
    base=Fabric(topology='mesh')
    variants=[
      ('optimistic_package_link_input',base),
      ('slower_board_link_input',replace(base,max_link_gbs=32,total_link_budget_gbs=256,
                                         payload_efficiency=.7,hop_latency_ns=1000,
                                         network_injection_latency_ns=500)),
      ('severe_board_link_input',replace(base,max_link_gbs=16,total_link_budget_gbs=128,
                                         payload_efficiency=.65,hop_latency_ns=3000,
                                         network_injection_latency_ns=1000)),
    ]
    w=Workload(context=32768)
    return [{'label':name,'assumptions':f.__dict__,
             'result':integrate_v03(w,common_memory_system(),f,algorithm='recursive_doubling')}
            for name,f in variants]


def run():
    f0=Fabric()
    size=Workload().hidden*Workload().activation_bits/8
    cases=[]
    for f in configurations():
        for algo in ('ring','recursive_doubling'):
            output=collective(f,size,algorithm=algo)
            cases.append({'config':f.__dict__,'algorithm':algo,'result':output})
    contexts=[]
    sys=common_memory_system()
    for ctx in (2048,8192,32768):
        w=Workload(context=ctx)
        rows=[]
        for f in configurations()[:5]:
            for algo in ('ring','recursive_doubling'):
                rows.append(integrate_v03(w,sys,f,algorithm=algo))
        contexts.append({'context':ctx,'rows':rows})
    return {'schema_version':'0.4','evidence_level':'E1 hypothetical resource/link scheduling',
            'evidence_disclaimers':[
                'No measured GPU or new hardware throughput. No hardware built.',
                'HBM4 36GB and >2.8TB/s per stack are vendor specifications, not achieved host usable rate.',
                'Link bandwidth, port budgets, per-hop latency and protocol efficiency are deliberately hypothetical; no routed PCB or package exists.',
                'UCIe 3.0 only applies to chiplet/package links; it is not evidence of a functioning motherboard link.',
                'Allreduce logical traffic simulated; reduction arithmetic not executed by timing model.',
                'No thermal/power/area/ECC link overhead model; no energy advantage claim.'
            ],
            'collective_comparisons':cases,'context_sensitivity':contexts,'board_link_stress':board_stress(),
            'cpu_collective_correctness_demo':demo()}

if __name__=='__main__':print(json.dumps(run(),sort_keys=True,indent=2,allow_nan=False))
