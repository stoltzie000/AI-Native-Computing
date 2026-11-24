# G1 alternative dataflow research — 2026-11-24
Evidence class E1 analytical bounds; no model trained, hardware benchmark or quality equivalence. Prior source traffic proxy 17.875 GB weights + 8.590 GB state traffic per decode step; controller peak 20.48 TB/s. Hold weights, bandwidth and all other costs fixed; vary remaining state traffic fraction f. Upper bound 20480/(17.875+8.590*f), SI units. Even perfect state elimination improves this memory-only ceiling by only 26.465/17.875 = 1.48056x; cannot yield 2x. For 2x at zero state traffic weight traffic must be <=13.2325 GB, at least 25.97% less than baseline weights. These are conditional bounds, not attainable speedups. Compute, state writes, reconstruction, cache metadata and quality constraints excluded.

[
  {
    "remaining_state_fraction": 0,
    "traffic": 17.875,
    "ceiling": 1145.7342657342658,
    "relative": 1.4805594405594404
  },
  {
    "remaining_state_fraction": 0.25,
    "traffic": 20.0225,
    "ceiling": 1022.8492945436384,
    "relative": 1.321763016606318
  },
  {
    "remaining_state_fraction": 0.5,
    "traffic": 22.17,
    "ceiling": 923.7708615245826,
    "relative": 1.1937302661253946
  },
  {
    "remaining_state_fraction": 0.75,
    "traffic": 24.3175,
    "ceiling": 842.1918371543128,
    "relative": 1.0883108872211371
  },
  {
    "remaining_state_fraction": 1,
    "traffic": 26.465,
    "ceiling": 773.8522576988476,
    "relative": 1
  }
]

## Research decisions
ADOPT FlashAttention as optimized exact-attention baseline, not a proprietary innovation: https://proceedings.neurips.cc/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5-Abstract.html . Tiling reduces intermediate IO but does not eliminate decode KV reads.
TEST MLA, compressed state with extra projection/reconstruction costs: https://aclanthology.org/2025.acl-long.1597/ . Do not assume compression is lossless or equal to this traffic sweep.
TEST selective SSM and hybrid: https://arxiv.org/abs/2312.00752 and https://arxiv.org/abs/2405.21060 . Controlled 8B study https://arxiv.org/abs/2406.07887 reports pure SSM weaknesses in copying, in-context learning and long-context reasoning; hybrid performed competitively on reported tasks. Published results not independently reproduced. Prioritize hybrid as research candidate, not final architecture. No external code copied; licensing must be checked before reuse.
## Next experiment
Implement matched trace accounting for attention/SSM/hybrid state storage and movement with actual pinned model configurations; compare optimized GPU implementations on identical task quality, including copying, retrieval, long context, reasoning and throughput. Reject architecture advantage if disappears under equal workload quality or equal hardware budget. Test recurrent update kernel versus independent reference; record numerical stability and bandwidth costs. G1 remains OPEN.
