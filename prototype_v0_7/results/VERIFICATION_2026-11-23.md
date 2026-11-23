# v0.7 verification evidence log — 2026-11-23

## First failure and correction

GitHub Actions run 45236851823 (job 137910725526) **FAILED** during Icarus Verilog compilation of historical v0.6. `prototype_v0_6/rtl/block_sparse_pe.v` used `cell` as a register identifier, a reserved Verilog/SystemVerilog configuration keyword. Compiler reported syntax errors at lines 25, 37, 38 and subsequent dependent expressions.

Original v0.6 source remains untouched. The branch adds `prototype_v0_7/rtl/block_sparse_pe_v06_compat.v`, a source-preserving copy with only `cell` renamed `cell_index`. The new v0.7 source was also corrected to use `cell_index`. The compatibility source was selected in CI.

Reference: SystemVerilog reserved keywords and configuration syntax, e.g. IEEE 1800 and https://www.vlsimentor.com/verilog/lex-keywords.

## Verified successful HDL run

GitHub Actions run **45237630207** (job **137913469477**) completed **successfully** after the correction.

Verified from job logs:
- v0.6 compatibility source compiled and passed 256 randomized signed/skip differential testbench cases.
- v0.7 compiled and passed 132 cases for each of LANES=1/2/4/8/16 crossed with ACC_W=16/32 — **1320 cases total**.
- Testbenches exercise signed arithmetic, 16-bit wraparound, zero-block bypass, reset, input snapshot, one-cycle done, and spurious start handling.
- Python v0.6 tests: 11/11 passed; Python v0.7 tests including Safetensors synthetic fixtures: 13/13 passed.
- Generic Yosys synthesis of default v0.7 PE completed, with `Number of cells: 7636`.

The numerical tests are deterministic and bounded. They do NOT constitute formal equivalence for all possible states. Some runs share the same randomized test patterns per configuration.

## Evidence boundaries

- 7636 is a Yosys generic logic-cell statistic, not standard-cell area, gate equivalents, FPGA LUT count, transistor count, achieved clock, or measured watts.
- No physically realized PE, complete memory hierarchy, chiplet integration, motherboard, power/thermal measurement, or matched GPU benchmark exists.
- The Safetensors audit passed synthetic fixtures; no genuine pretrained checkpoint was successfully downloaded or measured.
- The zero-block bypass is exact only when the metadata certifies that *every* weight in that block is zero.
- A new generic cell-count parameter sweep was added afterward; its results must be recorded separately only after its own CI run completes.

## Current gate result

**E2 subsystem functional RTL simulation: PASSED for the tested small PE configurations.** Generic RTL synthesis sanity: PASSED for the default variant. Full processor superiority, hardware physical design, and task-quality gates: OPEN.
