# Prototype v0.6 — verification plan and claims gate

## Evidence today

- 11 Python unit tests passed locally, exercising arithmetic, negative operands, signed 8-bit limits, the skip metadata invariant, count schedule and 100 randomized small 4x4 matrices.
- Verilog source and testbench authored but **no local Icarus Verilog, Verilator, or Yosys tools were available**, so no RTL simulation or synthesis was executed locally. A GitHub Actions workflow has been authored to supply the missing RTL simulation environment. Do not claim the workflow passed without inspecting an actual completed run.
- No FPGA/silicon device exists; no actual timing/power/bandwidth, AI model quality, or GPU comparison performed.

## Next correctness and performance gates

1. **RTL compile/simulation:** Run Icarus with `-g2012 -Wall`, verify the active, skip, signed tests. Fix any compiler or numerical issues; preserve failed versions.
2. **Cross-implementation differential tests:** Extend bench to feed randomized INT8 blocks and compare *actual RTL output* to independently computed signed32 serial output. A hand-calculated 3-vector suite is inadequate for a new processor.
3. **Overflow and parametrization:** Add assertion that `ACC_W >= 2*DATA_W`, constrain block indexing, and test min/max signed weights, reset during active work, repeated start, and ready/backpressure.
4. **Synthesis and clocking:** Use actual Yosys or commercial synthesis with identified standard cell/library; measure reported area, maximum clock with SDC, critical path, toggle-based dynamic power, leakage and interface timing. Synthesis estimates are still not physical silicon.
5. **Architectural scaling:** Design valid-mask SRAM/metadata fetch, compressed block storage, zero-skip scheduler, many PEs, interconnect and bank contention. Test with actual trained-model block patterns and equal-quality benchmarks, not synthetic 75% zero masks.
6. **Physical validation:** Measure FPGA kernel power/latency with instrumented voltages; later tapeout/measurement if design can win against optimized GPU systems under matched tasks and resources.

## Falsification

- If the RTL fails numerical correctness, rollback the core before investigating performance.
- If real model weights have insufficient certified zeros, reject exact-zero-only acceleration for that model.
- If metadata/index traffic eliminates savings, revise compressed representation.
- If SRAM/HBM read power, interconnect congestion or per-package heat eliminates theoretical performance gains, redesign before fabrication.

No speculative architecture is accepted merely because a deterministic simulator or HDL compiler passes.
