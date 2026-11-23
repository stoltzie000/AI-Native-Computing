# Next research and prototyping roadmap — current design directions

The mandate is to invent an AI-native computer — not a graphics card; all processor, memory, motherboard, package, cooling, algorithm, and software choices remain revisable. The following work may proceed without purchasing hardware or asserting a physical demonstration.

## G0 — Measured and reproducible GPU reference (open)

1. Obtain real Qwen2.5-32B-Instruct or similarly well-described model inference measurements, including exact model hash, quantizer, batch 1, KV type, context 2K/8K/32K, host and device, prefill vs decode, output quality and power.
2. Prefer a Rubin HBM4 reference with comparable 288GB memory if physically accessible. A B300/MI355X measured result is an informative older-generation data point, not an equal-generation winning comparison.
3. Record environment metadata and confidence intervals, excluding vendor peak FLOPS/TB/s as achieved workloads. MLPerf provides quality and throughput methodology, but not automatically the same workload.
4. Implement an independent second timing oracle to check the v0.3/v0.4 scheduler approximation and bound hidden memory-controller costs.

## G1 — Physically viable package/board design (open)

1. For each proposed HBM/controller compute package determine stack count, HBM base die/controller PHY interface, floorplan/reticle, total die-edge, routing congestion, aggregate SI, ESD protection and thermal interface area.
2. Distinguish short-reach advanced-package die-to-die links from cabled/PCB/connector links. Obtain actual PHY IP datasheet parameters or prototype. Unknown values **block** physical feasibility claims.
3. Design a real package power-delivery/voltage and liquid heat rejection estimate, including compute dynamic/leakage, HBM stack core and controller, PHY, retimers, voltage conversion, full system cooling/host overhead.
4. Screen two-package x four-stack, four-package x two-stack, and one-package x eight-stack assumptions. Reject any choice with unsupported thermal, I/O or memory controller.

## G2 — Algorithmic originality and quality-preserving efficiency (starting)

1. Compare structurally sparse matrix execution, expert selection with exact vs approximate pruning, low-rank and quantized attention/KV, local state compression, event-driven/neuromorphic and analog/optical candidate operators. Each gets independent task-quality evidence and a failure record.
2. Investigate formats and networks *other than tokens and transformers*, comparing objective time/energy per successful task, not source-model output units.
3. For block sparsity, measure real zero-block distribution and metadata overhead on a genuinely trained model (model hash/version). If zero blocks are not prevalent, reject naive structural-zero skipping. Do not pretend random pruning is quality lossless.
4. Consider compute-at-data/dataflow systems whose local memory traffic is materially lower than a dense model's 17.875GB weights + ~8.590GB KV at 32K context.

## G3 — Independent hardware correctness and timing (open)

1. Implement a small synthesis-ready sparse/block memory controller and PE in RTL with golden Python reference and adversarial randomized vectors. Confirm verification coverage.
2. Use a reproducible open-source gate/area/timing flow (technology assumptions cited) or a real FPGA build when hardware is available. Do not call FPGA timing equivalent to a custom ASIC.
3. Prototype one electrically instrumented link and one memory controller before any motherboard fabrication; measure BER, eye margin, sustained bandwidth, power, heat and timing.
4. Scale only after a physically validated subsystem passes. Construct a custom motherboard/backplane when it demonstrably improves end-to-end AI capability rather than because a new board is novel.

## Stop/iteration triggers

- Candidate does not exceed strong GPU baseline once equalized for AI quality, memory generation, power and system scale.
- Modeled advantage depends solely on adding HBM stacks or claiming impossible interconnect rates.
- Savings require non-existent sparsity, unmeasured model quality or unrealistic memory/storage overhead.
- Thermal, power, package, error rate, reliability, bandwidth and interface data cannot support a real prototype.

Record failure, isolate limiting component, change one experimental variable, and rerun. **A successful E1 simulation is not a competitive processor demonstration.**
