# v1.0 — 64-row burst-aligned column-buffered compute experiment

**Status:** RTL and analytical reference authored. Actual RTL compilation, simulation and generic synthesis must be verified in CI. No real physical hardware exists.

## Design experiment

For a **fixed 64-row × 4-column signed INT8** matrix-vector workload, one active activation triggers a single contiguous 64-byte column transfer into a 64×8-bit **register buffer** followed by 64 signed multiplies using only 2 or 4 time-multiplexed lanes. Exact-zero activations suppress their whole column transfer; the output remains exactly equivalent to a dense modular signed integer reference.

This addresses the 4-byte partial-burst weakness of v0.9 without 64 parallel MACs. It is *not* an integrated physical SRAM; synthesis will implement the buffered data as registers unless replaced with a mapped memory macro. The design has only one outstanding memory request and **cannot overlap column computation with next-column fetch**. It is a deliberate baseline to quantify the next limiting factor.

### Test matrix

CI will test ROWS=8 and 64; LANES=2 and 4; accumulators=16 and 32 bits. The independent dense oracle checks randomized signed inputs, 16-bit wrapping, zero-activation bypass, actual accepted column request count, host-input snapshot, request backpressure, asynchronous reset, and completion pulse. A separately implemented Python reference verifies 64-row traffic and modelled minimum-burst utilization.

### Conditional external traffic for fixed workload

With exactly two active inputs, 64 total rows, 4 input columns, INT8 weights, a hypothetical **64-byte minimum transfer**, and one independent transfer per active column per row tile:

| Row-tile height | Logical requests | Useful bytes | Conditional physical bytes |
|---:|---:|---:|---:|
| 4 | 32 | 128 | 2,048 |
| 8 | 16 | 128 | 1,024 |
| 16 | 8 | 128 | 512 |
| 32 | 4 | 128 | 256 |
| 64 | 2 | 128 | 128 |

This layout **can reduce memory-command overhead under those assumptions**, but there is no measured HBM timing, die area, power, clock, training quality, or GPU comparison. The external memory testbench returns exactly 64 bytes; this does not prove an HBM controller can deliver them at a specified rate.

## Next falsifiable gates

1. Run and independently inspect Icarus and Yosys CI results for every parameter combination.
2. Quantify actual controller cycles and generic logic area for LANES=2 vs 4 and 64-row buffer.
3. Add banked register/SRAM-macro memory and **two-buffer prefetch overlap**, measure if request/compute serialization dominates.
4. Measure real trained model activation zeros. Two earlier pretrained checkpoints had **no exact-zero weights**, but this does not establish their activation distributions.
5. Revisit algorithm and model family if there is no task-quality-matched advantage over tuned GPUs. A passing microkernel is not success.

## Verified GitHub Actions results

GitHub Actions run [45259340579](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45259340579), job 137989557786, **completed successfully**. The following were verified in the job logs:

- 8 Icarus Verilog configurations × 95 cases each = **760 passing RTL test transactions**.
- 7/7 new Python tests and 15/15 prior v0.9 Python regression tests passed.
- Yosys generic synthesis: **19,400 cells** at ROWS=64/LANES=2/ACC=32, and **20,334 cells** at ROWS=64/LANES=4/ACC=32.
- For the stated controller, 2 lanes need 32 active compute cycles per 64-row column; 4 lanes need 16. The four-lane candidate adds approximately **4.8%** counted generic cells. Clock periods, energy and physical SRAM are *not measured*.

Detailed source and limitations: [CI_EVIDENCE_2026-11-23.md](docs/CI_EVIDENCE_2026-11-23.md).
