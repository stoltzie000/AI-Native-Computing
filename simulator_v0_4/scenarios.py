"""Evidence-labelled hypothetical profiles. HBM4 memory STACK spec != assembled system performance."""
from dataclasses import replace
from network import Fabric


def configurations():
    # Identical 8-node PHY-count budget for all topology variants. All latency,
    # total-link-budget and efficiency values remain research assumptions.
    return [
        Fabric(topology='ring'),
        Fabric(topology='mesh'),
        Fabric(topology='star',switch_budget_gbs=384),
        Fabric(topology='full'),  # deliberately rejected with 4 ports/module
        Fabric(topology='full',max_compute_ports=8),  # allows ports but divides equal budget across 28 links
        Fabric(topology='ring',payload_efficiency=.65),
        Fabric(topology='ring',hop_latency_ns=1000,network_injection_latency_ns=500),
        Fabric(topology='mesh',total_link_budget_gbs=512),
    ]


def common_memory_system():
    """One HBM4 stack/module envelope; complete physical design NOT established."""
    from pathlib import Path
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulator_v0_3'))
    from engine import System,Memory
    return System('8 x HBM4 one-stack-per-node hypothetical fabric',8,
                  Memory(36,2800,banks=16,sustained_fraction=.70),200,
                  fabric_gbs=800,fabric_latency_us=2,
                  provenance='36GB HBM4 stack public spec; 2.8TB/s published peak per stack; 70% sustained, compute, topology, package, power all assumptions')
