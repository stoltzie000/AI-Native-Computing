"""E1 best-case weight-memory traffic bounds. NOT measured chip speed."""
from dataclasses import dataclass
from math import ceil, isfinite

@dataclass(frozen=True)
class TrafficScenario:
    weight_gb: float = 17.875
    kv_gb: float = 8.590
    zero_activation_fraction: float = 0.0
    metadata_gb: float = 0.0

    def __post_init__(self):
        for v in (self.weight_gb,self.kv_gb,self.zero_activation_fraction,self.metadata_gb):
            if not isinstance(v,(int,float)) or not isfinite(v):
                raise ValueError("nonfinite traffic parameter")
        if self.weight_gb<=0 or self.kv_gb<0 or self.metadata_gb<0:
            raise ValueError("invalid byte-volume assumption")
        if not 0<=self.zero_activation_fraction<=1:
            raise ValueError("zero activation fraction outside [0,1]")

    @property
    def original_gb(self):
        return self.weight_gb+self.kv_gb

    @property
    def gated_gb(self):
        return self.weight_gb*(1-self.zero_activation_fraction)+self.kv_gb+self.metadata_gb

    @property
    def best_case_bandwidth_speedup(self):
        return self.original_gb/self.gated_gb

    def required_zero_fraction(self,target_speedup):
        if target_speedup<=0 or not isfinite(target_speedup):
            raise ValueError("invalid speedup target")
        return (self.weight_gb+self.kv_gb+self.metadata_gb-(self.original_gb/target_speedup))/self.weight_gb

def cycle_lower_bound(block_size=4,active_columns=4,request_extra_cycles=2):
    """Illustrative independent serialized-request FSM cycle minimum.

    One scan per weight, and request_extra_cycles per fetched weight.
    No overlap, no contention. Controller accept/done = 2 cycles.
    Not an RTL trace nor comparable to preload-only v0.7 cycles.
    """
    if not all(isinstance(x,int) for x in (block_size,active_columns,request_extra_cycles)):
        raise ValueError("cycles must be integer")
    if block_size<1 or active_columns<0 or active_columns>block_size or request_extra_cycles<2:
        raise ValueError("invalid work size or memory latency")
    cells=block_size**2
    reads=block_size*active_columns
    return {"dense_reads":cells,"issued_reads":reads,"skipped_reads":cells-reads,
            "minimum_fsm_cycles":2+cells+reads*request_extra_cycles}
