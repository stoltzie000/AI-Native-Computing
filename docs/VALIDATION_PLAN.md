# Validation and Iteration Plan v0.1
Date: 2026-11-23

## Evidence levels
- E0: Hypothesis/idea — no validation.
- E1: Analytically bounded model — formulas and assumptions independently checked.
- E2: Executable architecture simulation — compared with independent reference kernels and sensitivity tests.
- E3: RTL/FPGA or other laboratory subsystem prototype — functional and selected timing/power behavior measured.
- E4: Full physical system — measured against GPU baseline with stated uncertainty.
Never promote an E1/E2 projection into an E4 performance claim.

## Workload portfolio
At minimum compare: single-user language generation (prefill and decode separately); longer-context retrieval/reasoning tasks; batched inference; embedding/vision or multimodal inference; and a training/update microbenchmark if training is in scope. Non-transformer alternatives are allowed; task quality must be equivalent. Record full workload and software revisions.

## Hardware benchmarking protocol
Use an optimized GPU implementation for each baseline. Fix datasets, quality criteria, number of runs, warmup, context, batch, clocks/thermal policy, wall-power metering boundaries and confidence intervals. Report p50/p95 latency, throughput, energy per successful task, peak/resident memory, total host+device power, and reliability. Report uncertainty; do not treat vendor peak specifications as achieved throughput.

## First model requirements
- Parameter/activation/optimizer storage when applicable, quantization metadata, KV/state allocation and capacity headroom.
- Reads/writes across every memory level, interconnect transfers, serialization, prefill vs decode, arithmetic intensity, realistic utilization and scheduling.
- Compute roofline and bandwidth roofline; concurrency and batch sensitivity.
- Technology-dependent estimates with cited physical assumptions, plus pessimistic/base/optimistic cases.
- Explicit invalid-input and memory-capacity rejection, automated tests, reproducible configs.
- A measured GPU trace calibration channel. Unknown input values remain unknown, not invented.

## Iterative design loop
1. Specify an architecture and falsifiable superiority hypothesis.
2. Build a traceable analytical performance/energy bound.
3. Simulate and cross-check arithmetic/communication correctness.
4. Compare with the best relevant baseline and a simpler competing architecture.
5. Identify the dominant limiter and run sensitivity experiments.
6. Reject/revise the architecture; retain failed trials and reasons.
7. Only when justified: RTL/FPGA/subsystem fabrication, then physical system testing.

## Initial decision gates
- G0: Reproduce and audit baseline data.
- G1: Feasible memory capacity, bandwidth, interconnect and thermal design.
- G2: Credible upper bound leaves room to outperform an optimized GPU.
- G3: Independent simulator predicts advantage over the same workload across plausible parameter ranges.
- G4: Physical subsystem validates predicted behavior.
- G5: Complete system demonstrates a quality-matched performance or energy advantage beyond measurement uncertainty.
No design is accepted purely because it appears novel.

## Current limitations
No original ASIC, motherboard, FPGA, power measurements, cycle-accurate simulator, fabrication quotes, or GPU benchmark traces have yet been verified for this project.
