"""Published capacities/bandwidths; all performance efficiencies and TOPS are assumed.

The speculative design examples are explicitly NOT engineering specifications.
"""
from model import Architecture


def architectures():
    return [
        Architecture('RTX 5090 peak-memory reference', 1, 32, 1792, 100,
                     provenance='NVIDIA published memory peak; 100 TOPS hypothetical comparable-workload ceiling'),
        Architecture('H200 peak-memory reference', 1, 141, 4800, 100,
                     provenance='NVIDIA published memory peak; 100 TOPS hypothetical comparable-workload ceiling'),
        Architecture('MI355X peak-memory reference', 1, 288, 8000, 100,
                     provenance='AMD published memory peak; 100 TOPS hypothetical comparable-workload ceiling'),
        Architecture('Near-memory fabric 8-node hypothesis', 8, 16, 900, 40,
                     fabric_gbs=200, fabric_latency_us=2,
                     provenance='ALL component values speculative design inputs'),
        Architecture('SRAM-centric fabric 4-node hypothesis', 4, 4, 500, 100,
                     fast_gb_per_module=12, fast_gbs_per_module=8000,
                     weight_fast_fraction=1, kv_fast_fraction=1,
                     fabric_gbs=400, fabric_latency_us=1,
                     provenance='ALL component values speculative; 48 GB SRAM + 32 TB/s aggregate not validated'),
        Architecture('PIM-centric fabric 16-node hypothesis', 16, 8, 1000, 40,
                     fabric_gbs=100, fabric_latency_us=5,
                     provenance='ALL component values speculative; models bulk traffic not true PIM internal dataflow'),
    ]
