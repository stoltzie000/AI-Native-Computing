# v0.9 coalesced memory architecture: verification & selection (2026-11-23)

## What is demonstrated

GitHub Actions run **45240716833**, job **137924272265**, completed **success**.
- Independent Python oracle 8/8 tests passed at the original RTL checkpoint.
- Icarus Verilog: **132** randomized/fixture/reset/backpressure cases at 16-bit accumulation, plus **132** at 32-bit = **264 total**. Testbench checks full dense arithmetic and external accepted read requests.
- Yosys generic synth completed; **5370 generic cells** for default N=4 INT8 ACC32. These are not standard-cell physical area, frequency, power or GPU performance.

Subsequently added `memory_tiling.py` and seven independent tests. Treat these tests as **unverified until a later CI run** logs their success.

## Topology and request demonstration

In v0.8, one active column in a 4x4 tile requested 4 weights individually; in v0.9 a transposed/column-major weight layout supports one request for a four-weight column. Both read the same four useful weight bytes. A zero activation suppresses all four rows' weight accesses. This is a small and rigorously tested logical memory-request advantage.

However, a 4-byte column request need not map to a 4-byte physical bus transaction. If every request transfers at least 64B, a 4x4 tile with four active columns fetches 256B for only 16B of useful weights (6.25%). This alone does **not** establish effective bandwidth or power savings.

## Fixed total work: tile height sensitivity

The new **conditional** row-tiling model holds the matrix at 64 rows × 4 input columns, two nonzero columns, INT8 weights, four MAC lanes, 64-byte minimum independent transfers, 200 memory-first-byte controller cycles per request and 32 bytes/cycle assumed link. It uses an idealized double-buffer overlap bound NOT IMPLEMENTED in RTL and ignores cache hit rates and physical clocks.

| Row tile | Number of row tiles | Column requests | Physically transferred bytes (assumed) | Useful bytes | Utilization | Optimistic total cycles (model only) |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 16 | 32 | 2048 | 128 | 6.25% | 6576 |
| 8 | 8 | 16 | 1024 | 128 | 12.5% | 3296 |
| 16 | 4 | 8 | 512 | 128 | 25.0% | 1656 |
| 32 | 2 | 4 | 256 | 128 | 50.0% | 836 |
| 64 | 1 | 2 | 128 | 128 | 100% | 426 |

**Careful:** A real HBM subsystem has command/bank/prefetch/cacheline and coalescing properties unlike these simple assumptions. This table is a falsifiable sensitivity calculation, NOT measured hardware and NOT evidence of outperforming GPUs.

## Design decision / next falsifiable step

Research **row tile=64 with a much smaller 2- or 4-lane time-multiplexed MAC** and staged column memory into local SRAM. This could amortize burst/latency cost while avoiding 64 simultaneous multipliers. It requires a separate controller/scratchpad/queue, memory schedule, and technology-mapped critical-path evaluation.

Never claim 100% physical HBM utilization on the basis of this conditional 64-byte transaction model. Measure actual trained-model activation sparsity and complete AI-task quality before selecting this as the final accelerator.

The project still has no demonstrated superior processor, motherboard, whole-system energy measurement, or quality-matched GPU comparison.
