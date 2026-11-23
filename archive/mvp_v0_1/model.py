#!/usr/bin/env python3
"""First-order, auditable LLM decode accelerator feasibility model. No measured silicon claims."""
import argparse, json
from dataclasses import dataclass, asdict
@dataclass
class Config:
    parameters_b: float = 30
    bits_per_weight: float = 4
    metadata_fraction: float = .10
    kv_gb: float = 2
    bandwidth_gbs: float = 1792
    bandwidth_utilization: float = .65
    compute_tops: float = 100
    compute_utilization: float = .5
    watts: float = 350
    fixed_cost_usd: float = 2500
    extra_bytes_per_token_gb: float = 0

def evaluate(c):
    weight_gb = c.parameters_b * c.bits_per_weight / 8 * (1+c.metadata_fraction)
    capacity_gb = weight_gb+c.kv_gb
    bytes_token_gb = weight_gb+c.extra_bytes_per_token_gb
    bandwidth_tps = c.bandwidth_gbs*c.bandwidth_utilization/bytes_token_gb
    compute_tps = c.compute_tops*1e12*c.compute_utilization/(2*c.parameters_b*1e9)
    tps = min(bandwidth_tps,compute_tps)
    return {'weights_gb':weight_gb,'required_capacity_gb':capacity_gb,'bandwidth_limit_tps':bandwidth_tps,'compute_limit_tps':compute_tps,'estimated_decode_tps':tps,'estimated_tokens_per_joule':tps/c.watts,'hardware_usd_per_tps':c.fixed_cost_usd/tps,'limiting_factor':'bandwidth' if bandwidth_tps<compute_tps else 'compute'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--bandwidth-gbs',type=float,default=1792)
    p.add_argument('--bandwidth-utilization',type=float,default=.65)
    p.add_argument('--compute-tops',type=float,default=100)
    p.add_argument('--watts',type=float,default=350)
    p.add_argument('--cost',type=float,default=2500)
    p.add_argument('--bits',type=float,default=4)
    p.add_argument('--parameters-b',type=float,default=30)
    p.add_argument('--kv-gb',type=float,default=2)
    a=p.parse_args()
    c=Config(parameters_b=a.parameters_b,bits_per_weight=a.bits,kv_gb=a.kv_gb,bandwidth_gbs=a.bandwidth_gbs,bandwidth_utilization=a.bandwidth_utilization,compute_tops=a.compute_tops,watts=a.watts,fixed_cost_usd=a.cost)
    assert c.bandwidth_gbs>0 and 0<c.bandwidth_utilization<=1 and c.compute_tops>0 and c.watts>0 and c.fixed_cost_usd>0 and c.parameters_b>0 and c.bits_per_weight>0 and c.kv_gb>=0
    print(json.dumps({'inputs':asdict(c),'outputs':evaluate(c)},indent=2))
if __name__=='__main__':main()
