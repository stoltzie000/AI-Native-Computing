# G1.1 — Common arithmetic and shared fixture validation

**Experiment:** Numerical correctness under identical mathematical inputs running on (a) AI-Native-Computing v1.0 RTL, (b) openTPU's ISA simulator, and (c) openTPU RTL via Verilator. **Not** a same-resource, same-datapath, measured bandwidth, GPU or energy benchmark.

## Frozen operator contract

- `W`: signed INT8, 64 rows by 4 columns; `x`: signed INT8 vector length 4; output `y[r] = sum(W[r,c] * x[c])` over `c=0..3`.
- Result: exact signed INT32; four signed INT8 products and their sum fit exactly in FP32 (|y| ≤65,536). No fixed-point accumulation overflow, quantizer, or output scaling. This precise numerical equivalence is only for this bounded workload.
- Deterministic seed `0x5A19A123`; 11 frozen synthetic fixtures: dense zero-free inputs, negative values, signed extremes, zero activations, zero weights. Canonical fixture SHA256 `6cacaf38065f50773531c84408572d930988a0c51d01608212db152cde474d38`.
- Independent Python integer oracle creates expected values and exact input images. All execution paths must match the same 64 outputs per fixture.

## Execution paths

1. **Our original v1.0 RTL**, unchanged: Icarus Verilog testbench feeds the same INT8 weights (converted to column-major bytes) and vector, checks all 64 signed INT32 outputs, counts real logical column-request handshakes, and checks skips, active compute cycles, backpressure, input latching, and completion. Test two and four MAC lanes. Memory responses are synthetic 64-byte columns, not an actual SRAM/HBM controller.
2. **Actual openTPU ISA:** Use unchanged upstream `FeSens/openTPU` commit `d84db55712aba0d40811d7762cb052f05d55b7e5`. Convert precisely representable INT8 weights/activations to FP32. Run real `I.V_MUL` with broadcast vector and `I.V_RSUM`. Check outputs exactly against integer oracle. **This uses the FP32 VPU, not the quantized MXU/MM path.** No compute-cycle/throughput comparison is valid.
3. **Actual openTPU RTL:** Execute the same ISA instructions through upstream `opentpu.rtlsim` and pinned Verilator 5.054 for dense, half-zero and all-zero fixtures, checking all outputs against the oracle. No upstream RTL patches, hardware board, or source incorporation.

## Arithmetic/memory comparability boundary

Our RTL's logical 64-byte INT8 columns and openTPU's FP32 VPU bulk loads use different encodings, control paths and arithmetic resources. The external VPU reads 256 FP32 weights (1,024 B) plus four FP32 activations (16 B), whereas our INT8 PE uses up to four 64 B weight-column responses plus four activation bytes. **These numbers cannot be treated as a fair physical memory comparison**; actual DDR/HBM burst/cache traffic and equal-resource throughput remain unmeasured.

A future fair speed/energy comparison must implement one shared quantization/precision, memory hierarchy, and capacity in both systems, or use a task-quality non-inferiority gate for model-specific representations. Do not derive GPU/FPGA superiority from this experiment.

## Reproduction and notification control

`python -m unittest discover -s experiments/matched_operator_v1_1/tests -v`

`python experiments/matched_operator_v1_1/fixture.py --out experiments/matched_operator_v1_1/results/generated`

GitHub Actions workflow `.github/workflows/matched-operator-v1-1.yml` runs the three execution paths and keeps evidence for 30 days; source and decisions are committed separately. **Only a push changing that workflow on its research branch triggers CI**, plus manual dispatch; no `pull_request` event or duplicate notification trigger.

**Acceptance rule:** all three systems agree exactly on the selected arithmetic fixtures, with no skips or unreported failures. A passing result establishes a common functional task—not hardware performance parity.

## Completed verification — 2026-11-23

The real [GitHub Actions run 45290172189](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45290172189) completed **SUCCESS** with 7/7 fixture tests and 7/7 original Python tests. All 11 same-data cases passed openTPU ISA, all 11 passed our real v1.0 Icarus RTL at 2 lanes and at 4 lanes, and **3/3** selected cases passed actual openTPU RTL through the pinned Verilator 5.054 toolchain. **36/36 cross-system fixture executions passed**; the exact generated test-data SHA was independently checked.

[Exact CI and artifact evidence](CI_EVIDENCE_2026-11-23.md) · [Machine-readable summary](results/VERIFIED_SUMMARY_2026-11-23.json) · [Retained raw 42-entry test artifact](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45290172189/artifacts/14874521670).

**Decision:** This is our first demonstrated common mathematical operator across two genuinely implemented RTL systems. It is **not a shared datapath, physical memory measurement, quantized MXU throughput or whole-system GPU comparison**. Detailed caveats above remain in force.
