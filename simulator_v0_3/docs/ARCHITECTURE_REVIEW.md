# Architecture-review checkpoint — v0.3

**Date:** 2026-11-23. All rates below are analytically conditioned scenario outputs, **not** benchmarks of a manufactured processor or of GPUs. All systems execute the same approximate Qwen2.5-32B decode model with 4-bit weight storage +10% metadata, 16-bit KV state, batch=1, 32,768-token context.

## Findings: use failure analysis to choose the next experiment

| Hypothetical system | Conditional output-step rate (per second) | Interpretation |
|---|---:|---|
| RTX 5090 memory-peak proxy | 66.7 | Published GPU bandwidth/capacity, all execution service assumptions synthetic |
| H200 memory-peak proxy | 174.5 | Same limitations |
| MI355X memory-peak proxy | 283.8 | Same limitations |
| Custom stacked-HBM 4-node | 433.1 | Fabric, HBM interfaces and compute cores are not physically specified |
| Custom HBM 8-node | 460.8 | Selected for *research*, not hardware acceptance |
| 8-node HBM + 0.5GB SRAM/node | 448.7 | Worse than 8-node HBM configuration given its lower assumed bulk bandwidth |
| Wafer/multi-die 48GB SRAM | 814.5 | Memory macro lower bound exceeds ordinary reticle; power, physical bandwidth unknown |
| 8-node worst-case one-bank hotspot | 45.5 | Bank layout can erase hypothetical benefit |

Comparison is **not** an equal-dollar, equal-area, equal-power or even equal compute-peak comparison. Multi-node candidates are physically larger systems. GPU assumptions and candidate assumptions have not been calibrated by benchmarks. Thus a numeric candidate/GPU ratio from this table is NOT evidence of superiority.

## Eight-module fabric sensitivity at 32K context

| Case | Conditional outputs/s | Relative to uncalibrated MI355X model | Decision |
|---|---:|---:|---|
| Default, 100% bulk-BW utilization | 460.8 | 1.62× | Optimistic theoretical scenario, not achieved performance |
| 70% memory usefulness | 365.3 | 1.29× | Still conditional advantage |
| 40% usefulness | 240.7 | 0.85× | **Fails** this comparison |
| 20% usefulness | 134.0 | 0.47× | **Fails** |
| Fabric latency 20 microseconds | 110.1 | 0.39× | **Fails** |
| All transactions hit one bank | 45.5 | 0.16× | **Fails** |

Interconnect synchronization is modeled as two reductions for each of 64 layers. That implies 128 collective operations per output step. For eight nodes with a log2(N) stage penalty, an extra 18 microseconds in assumed per-link latency adds approximately **6.912 milliseconds** per decode step before transfer serialization, explaining the strong performance loss. This formula is a property of this simplified model, not a prediction for a designed physical network.

## Alternative architecture evaluation

**C1. 4–8 near-memory HBM compute modules (priority to falsify):** A custom motherboard/backplane may arrange compute-memory tiles around local stacked memory, with a fast intra-package network and constrained host/IO peripherals. The proposed 8×2.5 TB/s capacity totals **20 TB/s as a hypothetical sum of individual local links**, not a promised *usable global bandwidth*. For an actual system, head placement, inter-chip communication, layout, signal integrity, module physical dimensions and thermal design are presently unknown. 2.5 TB/s per module is unverified.

**C2. Hybrid bulk-HBM plus small SRAM:** The explored 0.5 GB of SRAM per module implies an optimistic >=105 mm² of memory-macro area per module at TSMC's reported 38.1 Mbit/mm². Actual area is greater; memory bandwidth and clock/power compatibility with other logic unproven. It was slightly slower than the pure-HBM experiment because the model assumes slower bulk memory; it is **not rejected as a physical concept**. A fair follow-up must hold equivalent bulk-memory specifications fixed and vary only SRAM placement; compare against a no-SRAM control with the same bulk bandwidth.

**C3. 48 GB SRAM wafer-scale / many-die fabric:** A physical SRAM macro area bound is >=10,079 mm² total at 38.1 Mbit/mm², excluding computation and I/O. A single conventional reticle-scale die per 12 GB SRAM node is impossible under that cited density. Wafer-scale is possible in principle (Cerebras demonstrates a 44 GB SRAM wafer device), but we have not established suitable circuitry, yield, power or topology. The v0.3 performance ranking is NOT validated feasibility.

**C4. Processing-in-memory / analog / optical:** Research alternatives remain open. Standard HBM byte-transfer modeling cannot evaluate their internal compute and conversion costs fairly. Need architecture-specific correctness reference, physical energy model, error/noise/stability budgets and dataflow before making ranked claims.

## Proposed physical AI-native platform (design **hypothesis**, not final spec)

- **Processing:** 4–8 functionally independent compute-memory tiles with per-node matrix/vector execution and control; no obligation to reuse GPU ISA, PCIe-centric memory hierarchy or standard motherboard geometry.
- **Memory:** stacked memory close to each tile, narrow fast SRAM for scheduling/state; model all KV shards, activation movement and capacity overhead.
- **Motherboard/backplane:** custom high-speed fabric, local links preferred; separate supervisory/management processor, boot/telemetry, independently metered power domains, thermal sensors and error handling.
- **Firmware/runtime:** graph-to-tiles compiler and deterministic scheduling; support model architecture changes. Correctness tests required before performance comparisons.
- **Validation order:** measured GPU baseline and fabric link characterization; topology/floorplan/electrical limits; transaction simulator calibration; HDL functional module; real interconnect board; thermal/power; quality-matched real workload; full-system benchmark.

None of these can be declared physically buildable solely from the simulator.

## Functional dataflow demonstration

A separate deterministic toy 8×12 matrix-vector computation is split into four compute shards, aggregated using a simulated ring reduce-scatter/all-gather, and checked against a conventional serial matvec. The distributed software reference reproduces the serial numerical output exactly for the chosen inputs, and randomized 1/2/4/8-module tests pass with tolerance 1e-12. This proves the toy sharded algebra and logical communication algorithm on a CPU. It **does not** prove Qwen inference correctness, silicon functionality, a physically realistic network, or any speed advantage.

## Gate status

- **G0 references:** Qwen config and vendor peak memory specifications cross-checked; *measured* matched GPU workload baseline **OPEN**.
- **G1 memory:** storage and replica capacity checked, bank bottlenecks modeled; real die, packaging, power delivery and interconnect **OPEN**.
- **G2:** conditional upper bounds give room to explore, but assumptions currently too optimistic/uncertain; **OPEN**.
- **G3:** deterministic event scheduler with independent arithmetic and regression tests achieved; it is not cycle-accurate/calibrated; **PARTIAL**.
- **G4/G5:** hardware subsystem/full-system validation **NOT STARTED**.

## Falsifiable next research experiment

Construct a **per-link topology simulator** (mesh vs ring vs fully connected vs stitched wafer), assign physical per-link injection bandwidth and round trip latency, instrument collectives, and add a calibration interface for measured optimized GPU/HBM traces. For each topology, test actual tail latency and bank/route contention under 2K/8K/32K contexts, evaluate error-free data movement with exact volume conservation, then rank under an *identical* input-power/bandwidth budget. A candidate that cannot robustly beat a verified GPU benchmark within realistic ranges must be reworked, not declared successful.
