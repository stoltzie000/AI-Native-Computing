# Primary Sources and Assumptions (checked 2026-11-23)

| Claim | Source | Use |
|---|---|---|
| Qwen2.5-32B-Instruct hidden_size=5120, num_attention_heads=40, num_key_value_heads=8, layers=64, max_position_embeddings=32768 | [Model config](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct/blob/main/config.json) | Derive KV geometry and context reference. Parameter count 32.5B is approximate model naming/data. |
| RTX 5090 32 GB GDDR7; peak 1792 GB/s | [NVIDIA RTX 5090](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/) | Manufacturer memory spec ONLY. |
| H200 141 GB HBM3e, up to 4.8 TB/s | [NVIDIA H200](https://www.nvidia.com/en-us/data-center/h200/) | Manufacturer memory spec ONLY. |
| MI355X 288 GB HBM3E, peak 8 TB/s | [AMD MI355X](https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html) | Manufacturer memory spec ONLY. |
| Roofline uses operational intensity and memory/compute limits | [Williams et al., 2009, Roofline](https://escholarship.org/uc/item/5tz795vq) | Analytical framework, not calibrated prediction. |
| On-chip vs off-chip traffic matters for attention | [Dao et al., FlashAttention, NeurIPS 2022](https://proceedings.neurips.cc/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5-Abstract.html) | Motivation for accounting for movement. |
| SRAM-centric systems have been produced at wafer scale (Cerebras WSE-3, 44 GB SRAM) | [Cerebras WSE-3 release](https://www.cerebras.ai/press-release/cerebras-announces-third-generation-wafer-scale-engine) | Research precedent, not feasibility proof for 4x12 GB modules. |
| PIM for AI remains an active research direction | [PIMBA, MICRO 2025](https://uu.diva-portal.org/smash/get/diva2%3A2026046/FULLTEXT01.pdf) | Competing architecture, results not independently verified here. |

**NOT sourced or measured:** 100/40 TOPS comparator compute ceilings; memory/utilization factors; candidate 8/4/16-node module capacity, SRAM bandwidth, fabrication viability, fabric topology/latency, energy or output accuracy. These are scenario inputs, deliberately not factual hardware claims.
