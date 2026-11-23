# Yosys parametric synthesis sweep — 2026-11-23

**Source evidence:** GitHub Actions workflow run 45237901548, job 137914422602, completed successfully. Ten `chparam` configurations independently elaborated with Yosys generic `synth` and `stat` after Icarus tests passed. Results were extracted from the completed job log. These are **generic logic cells**, not physical library gates/area/power or clock rates.

## Measured generic cell statistics

| Multiplier LANES | Active compute cycles for 4x4 tile | Generic cells ACC_W=16 | Generic cells ACC_W=32 | Controller cycles including accept and done |
|---:|---:|---:|---:|---:|
| 1 | 16 | 2187 | 2996 | 18 |
| 2 | 8 | 3150 | 4606 | 10 |
| 4 | 4 | 4809 | 7679 | 6 |
| 8 | 2 | 8343 | 14041 | 4 |
| 16 | 1 | 14437 | 25315 | 3 |

The first default-parameter Yosys pass, without a `chparam` step, reported 7636 generic cells for LANES=4, ACC_W=32. The uniform parameter-sweep flow reports 7679 for that configuration. **Use sweep values only for within-sweep comparisons.** A 43-cell elaboration/tool-flow difference is not treated as a physical hardware change.

## Derived arithmetic proxies, not measured speed or energy

At equal clock frequency with one request at a time, the longest tested configuration takes 18 controller cycles (LANES=1), versus 3 cycles for LANES=16: only **6x tile latency** reduction, despite 16x fewer active compute cycles. Real clocks will differ with critical path.

For ACC_W=32, the number of generic cells multiplied by controller cycles is:
- LANES 1: 2996 × 18 = **53928**
- LANES 2: 4606 × 10 = **46060**
- LANES 4: 7679 × 6 = **46074**
- LANES 8: 14041 × 4 = **56164**
- LANES 16: 25315 × 3 = **75945**

For ACC_W=16, the same proxy is: lanes 1 **39366**, 2 **31500**, 4 **28854**, 8 **33372**, 16 **43311**.

**Interpretation:** Under the intentionally rough assumption of comparable cell complexity and identical clock period, 2 or 4 lanes look more promising than 16 lanes for area×latency of one request. This proxy is NOT silicon area, energy-delay product, or a measured physical advantage. Higher parallelism could improve sustained throughput with buffering, but only after designing and measuring such buffering.

## Decision / falsification

- **Deprioritize 16-lane full unroll** as the initial FPGA/ASIC research block until technology-mapped clock/frequency and energy evidence overturns the generic area-delay risk.
- **Prioritize LANES=2 and 4** for the next physically constrained experiment; retain 1 as a small-footprint control.
- Do not conflate a local 4×4 INT8 kernel with full-model AI inference or a GPU replacement.
- Next: get a real gate library or FPGA target, synthesize all variants with timing constraints, quantify routed utilization and power, implement a true memory/index pipeline, and compare task-quality-matched workloads.
