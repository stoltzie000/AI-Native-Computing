# Prototype v0.6 — block-sparse processing element (RTL candidate)

**Date:** 2026-11-23. **Status:** HDL SOURCE AUTHORED, RTL SIMULATION/SYNTHESIS NOT YET CONFIRMED; CPU reference tested. No physical chip or FPGA built. This is **NOT** a competitive hardware claim.

## Purpose

Translate the first algorithmic experiment into a hardware operator: a processor that can skip a block **when and only when the controller certifies its weights are all zero**, and otherwise performs signed matrix-vector arithmetic. This is a small candidate microarchitecture for an AI-native processor; not a graphics chip, transformer accelerator or complete AI computer.

## Modules

- `rtl/block_sparse_pe.v` — Verilog-2001-style sequential INT8xINT8/INT32 block-sparse processing element, with flattened data buses, start/done handshake, zero-block bypass, operation counter and cycle counter. Default 4x4 block. For supported widths: `ACC_W >= 2*DATA_W`; `BLOCK_SIZE^2` must fit the 16-bit index.
- `rtl/tb_block_sparse_pe.v` — three representative testbench cases: active 4x4 computation, certified zero-block skip, and signed negative weights.
- `rtl_reference.py` — independent Python signed-INT8 arithmetic and expected cycle schedule, **not** a Verilog compiler.
- `test_rtl_reference.py` — 11 CPU-only reference tests incl. deterministic 100 randomized 4x4 matrices and invalid metadata handling.
- `docs/VERIFICATION.md` — traceability, falsification and tool prerequisites.
- `.github/workflows/sparse-rtl-tests.yml` — in repository root, designed to install/run Icarus Verilog in GitHub Actions. This workflow must be examined for actual run success; creating it is not proof it passed.

## Core behavior

`start` sampled while idle; `block_valid=0` bypasses computation in two inclusive controller clock edges (`start` then `done`), leaving output all zero and issued multiplications at zero. **The metadata must be correct**. Active 4x4 uses one signed 8-bit multiplication per clock for 16 cycles; done follows in the next clock. Four signed 32-bit row sums are output. The data buses must stay stable during the run. The module has *no external SRAM/HBM controller, sparse index loader, input FIFO, multi-block pipeline, clock constraints, synthesis flow, power/area estimation or transistor layout.*

This intentionally tiny, low-throughput unit is chosen to validate **correctness and arithmetic behavior** before attempting a massively parallel design. It is **not claimed faster than any CPU/GPU**.

## Run locally or in CI

Python-only reference (already run locally):

```
python -m unittest discover -s prototype_v0_6 -p 'test_*.py' -v
```

Icarus RTL functional simulation (requires Icarus Verilog installed; **unavailable in the ChatGPT isolated container during authoring**):

```
mkdir -p prototype_v0_6/build
iverilog -g2012 -Wall -s tb_block_sparse_pe -o prototype_v0_6/build/pe_tb \
  prototype_v0_6/rtl/block_sparse_pe.v prototype_v0_6/rtl/tb_block_sparse_pe.v
vvp prototype_v0_6/build/pe_tb
```

Passing `vvp` should print `PASS block_sparse_pe RTL functional tests`. The GitHub workflow is intended to test this automatically. **Until a real successful RTL simulator run is observed, HDL correctness remains unverified** despite the Python reference tests.

## Engineering caveats

- A generic trained dense model has few/no certified all-zero blocks. Injecting sparsity by modifying weights can change model answers; exactness proof only applies to the unchanged sparse matrix.
- Output of one PE does not include accumulation across adjacent K blocks; a network/dataflow scheduler is required and must be independently tested.
- This design uses sequential arithmetic and full parallel flattened weight inputs, not efficient SRAM/HBM/PHY packaging. A real design must replace bus-based toy input with carefully staged memory accesses.
- No evidence of quality-equivalent reduction on trained 32B models. No silicon, board, area, voltage, clock rate, power or benchmark measurements.
