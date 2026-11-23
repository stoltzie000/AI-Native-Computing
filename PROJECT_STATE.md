# AI-Native-Computing — PROJECT_STATE
Last updated: 2026-11-23

## Current phase
Project baseline established; first-principles architecture research and experiment design. No competitive processor has yet been demonstrated.

## Decisions
- Design a complete AI-native computer, not merely a GPU replacement card.
- Processor, memory, motherboard/backplane, interconnect, power, cooling and software may all change.
- Challenge established assumptions, including token-centric execution and transformer-only workloads.
- Optimize real AI capability, task performance and efficiency; profitability is not a primary objective.
- Compare with strong GPU and purpose-built accelerator baselines using reproducible, fair measurements.
- Redesign failing candidates; archive negative results rather than claiming success.

## Verified progress
- Existing GitHub repository: stoltzie000/AI-Native-Computing, main branch.
- GitHub repository is public as of this checkpoint.
- Initial GitHub README pre-existed and was preserved.
- Previous local analytical prototype v0.1 exists and its four elementary unit tests passed in the assistant's isolated runtime on 2026-11-23. It is a simplified 30B low-bit inference roofline calculation, NOT a validated processor or GPU benchmark.

## Known shortcomings of previous v0.1
- Counts an assumed KV-cache capacity but does not model KV read traffic in its decode throughput estimate.
- Does not enforce physical memory capacity in evaluate().
- Uses assumed utilization, electrical power and cost; none are physical measurements.
- Tests confirm only arithmetic identities; no calibrated simulator or benchmark is available.
- Focuses on a PCIe-connected LLM accelerator and is superseded as product scope by full-system co-design.

## Current project artifacts
- docs/PRODUCT_DEFINITION.md — requirements and system scope.
- docs/VALIDATION_PLAN.md — evidence standards, benchmarking, iteration gates.
- Previous analytical prototype is historical evidence, not proof of superiority.

## Immediate next work
1. Establish reproducible reference workloads and optimized contemporary GPU baselines.
2. Create independent, audited architecture models with explicit capacity and movement accounting.
3. Explore multiple candidate topologies (including custom motherboard and memory) and document tradeoffs.
4. Implement testable simulator and use failure analysis to revise candidates.
5. Prototype physical subsystems only after modeling evidence merits it.

## Open constraints / unknowns
Real-world GPU measurements, candidate manufacturing technology, lab instruments, funding/resources, and physical benchmark data are not established. Do not invent them.

## Task-sequence continuity
No new executable Codex/GPT task number is assigned here. Before issuing a numbered handoff, reconcile the last task number in the active workflow; do not silently restart numbering.

## Safety / repository handling
Preserve existing work and uncommitted changes. Inspect repository state before future changes; do not overwrite, reset, wipe, or reconfigure repository visibility without approval.

## 2026-11-23 checkpoint — analytical simulator v0.2
**Status:** Implemented and independently executable in isolated Python 3 environment. All 17 unit tests passed. Source files and deterministic JSON output committed to `simulator_v0_2/`, then re-fetched from GitHub and verified with exact Git blob SHA against local artifacts (8/8 exact matches). The initial README and archived v0.1 were preserved. No user's local PC or hardware was modified.

### Model improvements
- Capacity validation includes compressed weights + metadata, KV resident state and scratch.
- KV cache reads and writes contribute to long-context decode traffic.
- Fast/bulk memory tiers, module count, simplified fabric bandwidth/latency, dense-operation lower bounds, generic work-unit roofline, optional assumed power with unknown energy otherwise.
- Explicit arithmetic assumptions, falsification and capacity failures.
- Sources: `simulator_v0_2/docs/SOURCES.md`. Decision/failure log: `simulator_v0_2/docs/DECISION_LEDGER.md`.

### Conditional scenario outcomes (Qwen2.5-32B proxy, 4-bit weights, context=32768, batch=1)
All rates are optimistic **analytical scenarios**, NOT measured GPU or new-processor results.
- RTX 5090 memory-spec proxy: 67.7 output units/s
- H200 memory-spec proxy: 181.4
- MI355X memory-spec proxy: 302.3
- Proposed 8-node near-memory: 251.4
- Proposed 16-node PIM *proxy*: 401.5 (not a physical PIM model)
- Proposed 4-node 48GB SRAM concept: 1036.4, assumes total 32 TB/s SRAM, full weight+KV residence, unrealistic unverified component parameters
- SRAM scenario at only 75% fast residency: 290.2; at 50%: 148.1. At 25%: REJECT_CAPACITY. Sensitivity falsifies robust superiority.

### Decision
G0 partially completed: published model/GPU memory specifications verified, no measured optimized GPU workload yet. E1 analytical model implemented, tests passed. **No physical design proven, no reproducible hardware advantage claimed.** SRAM-centric route remains a high-risk hypothesis; no architecture selected for hardware.

### Next work
1. Measure or retrieve appropriately matched GPU benchmark traces and quantify kernel efficiency.
2. Separate true SRAM physical area, yield, thermal, I/O, fabric and power viability from hypothetical numbers.
3. Build an event/transaction-level memory/fabric simulator with at least one independent reference implementation.
4. Compare non-transformer and task-quality-matched AI workloads; explore monolithic, on-package, optical/analog/PIM where justified.
5. Iterate/reject on failure. Only then consider RTL/FPGA and hardware experiments.

### Task sequencing
No Codex/GPT executable task number assigned by this checkpoint; number continuity remains unresolved.

## 2026-11-23 checkpoint — v0.2.1 physical feasibility correction
Physical feasibility check added to `simulator_v0_2/physical_limits.py`, `test_physical_limits.py`, and `docs/PHYSICAL_FEASIBILITY_SCREEN.md`. Current local suite: **21/21 unit tests passed**. The five changed/new files were re-fetched from GitHub and matched their local Git blob SHA exactly (5/5). Prior v0.2 result estimates retained as **unmeasured**, conditional arithmetic tests.

**Evidence:** TSMC published high-density SRAM macro density 38.1 Mb/mm². A 12 GB SRAM store needs >= 2,520 mm² of SRAM macro at that density, or ~2.94 conventional 858 mm² reticle footprints **without compute/routing/PHY overhead**. Four such stores need >= 10,079 mm² aggregate. Therefore the interpretation “one 12 GB SRAM node equals one ordinary reticle-size silicon die” is **rejected**. Candidate must be reworked as stitched-wafer or multi-chiplet logical modules with realistic interconnect, thermal and energy costs. No revised physically validated design is available.

**Gate status:** E1 calculations validated for selected assumptions; G0 benchmarking incomplete; G1 capacity constraints modeled, real physical feasibility remains OPEN; G2-G5 NOT PASSED. No physical superiority claim.

**Next implementation priority:** event-level trace simulator with attention/weight transfers, bank-level routing/latency and topology; examine wafer-scale/stacked/hybrid alternatives with physical data and compare to measured optimized GPU benchmarks. Preserve failed architectures and hypotheses.
