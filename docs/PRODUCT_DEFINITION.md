# AI-Native Computing — Product Definition v0.1
Date: 2026-11-23
Status: Research definition, not a demonstrated hardware design.

## Mission
Invent, develop, and experimentally demonstrate a computing system whose hardware and AI execution methods are co-designed from first principles and deliver a reproducible advantage over strong contemporary GPU-based systems on equivalent AI tasks.

## Scope
The solution may redesign the processor, motherboard/backplane, memory technology and placement, package, interconnect, power distribution, cooling, firmware, system software, compiler/runtime, data representation, and potentially the AI algorithms themselves. No assumption that PCIe, PC motherboards, GPUs, transformers, token-based generation, or existing instruction sets must be retained.

## Priorities
1. Equivalent or better AI capability and output quality.
2. Better time-to-useful-result for selected representative workloads.
3. Better total-system energy efficiency, especially energy per correct/accepted result.
4. Scaling to larger problems while preserving reliability.
5. Clear evidence, reproducibility, and ability to revise failed design decisions.
Commercial profitability is NOT a design objective. Fabrication feasibility, physical laws, materials availability, thermal limits and engineering time remain constraints.

## Fair comparisons
Measure on matched task sets and quality thresholds; report latency, throughput, wall-plug energy, memory use, and complete system configuration. Compare against well-optimized contemporary GPUs, not theoretical peak numbers or deliberately unoptimized baselines. When proposing a different AI model or representation, validate task accuracy and include any added preprocessing, training, communication, and conversion overhead.

## Research candidates (none selected)
- Digital near-memory or processing-in-memory compute.
- Distributed SRAM/DRAM and 2.5D/3D memory-compute integration.
- Spatial/dataflow processing fabric on a custom motherboard/backplane.
- Low-bit or adaptive precision hardware with accuracy safeguards.
- Optical, analog, neuromorphic, or unconventional computing where testable physical advantages can be shown.
- Hybrid architectures combining specialized subsystems.

## Definition of success
A complete, inspectable system shows statistically credible superiority on a relevant, quality-matched AI workload against a strong GPU baseline, and its tradeoffs are explicitly characterized. A spreadsheet model, theoretical ceiling, simulator output, or FPGA functional check alone does NOT establish product superiority.

## First MVP
An evidence-led engineering research suite: benchmark specifications, workload traces, parametric roofline and movement models, candidate simulator, correctness tests, sensitivity analysis, and a repeatable decision ledger. This is an architecture-discovery MVP, not a manufactured chip.
