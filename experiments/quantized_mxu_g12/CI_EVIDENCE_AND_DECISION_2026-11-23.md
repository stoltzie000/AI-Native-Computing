# G1.2 — Real quantized MM vs independently implemented integer core

**Date:** 2026-11-23 (Eastern; corresponding runner log Nov 24 UTC).

## Verified outcomes

- **GitHub Actions successful run**: [45296366906](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45296366906), job **138117665388**, completed **success**.
- **Source validation**: `exact_core.py` verified SHA-256 `edd1cb8ff9f0193900f670c13aa8427a2550c5204ce1ca280c0ff8ef765176d7` before executing tests. External source pinned at `FeSens/openTPU@d84db55712aba0d40811d7762cb052f05d55b7e5`, checked out without modification.
- **11/11 local Python unit tests** passed (independent exact integer core and deterministic fixture constraints).
- **1/1 upstream actual MM directed test** `test_mm_matches_integer_math` passed. This uses the real QACT/MM instruction path, not the FP32 VPU workaround used in prior G1.1.
- **24/24 actual upstream ISA result comparisons** passed (8 synthetic FP32 activation scenarios ×3 activation rows) using the exact independent Python signed-integer accumulation and upstream's exact FP32 scale multiplications.
- **24/24 Icarus RTL executions** passed on exactly the quantized QACT code bytes, weights and offset vectors generated from upstream, against the same independent 48-bit integer accumulators. Testbench verifies signed output width and dropped groups.
- **120 computed scalar outputs** (`24×5`) compared against real upstream ISA output FP32 bits; testbench checks all corresponding signed 48-bit accumulators.
- Full [read-only GitHub CI artifact](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45296366906/artifacts/14877016582) contains **152 entries** of hex input/expected files, actual verification logs, full JSON and exact dependency metadata. It was independently downloaded and inspected: **24** `PASS_QMM_CORE` entries, full `summary.json` with **24** cases, and summary hash `6ec0e20114e0ad153d9dd4701c93b45b4092446644812e9cc596127dd365a9b7`. The actual aggregate, per-output results and pass log are also committed for durable use.

## Observed numerical corner-case coverage

Within **24 × 5 × 8 = 960** synthetic output/group windows, **153** had negative shift offsets and correctly contributed zero to the exact accumulator. This is **15.94%** *synthetic data group dropping*, **not pretrained-model sparsity or observed hardware savings**; the RTL processes/checks every group and does not implement an optimized skip/DRAM bypass.

The largest absolute independently computed signed accumulator among all generated cases was **16,945,514,496**, which is above 32-bit signed range. This validates exercising the **48-bit** signed accumulator rather than silently narrowing intermediate results.

## First failed attempt and correction — preserved

[Initial run 45295964951](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45295964951) failed **before arithmetic execution**: a temporary file-transfer operation wrote a placeholder error string instead of the 2,316-byte `exact_core.py` source. We verified all other staged file heads, replaced only the affected file from the real local source, and added an explicit CI SHA-256 guard. The original failure remains in GitHub history and must not be relabeled a numerical failure.

## Exact scope of what passed

This result is an independently implemented **signed INT8 integer dot/group + offset/shift accumulator** compared with the actual openTPU INT8 MM engine, while:
- **QACT quantization** is executed by the upstream ISA and separately validated against upstream's own `F.quantize_mx`, **not** independently designed or implemented in our new RTL.
- **FP32 multiply/FTZ epilogue** is bit-compared using upstream's `F.mul` primitive, not independently reproduced in RTL.
- **Memory and state** inputs to the new core arrive on stable wide buses. The new research RTL has **no actual SRAM, cache hierarchy, DDR/HBM transaction or controller**, no driver, no complete model load or physical I/O.
- **No throughput, latency, clock frequency, die area, power, FPGA timing or GPU task-quality measurement** was performed. The sequential core's one 8-element group per cycle is an RTL controller design parameter, not a comparable performance result against openTPU's parallel MXU.

## Research decision

**ADOPT G1.2 as a verified quantized-arithmetic functional checkpoint**, not a winning processor architecture. Preserve earlier G1.1 (different FP32 VPU path) and v1.0 (unscaled INT8) as independent controls. Next experimental gate must specify equal memory/layout, signed precision including quantizer and epilogue, number of compute lanes, buffer capacity and available bandwidth, with a controlled physical implementation or empirically calibrated memory model. Do not rank the two RTL systems by incompatible internal cycle counts.

The CI workflow fires on its own YAML changes **only on `research/quantized-mxu-g12`**, plus explicit manual dispatch. There is **no `pull_request` CI trigger**. No previous project source, weights, or local user PC files were modified by this remote GitHub experiment.
