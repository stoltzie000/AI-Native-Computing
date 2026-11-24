"""E1 memory movement accounting for one 64-value QACT row, SI bytes.
A synthetic burst-rounding model, not DRAM/PHY timing or model accuracy.
"""
from dataclasses import dataclass
from math import ceil
def round_up(x,b): return ceil(x/b)*b
@dataclass(frozen=True)
class Scenario:
    n:int
    burst:int=64
    q_bytes:int=64
    offset_bytes:int=8
    scale_bytes:int=4
    external_raw_load:bool=True
    def __post_init__(self):
        if type(self.n) is not int or self.n<1:raise ValueError("n >=1")
        if type(self.burst) is not int or self.burst<1 or self.burst&(self.burst-1):raise ValueError("power of two burst")
        if any(type(v) is not int or v<0 for v in (self.q_bytes,self.offset_bytes,self.scale_bytes)):raise ValueError("nonnegative byte sizes")
        if type(self.external_raw_load) is not bool:raise ValueError("external load bool")
    def account(self):
        raw=64*4
        packed=self.q_bytes+self.offset_bytes+self.scale_bytes
        raw_read=round_up(raw,self.burst)
        compressed=round_up(packed,self.burst)
        float_traffic=self.n*raw_read
        quant_traffic=(raw_read if self.external_raw_load else 0)+compressed*(1+self.n)
        return dict(evidence_class="E1_SYNTHETIC_BURST_TRAFFIC_ONLY",
                    useful_raw_bytes=raw,useful_quant_bytes=packed,
                    raw_burst_bytes=raw_read,quant_burst_bytes=compressed,
                    repeated_raw_traffic=float_traffic,
                    quantized_total_traffic=quant_traffic,
                    saved_bytes=float_traffic-quant_traffic,
                    reaches_break_even=quant_traffic<=float_traffic,
                    independent_model_accuracy_verified=False,
                    hardware_latency_or_energy_known=False)
if __name__=="__main__":
    for external in [True,False]:
        for n in [1,2,3,4,8]:
            a=Scenario(n=n,external_raw_load=external).account()
            print(f"external_raw_load={external} reads={n} raw={a['repeated_raw_traffic']} quant={a['quantized_total_traffic']} saved={a['saved_bytes']}")
