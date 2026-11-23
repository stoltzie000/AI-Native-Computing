"""Reproducible deterministic sensitivity report; no measured hardware numbers."""
import json
from dataclasses import replace
from engine import Workload, simulate
from scenarios import reference_systems, research_systems
from functional_microkernel import demo


def run():
    data = {"schema_version": "v0.3", "evidence_level": "E1 model; not hardware measurement",
            "assumptions": ["Single autoregressive decode step, batch=1, no prefill/quality measurements",
                "Tensor-parallel head-sharded synchronous execution", "Layers have 4 ordered subphases (QKV, attention, O projection, MLP) with 2 collectives; no cross-layer overlap",
                "GPU capacity and memory peak from vendors; all other hardware service assumptions synthetic",
                "One aggregate fabric, no physical topology/power/area model",
                "No system power estimates, therefore no energy-efficiency conclusions"],
            "experiments": []}
    for context in (2048, 8192, 32768):
        w = Workload(context=context)
        rows = [simulate(w, s, record_first_layer=(context == 32768))
                for s in reference_systems() + research_systems()]
        data["experiments"].append({"workload":w.name, "context":context, "results":rows})
    base = research_systems()[1]
    cases = [
      ("default", base),
      ("70pct_useful_bulk", replace(base, bulk=replace(base.bulk, sustained_fraction=.7))),
      ("40pct_useful_bulk", replace(base, bulk=replace(base.bulk, sustained_fraction=.4))),
      ("20pct_useful_bulk", replace(base, bulk=replace(base.bulk, sustained_fraction=.2))),
      ("fabric_latency_20us", replace(base, fabric_latency_us=20)),
      ("single_hot_bank", replace(base, bank_mapping="hot_bank")),
    ]
    data["stress_tests"] = [dict(case=label, result=simulate(Workload(), s)) for label,s in cases]
    data["distributed_functional_demo"] = demo()
    data["rejected_nondivisible_16_module_head_layout"] = simulate(
        Workload(), replace(base, name="16-module invalid Q-head mapping",modules=16))
    return data


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2, allow_nan=False))
