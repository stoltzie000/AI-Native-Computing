"""E1 analytical constraints. Not a PDK, PHY implementation or power measurement.

All GB, GB/s are SI decimal; GiB is binary. A transfer is only assumed
1 bit/transfer when users explicitly choose such an electrical scenario.
Never infer UCIe/board PHY properties from a raw data-rate specification.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

GB = 10**9


def finite(name: str, value: float, *, allow_zero=False):
    if type(value) not in (float, int) or not math.isfinite(value) or (value < 0 if allow_zero else value <= 0):
        raise ValueError(f'{name} must be finite and {"nonnegative" if allow_zero else "positive"}')


@dataclass(frozen=True)
class RawLinkHypothesis:
    """Raw electrical transfer scenario, NOT a demonstrated or UCIe-compliant link.

    raw_gbits_per_sec_per_lane is explicitly bits/sec, not an inferred GT/s.
    Full duplex requires two independent groups of unidirectional lanes.
    """
    raw_gbits_per_sec_per_lane: float
    encoding_fraction: float
    protocol_fraction: float
    max_unidirectional_lanes_per_port: int
    assumed_pj_per_delivered_bit: float | None = None

    def __post_init__(self):
        for x in ('raw_gbits_per_sec_per_lane', 'encoding_fraction', 'protocol_fraction'):
            finite(x, getattr(self,x))
        if self.encoding_fraction > 1 or self.protocol_fraction > 1:
            raise ValueError('fractions cannot exceed 1')
        if type(self.max_unidirectional_lanes_per_port) is not int or self.max_unidirectional_lanes_per_port < 1:
            raise ValueError('lane count must be a positive integer')
        if self.assumed_pj_per_delivered_bit is not None:
            finite('assumed_pj_per_delivered_bit',self.assumed_pj_per_delivered_bit)

    def needed_one_way_lanes(self, useful_GBs_per_s: float) -> int:
        finite('useful_GBs_per_s',useful_GBs_per_s)
        raw_required = useful_GBs_per_s * 8 / (self.raw_gbits_per_sec_per_lane*self.encoding_fraction*self.protocol_fraction)
        return math.ceil(raw_required - 1e-12)

    def envelope(self, useful_GBs_per_s:float, node_max_degree:int, links:int) -> dict:
        for name,value in (('node_max_degree',node_max_degree),('links',links)):
            if type(value) is not int or value < 1: raise ValueError(f'{name} must be positive int')
        lanes=self.needed_one_way_lanes(useful_GBs_per_s)
        total_duplex_lanes=2*lanes*links
        node_lanes=2*lanes*node_max_degree
        return {
          'status': 'REJECT_ASSUMED_LANE_PORT' if lanes>self.max_unidirectional_lanes_per_port else 'UNVERIFIED_ELECTRICAL_ENVELOPE',
          'requested_per_direction_payload_GBs_per_s': useful_GBs_per_s,
          'one_way_lanes_per_link':lanes,
          'duplex_lanes_per_link':2*lanes,
          'total_physical_unidirectional_lanes':total_duplex_lanes,
          'busiest_compute_node_lanes':node_lanes,
          'peak_aggregate_bidirectional_GBs_per_s':2*useful_GBs_per_s*links,
          'minimum_aggregate_link_phy_w_at_full_load':(
            2*useful_GBs_per_s*links*GB*8*self.assumed_pj_per_delivered_bit*1e-12
            if self.assumed_pj_per_delivered_bit is not None else None),
          'note':'Raw bit-rate scenario, not a specified PHY; excludes clocks, retimers, cooling, leakage, package traces, error handling and actual waveform validation.'
        }


def decode_traffic(weights_bytes: float, kv_bytes:float, raw_weight_fraction:float=1.0, raw_kv_fraction:float=1.0):
    for n,x in [('weights_bytes',weights_bytes),('kv_bytes',kv_bytes)]: finite(n,x,allow_zero=True)
    for n,x in [('raw_weight_fraction',raw_weight_fraction),('raw_kv_fraction',raw_kv_fraction)]:
        finite(n,x,allow_zero=True)
        if x>1:raise ValueError(n+' must be <= 1')
    return weights_bytes*raw_weight_fraction+kv_bytes*raw_kv_fraction


def same_bandwidth_double_speed(weights_bytes:float, kv_bytes:float, factor:float=2.0) -> dict:
    """To beat own *bandwidth roofline* by factor, fixing bandwidth+KV transfers.

    NOT a GPU benchmark and NOT evidence that skipped weights maintain AI quality.
    """
    finite('weights_bytes',weights_bytes)
    finite('kv_bytes',kv_bytes,allow_zero=True)
    finite('factor',factor)
    if factor<=1: raise ValueError('factor must exceed 1')
    budget=(weights_bytes+kv_bytes)/factor
    remaining_for_weights=budget-kv_bytes
    max_fraction=max(0,min(1,remaining_for_weights/weights_bytes))
    return {'factor':factor,'original_bytes':weights_bytes+kv_bytes,
            'allowed_total_bytes':budget,'fixed_kv_bytes':kv_bytes,
            'allowed_weight_fraction':max_fraction,
            'minimum_weight_traffic_reduction_fraction':1-max_fraction,
            'possible_by_weight_reduction_only':remaining_for_weights>=0,
            'quality_equivalence':'NOT_ESTABLISHED'}


@dataclass(frozen=True)
class AssumedPower:
    """Hypothetical power. Components do not constitute a system-level measurement."""
    compute_package_w: float
    hbm_stack_w:float
    module_count:int
    stacks_per_module:int
    host_w:float = 0
    cooling_overhead_fraction:float = 0
    phy_power_w:float | None = None
    allowed_system_w:float | None = None

    def __post_init__(self):
        for name in ('compute_package_w','hbm_stack_w'):
            finite(name,getattr(self,name))
        for name in ('host_w','cooling_overhead_fraction'):
            finite(name,getattr(self,name),allow_zero=True)
        for name in ('module_count','stacks_per_module'):
            v=getattr(self,name)
            if type(v) is not int or v < 1:raise ValueError(name+' must be positive integer')
        for name in ('phy_power_w','allowed_system_w'):
            if getattr(self,name) is not None:finite(name,getattr(self,name),allow_zero=True)

    def report(self):
        compute=self.compute_package_w*self.module_count
        memory=self.hbm_stack_w*self.module_count*self.stacks_per_module
        known=compute+memory+self.host_w
        phy=self.phy_power_w or 0
        total=(known+phy)*(1+self.cooling_overhead_fraction)
        return {'assumed_lower_envelope_w':total if self.phy_power_w is not None else None,
                'assumed_compute_w':compute,'assumed_hbm_w':memory,
                'phy_power_known':self.phy_power_w is not None,
                'status':('REJECT_ASSUMED_POWER' if self.allowed_system_w is not None and self.phy_power_w is not None and total>self.allowed_system_w
                          else 'UNVERIFIED_POWER_ENVELOPE'),
                'note':'Every component is a user-specified hypothesis; even nonrejection cannot prove physical viability.'}


def benchmark_comparability(reference:dict, candidate:dict):
    """Gate numerical hardware comparisons. Reject known mismatches; mark unknowns.

    A power comparison requires actual wall power measurements for both, NOT TDP.
    """
    required=('workload','context','batch','weight_bits','kv_bits','model_quality_verified',
              'memory_generation','memory_stacks','measured_timing','measured_wall_energy')
    for d in (reference,candidate):
        if any(k not in d for k in required): raise ValueError('incomplete benchmark record')
    mismatches=[k for k in ('workload','context','batch','weight_bits','kv_bits',
                           'memory_generation','memory_stacks') if reference[k]!=candidate[k]]
    if mismatches:return {'status':'REJECT_MATCHED_COMPARISON','mismatched_fields':mismatches}
    if not reference['model_quality_verified'] or not candidate['model_quality_verified']:
        return {'status':'BLOCK_QUALITY_UNVERIFIED','mismatched_fields':[]}
    if not reference['measured_timing'] or not candidate['measured_timing']:
        return {'status':'BLOCK_NO_PAIRED_TIMING','mismatched_fields':[]}
    if not reference['measured_wall_energy'] or not candidate['measured_wall_energy']:
        return {'status':'BLOCK_ENERGY_COMPARISON','mismatched_fields':[]}
    return {'status':'READY_FOR_STATISTICAL_REVIEW_NOT_PROVEN','mismatched_fields':[]}
