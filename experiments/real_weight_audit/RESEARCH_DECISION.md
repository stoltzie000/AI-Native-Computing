# Decision after actual trained-weight experiment — 2026-11-23

## Evidence
GitHub Actions run 45241981337, job 137928727818 completed successfully. Both independently published checkpoint hashes matched downloaded binary files before inspection.

The MicroMixer attention-free 1M checkpoint (874,624 eligible 2D elements) and MicroT attention transformer 300K checkpoint (296,960 eligible 2D elements) both contained **zero exact-zero eligible matrix elements**, zero all-zero 4x4 blocks and zero all-zero 8x8 blocks. Counts and exact hashes are in `results/MEASURED_2026-11-23.json`. This is a direct negative finding, not a simulation.

## Engineering interpretation
- The v0.6/v0.7 **exact-zero weight block skip PE** has no intrinsic opportunity to bypass weights in these *unpruned* model checkpoints. Its toy 75% sparse experiment demonstrated correct conditional arithmetic, not real-model advantage. Deprioritize it as a standalone general AI accelerator.
- v0.8/v0.9 activation-gated implementations depend instead on the fraction of **exact-zero intermediate activations**, which was **not measured** by this weight audit. Zero parameters do not imply zero activations, and nonzero parameters do not rule out zero activations. Run instrumented inference against pinned prompts/datasets to determine the actual gating opportunity.
- Creating zero blocks by structured pruning or altered training is a possible research direction, but requires evidence of preserved task accuracy/quality and costs for training/metadata/reformatting.
- The v0.9 column-major/burst-aligned memory candidate is independent of weight zeros and can potentially improve transaction overhead through a new layout, but no physical memory controller or board timing/energy has been demonstrated.
- A superior system cannot be claimed by comparing eight HBM4 stacks against older GPUs; Rubin has a comparable published peak bandwidth class. Use quality-matched GPU and end-to-end system energy measurements.

## Selection state
**Rejected for these samples:** assuming naturally occurring dense-model exact-zero *weight blocks* are a source of acceleration.

**Still open:** exact-zero activation sparsity in real models; memory coalescing/layout advantages in physically realized controllers; near-memory compute; algorithm-model/hardware co-design including alternative non-transformer and non-token tasks; bounded FPGA/ASIC implementation.

## Next falsification sequence
1. Execute pinned actual TinyStories-trained model checkpoints on a defined input suite and log intermediate activation exact-zero fractions and layer geometry with independent task-output checks. Treat downloaded model code as untrusted and review it before execution.
2. If activation zeros are too rare for the v0.8/v0.9 74% weight-traffic reduction target, reject exact-zero gating as the primary source of competitive advantage for those workloads.
3. Implement and simulate a realistic 64-row column buffer with 2–4 time-multiplexed MAC lanes, fixed burst line size and outstanding/queued memory reads; obtain technology-mapped frequency, area and energy estimates.
4. For every candidate, compare against optimized GPU sparse/dense kernels and a physically bounded full-system power/cooling budget. Do not confuse simulator throughput, generic Yosys cells, or small CPU numerical tests with proof of superior hardware.
