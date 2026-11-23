"""E1 network/link scheduling model for candidate AI compute fabrics.

NOT an electrical/PHY model, GPU benchmark, or timing characterization. Inputs
for latency, usable link bandwidth, topology, and per-message overhead are
independent hypothetical parameters. All byte/s units decimal. Topology
and synchronous collective schedule are simulated with directed link calendars.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque
import math
from typing import Hashable

GB = 10**9


def number(label: str, value: float, zero_ok: bool = False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (value < 0 if zero_ok else value <= 0):
        raise ValueError(f"{label} must be finite and {'nonnegative' if zero_ok else 'positive'}")


@dataclass(frozen=True)
class Fabric:
    nodes: int = 8
    topology: str = 'ring'  # ring, mesh, full, star
    max_compute_ports: int = 4
    max_link_gbs: float = 128.0  # per-direction hypothetical nominal payload rate ceiling
    total_link_budget_gbs: float = 1024.0  # total physical full-duplex link capacity, counted once per undirected link
    payload_efficiency: float = 0.85
    hop_latency_ns: float = 120.0  # assumed endpoint + switch/hop service
    network_injection_latency_ns: float = 80.0  # per message stage, sender overhead
    switch_budget_gbs: float | None = None  # if star, shared switch fabric rate; omitted = unconstrained
    # This is an optional parameter, never a default measured result.
    assumed_link_energy_pj_per_bit: float | None = None

    def __post_init__(self):
        if type(self.nodes) is not int or self.nodes < 2 or self.nodes > 64:
            raise ValueError('nodes must be integer 2..64')
        if self.topology not in ('ring', 'mesh', 'full', 'star'):
            raise ValueError('unsupported topology')
        if type(self.max_compute_ports) is not int or self.max_compute_ports < 1:
            raise ValueError('max_compute_ports must be positive integer')
        for key in ('max_link_gbs', 'total_link_budget_gbs', 'payload_efficiency'):
            number(key, getattr(self,key))
        for key in ('hop_latency_ns','network_injection_latency_ns'):
            number(key, getattr(self,key),zero_ok=True)
        if self.payload_efficiency > 1:
            raise ValueError('payload_efficiency <= 1 required')
        if self.switch_budget_gbs is not None:
            number('switch_budget_gbs', self.switch_budget_gbs)
        if self.assumed_link_energy_pj_per_bit is not None:
            number('assumed_link_energy_pj_per_bit', self.assumed_link_energy_pj_per_bit)
        if self.topology == 'mesh' and self.nodes not in (4, 8, 16):
            raise ValueError('mesh tested only for 2x2, 2x4, or 4x4')
        if self.topology == 'star' and self.max_compute_ports < 1:
            raise ValueError('star needs at least one compute port')


def edges(f: Fabric) -> list[tuple[Hashable,Hashable]]:
    n=f.nodes
    if f.topology=='ring':
        es = {(min(i,(i+1)%n), max(i,(i+1)%n)) for i in range(n)}
        return sorted(es)
    if f.topology=='full':
        return [(i,j) for i in range(n) for j in range(i+1,n)]
    if f.topology=='star':
        return [(i,'S') for i in range(n)]
    width=2 if n == 4 else 4
    es=[]
    for node in range(n):
        r,c=divmod(node,width)
        if c+1<width: es.append((node,node+1))
        if node+width<n: es.append((node,node+width))
    return es


def adjacency(f: Fabric):
    adj={i:[] for i in range(f.nodes)}
    if f.topology=='star':adj['S']=[]
    for a,b in edges(f):
        adj[a].append(b);adj[b].append(a)
    for k in adj:adj[k].sort(key=lambda x: (isinstance(x,str),str(x)))
    return adj


def validate_physical(f: Fabric) -> dict:
    es=edges(f)
    adj=adjacency(f)
    max_degree=max(len(adj[i]) for i in range(f.nodes))
    if max_degree > f.max_compute_ports:
        return {'status':'REJECT_PORTS','required_ports_per_node':max_degree,
                'available_ports_per_node':f.max_compute_ports,
                'physical_links':len(es)}
    allocated=min(f.max_link_gbs,f.total_link_budget_gbs/len(es))
    return {'status':'FEASIBLE_PARAMETER_ENVELOPE',
            'required_ports_per_node':max_degree,
            'available_ports_per_node':f.max_compute_ports,
            'physical_links':len(es),
            'allocated_link_gbs_per_direction':allocated,
            'useful_link_gbs_per_direction':allocated*f.payload_efficiency,
            'total_allocated_gbs':allocated*len(es),
            'note':'Port and bandwidth budget checks only; actual PHY, trace length, placement, thermals, reticle and power unresolved'}


def path(f: Fabric, source: Hashable, destination: Hashable) -> list[Hashable]:
    adj=adjacency(f)
    if source not in adj or destination not in adj or source==destination:
        raise ValueError('distinct valid endpoints required')
    todo=deque([source]); prev={source:None}
    while todo:
        u=todo.popleft()
        if u==destination:break
        for v in adj[u]:
            if v not in prev:
                prev[v]=u;todo.append(v)
    if destination not in prev:raise AssertionError('topology unexpectedly disconnected')
    result=[];cur=destination
    while cur is not None:
        result.append(cur);cur=prev[cur]
    return result[::-1]


def ring_order(f:Fabric, optimize=True):
    if not optimize or f.topology != 'mesh':return list(range(f.nodes))
    if f.nodes==4:return [0,1,3,2]
    if f.nodes==8:return [0,1,2,3,7,6,5,4]
    # For 4x4 grid: exterior perimeter followed by interior path.
    return [0,1,2,3,7,11,15,14,10,6,5,9,13,12,8,4]


def messages_for_stage(n:int, algorithm:str, stage:int, elements_bytes:float, order:list[int]):
    if algorithm=='ring':
        # ring all-reduce (reduce-scatter followed by all-gather): 2(n-1)
        # stages, each node sends one shard in each stage. Only traffic
        # scheduling is simulated here, not numeric reduction operations.
        return [(order[i],order[(i+1)%n],elements_bytes/n) for i in range(n)]
    if algorithm=='recursive_doubling':
        if n&(n-1):raise ValueError('recursive doubling requires power-of-two nodes')
        # log2(n) stages, each partner sends the whole vector
        return [(i, i^(1<<stage), elements_bytes) for i in range(n)]
    raise ValueError('algorithm must be ring or recursive_doubling')


def collective(f: Fabric, elements_bytes: float, algorithm='ring', optimize_ring=True,
               save_events=False) -> dict:
    number('elements_bytes',elements_bytes)
    envelope=validate_physical(f)
    result={'topology':f.topology,'algorithm':algorithm,'nodes':f.nodes,
            'payload_bytes_per_node':elements_bytes,'port_and_budget':envelope,
            'status':envelope['status']}
    if envelope['status']!='FEASIBLE_PARAMETER_ENVELOPE':return result
    if algorithm not in ('ring','recursive_doubling'):
        raise ValueError('unknown collective')
    if algorithm=='recursive_doubling' and f.nodes&(f.nodes-1):
        raise ValueError('recursive doubling only for power-of-two module count')
    num_stages=2*(f.nodes-1) if algorithm=='ring' else (f.nodes.bit_length()-1)
    ring=ring_order(f,optimize_ring)
    # Link is a full-duplex resource: A->B and B->A have independent calendars.
    available={}
    network_time=0.0
    total_link_bytes=0.0
    total_wire_messages=0
    max_hops=0
    events=[]
    effective_bw=envelope['useful_link_gbs_per_direction']*GB
    switch_ready=0.0
    for s in range(num_stages):
        stage_start=network_time
        stage_end=stage_start
        msgs=messages_for_stage(f.nodes,algorithm,s,elements_bytes,ring)
        for src,dst,amount in msgs:
            route=path(f,src,dst)
            max_hops=max(max_hops,len(route)-1)
            ready=stage_start+f.network_injection_latency_ns*1e-9
            for a,b in zip(route,route[1:]):
                edge=(a,b)
                begin=max(ready,available.get(edge,0.0))
                if f.topology=='star' and a=='S' and f.switch_budget_gbs is not None:
                    begin=max(begin,switch_ready)
                finish=begin+f.hop_latency_ns*1e-9 + amount/effective_bw
                # Shared switch crossbar serialized when explicitly configured.
                if f.topology=='star' and a=='S' and f.switch_budget_gbs is not None:
                    finish=max(finish,begin+amount/(f.switch_budget_gbs*GB))
                    switch_ready=finish
                available[edge]=finish
                ready=finish
                total_link_bytes+=amount
                total_wire_messages+=1
            stage_end=max(stage_end,ready)
            if save_events and s<2 and src<2:
                events.append({'stage':s,'sender':src,'receiver':dst,
                               'hop_count':len(route)-1,'arrival_us':round(ready*1e6,5)})
        network_time=stage_end
    total_injected_bytes=f.nodes*(2*(f.nodes-1)*(elements_bytes/f.nodes)
                                   if algorithm=='ring' else (f.nodes.bit_length()-1)*elements_bytes)
    assert total_link_bytes+1e-6>=total_injected_bytes
    result.update(status='SIMULATED_ENVELOPE',stages=num_stages,
                  latency_us=network_time*1e6,
                  link_bytes=total_link_bytes,
                  logical_injected_bytes=total_injected_bytes,
                  hop_message_count=total_wire_messages,
                  max_route_hops=max_hops,
                  wire_amplification=total_link_bytes/total_injected_bytes,
                  assumed_link_energy_j=(total_link_bytes*8*f.assumed_link_energy_pj_per_bit*1e-12
                                          if f.assumed_link_energy_pj_per_bit is not None else None),
                  sample_events=events if save_events else None)
    return result


def integrate_v03(workload, system, f:Fabric, algorithm='ring', optimize_ring=True):
    """Add explicit collective service to v0.3 memory+compute timing.

    V0.3 uses layer barriers. Set its fabric cost approximately zero and replace
    with 2*layers * this network scheduler's standalone repeated collective cost.
    No overlapping collectives, no concurrent inference requests, no measured PHY.
    """
    from dataclasses import replace
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulator_v0_3'))
    from engine import simulate
    if system.modules!=f.nodes:raise ValueError('node mismatch')
    base=simulate(workload,replace(system,fabric_gbs=1e15,fabric_latency_us=0))
    if base['status']!='SIMULATED':return {'status':base['status'],'reason':base.get('reason')}
    communication=collective(f,workload.hidden*workload.batch*workload.activation_bits/8,
                              algorithm=algorithm,optimize_ring=optimize_ring)
    if communication['status']!='SIMULATED_ENVELOPE':return communication
    network_time_s=communication['latency_us']*1e-6*system.collectives_per_layer*workload.layers
    # v0.3 zero-fabric retains an infinitesimal serialization term (<1ns).
    total_s=base['decode_step_ms']/1000+network_time_s
    return {'status':'SIMULATED_ENVELOPE', 'topology':f.topology,'algorithm':algorithm,
            'context':workload.context,'modules':f.nodes,
            'base_memory_compute_ms':base['decode_step_ms'],
            'all_collectives_ms':round(network_time_s*1000,6),
            'step_ms':round(total_s*1000,6),
            'conditional_steps_per_second':round(1/total_s,5),
            'network':communication}
