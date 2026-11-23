# Research decision: weight sparsity is not sufficient by itself

Date: 2026-11-23. Evidence level: literature assessment and local arithmetic only; no trained-model checkpoint examined or original hardware measured.

## Competing methods (do not assume ours wins)

| Method | Required property | Evidence | Risk |
|---|---|---|---|
| Exact zero-block skipping (our v0.6/v0.7 PE) | Whole weight blocks contain exact zeros | Mathematically exact for certified zeros, fixture regression | Dense pretrained weights may have few eligible blocks; metadata and fetch overhead |
| SparseGPT | Prune weight elements after training | Original ICML paper reports 50–60% unstructured sparsity with small accuracy changes on selected LLMs | Unstructured zero weights do NOT imply 4x4/8x8 fully zero blocks |
| TEAL | Dynamically induce activation sparsity | ICLR 2025 authors report up to 1.53x/1.8x GPU decode speedups at 40%/50% model-wide activation sparsity | Approximation/quality evaluation and dynamic indexing, strong existing GPU competitor |
| RoShift | Rotate/shift activation representation for sparse execution | Nov 2026 arXiv preprint reports up to 1.72x speedup versus a dense RTX 5090 reference at 50% sparsity | Independent validation not available here; equivalence and software adaptation needed |
| Exact activation-gated dataflow | AI activation is EXACT zero and its associated weight work can be omitted | Conditional mathematical identity, not a GPU-beating processor | Need architectures with actual zero activations, plus memory skip/dispatch timing |
| Shared memory and two-package compute | Reduce package collectives relative to 8-node mesh | Prior v0.5 conditional equal-resource model | No physically verified controller/cooling, conventional GPU may already do this |

Primary sources:
- SparseGPT paper: https://proceedings.mlr.press/v202/frantar23a.html
- TEAL ICLR paper: https://proceedings.iclr.cc/paper_files/paper/2025/hash/f3f2ff9579ba6deeb89caa2fe1f0b99c-Abstract-Conference.html
- RoShift preprint: https://arxiv.org/abs/2611.20549
- Tiny alternative-model checkpoint candidate: https://huggingface.co/llaa33219/MicroMixer-4-1M-TinyStories/blob/main/epoch_2.safetensors

## Originality and quality gate

A competitor achieving 1.8x GPU decode speedup with sparse software kernels is evidence that sparse arithmetic alone is NOT a novel or sufficient win. Our processor needs a measured additional advantage against an optimized sparse GPU, not just against dense baseline execution.

Equal task quality is mandatory. Exact-zero skipping has lossless arithmetic *only when exact zeros are present*; any post-training pruning or thresholding to CREATE zeros must be evaluated for task quality, not assumed harmless.

## Next falsifiable trials

1. Obtain and hash a genuinely trained checkpoint, then run the read-only safetensors audit. At least one dense transformer and one non-transformer/attention-free checkpoint should be included.
2. Measure exact 4x4 and 8x8 zero-block fractions and metadata overhead. If the fractions are negligible, **reject pure weight-zero-block skipping as the primary compute architecture for those models**.
3. Implement an exact activation-gated test operator on fixed signed arithmetic and compare traffic, scheduling and energy assumptions against the existing block-sparse PE.
4. Compare the sparse operator and hypothetical accelerator against current GPU inference software that ALREADY exploits sparsity. Report kernel time, host/power boundary and end-task quality.
5. Continue evaluating compute-in-memory, state-space, recurrent and event-driven systems that are not designed exclusively around tokens.

## Explicitly unknown

Actual pretrained weight zero-block distribution, effect of approximation on quality, SRAM/HBM energy, physical RTL timing, motherboard feasibility, and competitive GPU performance. No external model weights were successfully downloaded in this session; do not report a measured sparsity percentage.
