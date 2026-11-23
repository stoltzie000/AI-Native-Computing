# AI-Native Computing v0.9 — column-major coalesced gated memory

## Goal
Address v0.8's key bottleneck: one serialized memory request per active *weight*. Reorganize memory so an active activation triggers one burst-like *column request* supplying all row weights for that input column. An exactly-zero activation produces no request and no multiplication for that column.

## Architectural change
- Weight tile stored **column-major**, indices `col*N + row`, instead of row-major. This is a legitimate cross-layer memory/dataflow co-design, but may conflict with other kernels and model layouts; conversion/preprocessing cost must be counted.
- `N` signed multiplier lanes accept one column response and update N row accumulators in parallel.
- Only one outstanding read, in-order response, explicit backpressure.
- External memory model testbench checks accepted column requests and independent dense reference outputs. No physical SDRAM/HBM, cacheline, bank, PHY or timing model is implemented.

## Expected functionality, not performance
For a 4×4 INT8 weight tile:

| Active input columns | v0.8 element requests | v0.9 column requests | Logical useful weight bytes | Zero-skipped weight elements |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 16 |
| 1 | 4 | 1 | 4 | 12 |
| 2 | 8 | 2 | 8 | 8 |
| 3 | 12 | 3 | 12 | 4 |
| 4 | 16 | 4 | 16 | 0 |

**Crucial physical limitation:** A 4-weight INT8 column is only **4 bytes**, potentially far smaller than a real memory burst. With hypothetical 64-byte minimum independent transfers, four active columns require 256 physical bytes despite 16 useful weight bytes—6.25% utilization. A real HBM controller might coalesce requests across a larger tile, or might not; neither is implemented yet.

## Verification
The Python oracle in `reference.py` cross-checks exact signed arithmetic, zero-gated fetch coordinates, and a simple configurable minimum-burst calculation; the HDL bench executes a deterministic randomized, stall/reset/handshake suite. CI: `.github/workflows/rtl-v09-verification.yml`. **No local or remote RTL result is claimed until a completed CI run is inspected.**

## Next design decision
Scaling N to ≥64 could fill a hypothetical 64B minimum transfer at INT8, but 64 parallel MACs, wiring, memory banking and register width increase silicon and power demands. Alternative: stage a larger column into a local SRAM buffer and time-multiplex 2–4 lanes. Both need model/RTL tests and a justified physical memory specification.

Before claiming any advantage over optimized GPUs, measure exact-zero activation statistics on real trained models, equal task quality, physical burst traffic, whole-system energy, and real runtime latencies. The project is not completed by passing this PE test.
