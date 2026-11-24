# G1.3 shared FP32 epilogue — generic synthesis comparison
Date: 2026-11-24. RTL_RESULT + SYNTHESIS_ESTIMATE, no physical timing/power.
Same five signed INT48 accumulators, FP32 weight scales and activation scale, same binary32 RNE/FTZ operations, 24 pinned upstream ISA fixtures (five outputs each). Identical Yosys 0.33 synth/stat flow.

| Candidate | Hierarchy generic cells | Execution contract | Evidence |
|---|---:|---|---|
| Parallel combinational epilogue | 75,373 | combinational, unclocked | run 45448043366/job 138637128400 SUCCESS |
| Serial shared epilogue | 10,660 | 11 active simulated cycles/job | run 45448575985/job 138639047568 SUCCESS |

Difference 64,713 cells (~85.86% reduction). NOT equal throughput or energy; no FPGA, ASIC library/area, Fmax, timing, P&R or power. Serial RTL: 48/48 ISA-backed jobs across 24 suites, five exact FP32 outputs/job. Inputs deliberately mutated after latch. The first run 45448499448 failed missing ascale.hex/wscale.hex/expected_fp32.hex because adapter.py alone does not write these; repaired workflow invokes generate_cases.py before Icarus. Corrected artifact 14946203478, raw bytes not independently rehashed.
Decision TEST serial epilogue as resource-pressure candidate; preserve parallel version as latency reference. NEXT_ACTION latency/resource-constrained mapped hardware and full pipeline integration with a fair throughput comparison. G1 OPEN.
