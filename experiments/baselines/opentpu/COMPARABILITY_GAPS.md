# Comparison discipline — openTPU versus AI-Native-Computing v1.0

This document records known mismatches **before** performance numbers are calculated. A functioning reference is not automatically a fair rival. The paths below were inspected at upstream openTPU commit `d84db55712aba0d40811d7762cb052f05d55b7e5` and our canonical `main`.

## Important mismatches

| Dimension | openTPU upstream baseline | Our v1.0 prototype | Consequence |
|---|---|---|---|
| Arithmetic | `tests/test_isa.py::test_mm_matches_integer_math` performs quantized matmul with activation quantization, per-group shifts and output scales; compares floating-point reconstructed outputs bit-exact to a specified software oracle | Signed INT8 weight × signed INT8 activation, signed ACC16/ACC32 modular sum, no output scaling | **Cannot compare numeric outputs directly** without matching scale/rounding/activation quantization or implementing a shared operator contract |
| Reference execution | Real upstream `Machine` ISA simulator, with an RTL/ISA differential selected in this experiment | Our standalone Python reference and signed `column_buffered_pe.v` RTL | Functional proofs cover **different instructions and interface contracts** |
| Memory organization | Streaming quantized weight/scale data for MM from DRAM; ISA and tests count specific transaction formats | One 64-byte column-response per active activation in a hypothetical burst model; buffer is **registers** | Logical request count and bytes do not equal physical DRAM burst traffic |
| Matrix sizes | Upstream directed MM fixture: 3×64 activation block × 5×64 weights (and larger/fuzz variants), config D=32 | Current v1.0 primary test: 64 output rows × 4 input columns, two/four time-multiplexed MAC lanes | Different work sizes cannot be ranked by raw cycles or gate count |
| Implementation | Upstream complete ISA/RTL/FPGA-board stack with reported real card experiments, **not yet reproduced on card here** | Our small RTL processing element, Icarus/Yosys verified; no FPGA or board | Different measured evidence tiers and resource boundaries |
| Power/clock | A GitHub-hosted RTL test has no FPGA wattmeter/clock | Generic synthesis cell count, not physical timing/energy | **Neither can claim measured performance superiority** on this run |

## Pre-registered fair head-to-head construction

1. Define one **exact operator contract** shared by both implementations: input shapes (e.g., 64×64 INT8), quantizer and scale encoding, order/width/rounding of accumulation, output format, reset and tolerance. Keep arithmetic bit-exact where both can implement that contract; if model quantization differs, use a fixed task-score non-inferiority evaluation instead.
2. Generate a **common deterministic input suite** with dense zero-free weights/activations, synthetic exact-zero activations, heavy-tail values, signed extremes and real pinned-model activation samples. Report the zero-free negative control separately from sparse cases.
3. Implement an adapter to drive each system with *the same* required operation, and check each against an independent NumPy/Python oracle before measuring speed. Do not claim parity by merely comparing different tests.
4. Separate compute cycles, memory stalls, total controller cycles, transfer bytes, prefill/decode, and end-task metrics. Normalize to **equal MAC capacity, available memory and power**, or explicitly label non-equal configurations.
5. Run physical FPGA experiments with same actual memory controller/clock/power instrumentation before making latency or joule claims. For a GPU baseline, run the same arithmetic/model and output-quality protocol on an optimized GPU.
6. Archive every rejected variant with configuration and failure reason. Any speedup based only on hypothetical minimum burst size remains a sensitivity analysis.

## Observed baseline source particulars

The upstream directed MM test uses `Config(S=1, D=32)`, 3 activation rows and 64 inputs, five weight rows, and `w = rng.integers(-127,128,(5,64))`; weights and QACT scales are combined through dynamic shifts before `F.mul` final reconstruction. This is **not** the same operation as our raw modular INT8 dot product.

The current external run verifies source and arithmetic behavior only; it does not inspect silicon timing or electrical I/O. Evidence of passing cases must be added after a completed CI log, and failures retained.
