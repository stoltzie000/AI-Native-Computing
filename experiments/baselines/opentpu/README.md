# Reproduction gate R01 — openTPU ISA and RTL baseline

Status: **48 external ISA/dataflow/compiler tests reproduced; external RTL differential still unverified.** Three historical Verilator 5.020 runs encountered tooling/parser failures, documented in [FAILURE_AND_COMPATIBILITY_LOG.md](FAILURE_AND_COMPATIBILITY_LOG.md). The next trial builds **Verilator 5.054 from pinned upstream commit** and tests **openTPU RTL unchanged**. Do not claim a passing RTL baseline until successful job logs and JUnit evidence are verified.

## Why openTPU first

The AI-Native-Computing `PROJECT_STATE.md` identifies reproduction of a substantive existing accelerator as the next step after negative trained-model weight- and activation-sparsity findings. [openTPU](https://github.com/FeSens/openTPU) is a real accelerator stack with ISA emulator, RTL and upstream FPGA hardware reports. Its Python/Verilator test paths are smaller to reproduce than the full Gemmini/Chipyard generator.

## Immutable provenance and rights

- Upstream owner: `FeSens/openTPU`.
- Frozen upstream **commit**: `d84db55712aba0d40811d7762cb052f05d55b7e5` (retrieved through connected GitHub repository API; 2026-11-11).
- [Source tree](https://github.com/FeSens/openTPU/tree/d84db55712aba0d40811d7762cb052f05d55b7e5).
- Upstream root LICENSE checked: **Apache License, Version 2.0**. Reproduction runs the upstream source in a temporary CI checkout; it does not copy or merge the upstream source into this repository.
- Runtime: GitHub-hosted Ubuntu, CPython 3.11, pinned NumPy/Pytest version plus upstream `pip install -e .`, apt-installed Verilator (record exact version). Dependency freeze is retained in CI artifact.
- No pretrained model downloads, FPGA allocation, credentials, manufacturing or board writes are required for this test.

## Pre-registered tests

1. Independent ISA simulation and instruction encoding: `tests/test_isa.py`.
2. Memory layout and transaction accounting: `tests/test_dataflow.py`.
3. Selected compiler/runtime dataflow cases:
   - `test_hardware_loop_lowering_uses_address_registers`
   - `test_rows_loaded_into_an_accumulators_tile_go_one_ld_a_row`
   - `test_dot_chunks_rows_beyond_mxu_columns`.
4. Verilator-vs-ISA **actual RTL comparison**: `tests/test_rtl.py::test_fuzz_mm_replay[2-8-0]`. This builds the upstream RTL simulator and checks DRAM/TMEM bit-for-bit after a fixed-seed MM replay workload. **A skipped RTL test is failure**, not a passing hardware result.
5. Our own independent v1.0 Python reference regression is also run to ensure no accidental local breakage. The two architectures' kernels/precision/layout are not yet identical and **no speed or energy superiority comparison is permitted**.

### Proof standard

The GitHub job must (a) confirm exact upstream SHA, (b) pass at least 20 external functional tests, (c) run and pass at least 1 real non-skipped Verilator/ISA RTL test, (d) retain machine-readable JUnit reports and tool versions, and (e) explicitly disclose limitations.

**No equivalent current GPU benchmark, physical openTPU card, device clocks/power or fair workload-normalized throughput is reproduced here.** Those require separate, controlled experiments. An upstream reported FPGA token rate is not our direct measurement.

## Notification control

The workflow is configured for push on **only this research branch and only when the workflow YAML itself changes**, plus explicit manual dispatch. There is **no pull_request trigger**, so ordinary source/document edits and PR activity cannot generate duplicate test runs. Merging to main should not retrigger this gate.

## Next decision

A green external ISA+RTL reference enables apples-to-apples operator/dataflow test planning, with a frozen executable control. It does **not** imply that our v1.0 is better, equivalent or worse. Next gate is to construct same INT8 matrix-vector workload and same physical memory transaction model in both systems, and ultimately instrument physical FPGA or ASIC systems.
