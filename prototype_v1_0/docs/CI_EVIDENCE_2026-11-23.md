# v1.0 actual RTL and generic synthesis evidence — 2026-11-23

GitHub Actions workflow run **45259340579**, job **137989557786**, completed with conclusion **success**. All values below are from the completed GitHub job logs, not predicted simulator outcomes.

## Functional verification

- Independent new Python reference: 7/7 tests passed.
- Prior v0.9 Python regression: 15/15 tests passed.
- Icarus Verilog: ROWS=8 or ROWS=64; LANES=2 or 4; ACC_W=16 or 32. All **8 parameter combinations** passed **95 deterministic/randomized test transactions each**, **760 total**.
- Testbenches check modulo signed arithmetic, 16-bit wrapping, external column read handshakes, cancellation of whole-column read on zero activation, request backpressure, input latching, premature start rejection, reset and done pulse.
- The memory responder returns a preassembled contiguous column; it is a **testbench**, not a physical HBM/DDR controller.

## Generic Yosys synthesis results

Identical `read_verilog; chparam; hierarchy; synth; stat` Yosys flow for 64 rows, INT8, ACC32:

| LANES | MAC active cycles per nonzero column | Yosys generic cell count |
|---:|---:|---:|
| 2 | 32 | 19,400 |
| 4 | 16 | 20,334 |

Four lanes increase counted generic logic cells by **(20334/19400−1)×100 = 4.8144%**, and halves the compute-only cycle count at identical hypothetical clock period. These numbers are **not physical chip area, energy, critical path, achievable clock frequency, or benchmark latency**. The 512-bit column register array, 64 row accumulators and variable-index write/mux logic dominate much of the synthesized logic. An SRAM macro or banked scratchpad may substantially change cell counts and timing.

## Falsification boundary

For fixed 64×4 INT8 matrix and 2 active input columns, an ideal 64-byte burst for each column produces 2 contiguous logical requests / 128 useful bytes. The v0.9 4-row baseline would require 32 independent logical requests and, if each physical request has 64-byte minimum transfer, 2,048 transferred bytes. **This is a hypothetical burst-granularity comparison, not a measured HBM result**.

The v1.0 RTL has only one outstanding column read and cannot overlap computation with fetching the next column. Even a perfect burst utilization cannot guarantee superior throughput because of memory latency, clock rate, buffering and control overhead. Real trained model *activation* exact-zero fraction is not yet measured. No GPU superiority claim is justified.

## Selection

**Retain 4 lanes as preferred next synthesis/timing hypothesis**, 2 lanes as control. Next: proper mapped timing/area, physical SRAM/burst interface and ideally double-buffer prefetch; plus independently measured activation zero fractions from real trained AI inference. Reconsider the entire activation-gating architecture if zeros are too rare.
