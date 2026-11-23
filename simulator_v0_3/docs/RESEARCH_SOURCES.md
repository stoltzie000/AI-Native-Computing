# Provenance and sources — 2026-11-23

| Source | Verified fact used | What it does NOT establish |
|---|---|---|
| [Qwen2.5-32B-Instruct model config](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct/blob/main/config.json) | 64 layers, 5,120 hidden channels, 40 attention heads, 8 KV heads, 32,768 max position setting, 27,648 intermediate dimension | Exact quantized memory-transaction trace or optimized inference latency |
| [NVIDIA RTX 5090](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/) | Advertised 32 GB GDDR7 and 1,792 GB/s bandwidth | Measured Qwen inference or compiler efficiency |
| [NVIDIA H200](https://www.nvidia.com/en-us/data-center/h200/) | Advertised 141 GB HBM3e and 4.8 TB/s bandwidth | Measured Qwen inference or whole-system energy |
| [AMD Instinct MI355X](https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html) | Advertised 288 GB HBM3E and 8.0 TB/s bandwidth | Measured Qwen inference or total-node power |
| [TSMC SRAM research](https://research.tsmc.com/page/memory/4.html) | Published 38.1 Mbit/mm² macro density at N2 research technology | An available low-cost/licensable SRAM macro, a feasible full chip, or that density at another node |
| [Cerebras wafer engine announcement](https://www.cerebras.ai/press-release/cerebras-announces-third-generation-wafer-scale-engine) | Physical precedent for wafer-scale system and ~44 GB SRAM | Feasibility or engineering correctness of the new candidate architecture |
| [MLCommons Inference v6.1](https://mlcommons.org/2026/09/mlperf-inference-v6-1-results/) and [MLPerf official rules](https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc) | Quality-gated task metrics, whole-system power metering and reproducible benchmark methodology | Matched v0.3 proxy throughput for Qwen2.5-32B on a named GPU; no such measurements imported yet |
| [HALO near-memory research](https://arxiv.org/abs/2510.02675), [HPIM](https://arxiv.org/abs/2509.12993), [BOOST](https://mast.stanford.edu/pubs/boost/paper.pdf) | Prior art and alternative memory/dataflow research directions | Independent physical performance proof for our candidate designs |

## Values invented for scenario modeling (not factual hardware specifications)

- Module count, aggregate architecture layout, bank count, transaction latency=0 in many scenarios, useful memory bandwidth=100% default, compute TOPS=500 on each GPU proxy, all fabric bandwidths/latencies, two reductions per layer as mapped, tiles per phase=16, HBM capacities/bandwidths on the new modules, 0.5GB SRAM+4TB/s local bandwidth, weight metadata fraction=10%, 7.5% QKV and 5.5% attention-output weight split, and scratch memory=2GB.
- Derivation of memory traffic: all model weights read per decode step plus KV historical state reads and one token write; batch=1. Treat this as a deliberately conservative workload byte model whose real cache/dequantization/kernel behavior may be very different. Vendor GPUs may use distinct memory-effective algorithms.
- TSMC SRAM area bound = capacity (GB, decimal) ×8e9 bits/GB / (38.1e6 bits/mm²); memory-only lower bound. For 0.5GB: 104.99 mm²; for 12 GB: 2519.69 mm².
- **No estimated power, joules, training capability or model-output quality.** Claims that use these quantities before obtaining measurements would be invented.
