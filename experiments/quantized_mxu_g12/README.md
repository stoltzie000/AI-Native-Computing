# G1.2 — Real openTPU quantized MM numerical contract

**Status: VERIFIED.** GitHub Actions [run 45296366906](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45296366906) passed 11/11 independent Python tests, 1/1 upstream actual QACT/MM directed test, 24/24 same-input quantized ISA comparisons and 24/24 independently implemented integer-core RTL cases. [Completed evidence and limitations](CI_EVIDENCE_AND_DECISION_2026-11-23.md).

This experiment corrects a limitation of G1.1: the earlier independent openTPU comparison used FP32 VPU MUL/RSUM instead of its real quantized matrix multiply engine. The pinned source of truth is [openTPU](https://github.com/FeSens/openTPU) at commit `d84db55712aba0d40811d7762cb052f05d55b7e5` (Apache-2.0). No external source is incorporated into this repository.

## Precise numerical contract under test

- Three FP32 activation rows of 64 elements each are quantized using actual upstream `QACT` (D=32, 8-element groups); compare QACT state against upstream's `fp32.quantize_mx` (`int8 q`, per-row `Sa`, per-group `da`).
- Five independent signed INT8 weight rows of 64 elements with separate per-row FP32 `Sw` and two per-row uint8 `dw` offsets.
- Invoke **actual openTPU MM `WF=0`**, `D=32`, `KB=2`, `W=16`, not VPU MUL/RSUM. For each of 8 groups of 8, compute signed exact `C = sum(q[i]*weight[i])`, `sh = 16 - dw[weight_row, block] - da[activation_row,group]`, then accumulate `C << sh` if sh>=0, otherwise drop group. The exact signed integer accumulator can exceed 32 bits; do not narrow it prematurely.
- Output epilogue: `y = F.mul(F.mul(F.i2f(acc), Sw), F.mul(Sa, 2^-16))` with separately rounded upstream FP32/FTZ semantics. This experiment **shares upstream's `F.mul`** for a bit-exact FP32 output test. That limits the independence of the *FP32 epilogue*, but not the exact integer core.
- Eight deterministic matrix cases × three activation rows = **24 independent integer-core RTL checks**, each with five output rows and all eight quantized subgroups. Includes zero inputs, uniformly positive/negative inputs, mixed signed values and deliberately varying quantization offsets.

## Implementation and measurement boundaries

`exact_core.py` is a pure-Python independent integer oracle. `rtl/exact_mxu_int8_core.v` is a **separate synthesizable research core**, not a modification or replacement of `prototype_v1_0`. It consumes already quantized bytes/offsets as stable wide buses, multiplies eight INT8 lanes per cycle, and accumulates 48-bit integers across all groups. It does **not** implement QACT, real SRAM/HBM, burst transfers, floating-point epilogue, complete openTPU chip architecture or model inference.

`adapter.py` uses upstream `Machine` to run the actual `LD, QACT, MM, HALT` program, compares QACT state, independently computes the integer accumulators, reconstructs FP32 results with `F.mul`, verifies **exact FP32 output bits** against actual MM output, and emits hex fixtures for Icarus RTL. Testbench checks 40 groups × 5 weights/8 groups, signed output bits and number of dropped groups for each generated input.

## How to reproduce

GitHub Actions `.github/workflows/quantized-mxu-g12.yml` (single branch, YAML-only trigger plus manual dispatch, **no PR trigger**) performs:

1. Checkout our project, and upstream openTPU at immutable commit.
2. Install Python/Numpy dependencies and `iverilog`/`vvp`.
3. Run independent Python tests and upstream `tests/test_isa.py::test_mm_matches_integer_math` as a control.
4. Run our adapter through actual openTPU QACT/MM, verify all 24 output vectors and generate hex inputs plus an audit JSON and SHA256 summary.
5. Compile our new RTL in Icarus and run all 24 generated same-input cases; require `PASS_QMM_CORE` once per case.
6. Upload all fixtures, logs, model hashes, tool versions and summary to short-retention CI artifact. Commit a durable decision record only after actual completion.

## Decision gates

Passing proves exact **integer arithmetic and output consistency** for this specific INT8 MXU data contract. It does **not** mean both implementations have the same memory interface, parallelism, clock, silicon power, physical bandwidth, or quality-matched GPU speed. Explicitly do **not** compare the RTL's 40 group cycles against upstream ISA instruction counts as hardware throughput.

The next stage after numerical correctness must implement/measure an identical **memory-transfer and resource contract**, and subsequently physically instrument an FPGA/ASIC or board before any performance claim. Preserve all failures and negative model sparsity findings in `PROJECT_STATE.md`.
