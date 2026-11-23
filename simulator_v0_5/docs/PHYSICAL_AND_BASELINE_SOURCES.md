# Hardware and benchmark evidence register — 2026-11-23

Only published specifications are reported here; no hardware was measured by this project. Explicitly distinguish physical vendor evidence from assumptions and from project simulations.

| Evidence | Verified primary source | What it establishes | What it does NOT establish |
|---|---|---|---|
| NVIDIA Rubin single GPU | [NVIDIA HGX official](https://www.nvidia.com/en-us/data-center/hgx/) | Individual GPU: 288 GB HBM4, 22 TB/s nominal memory bandwidth, 3.6 TB/s NVLink bandwidth. HGX NVL8: eight Rubin GPUs and 130 TB/s aggregate HBM4 bandwidth in the system. | Whether hardware has been shipped to user; measured Qwen2.5-32B single-request decode rate; memory stacks per Rubin; wall plug efficiency |
| Micron HBM4 12H | [Micron HBM4 product page](https://www.micron.com/products/memory/hbm/hbm4), [March 2026 manufacturer press release](https://investors.micron.com/news/press-release/2026/Micron-in-High-Volume-Production-of-HBM4-Designed-for-NVIDIA-Vera-Rubin-PCIe-Gen6-SSD-and-SOCAMM2-03-16-2026/default.aspx) | 36GB/12H and greater than 2.8TB/s *per stack* peak; improved energy efficiency vs HBM3E in vendor test conditions | Sustained bandwidth in an imagined multi-module board, memory-controller/host power, package-level signal integrity |
| UCIe 3.0 and 4.0 | [UCIe consortium specification index](https://www.uciexpress.org/specifications/ucie-3-0) | UCIe 3.0 added 48/64 GT/s. UCIe 4.0 describes on-package memory links reaching **up to 93.75% data efficiency** and ~2.5 TB/s/mm die-edge bandwidth density. | These raw data rates are **not Gbit/s per lane** without an encoding/modulation/protocol description; not evidence of 64 Gbit/s at a motherboard connector; not a lab-validated PHY for this design |
| Contemporary HBM3E GPU | [AMD MI355X official](https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html) | 288 GB HBM3E, nominal 8 TB/s, vendor typical board power 1,400 W | Fair equal-memory-generation comparison to new eight-HBM4 concept; measured wall power for same model and inference mode |
| Inference reference suite | [MLCommons Inference reference](https://github.com/mlcommons/inference), [MLPerf Inference v6.0 results repository](https://github.com/mlcommons/inference_results_v6.0) | Public benchmark protocols, model/configuration definitions, reproducibility and some published results | No matching Qwen2.5-32B/BF16-KV/4-bit/32K batch-one baseline has been extracted and verified for this project |

## Inputs that are *not* vendor facts

- 70% HBM4 achieved/sustained utilization, 200 TOPS per eight-package module, 128 GB/s payload per link, 120 ns per hop, 80 ns injection, 85% protocol efficiency, and the schedule's exact overheads are *chosen hypothetical parameters*.
- `RawLinkHypothesis(raw_gbits_per_sec_per_lane=64)` uses a **hypothetical 64 Gbit/s serial line-rate**, not a conversion from a UCIe 64 GT/s figure. Full-duplex links count two sets of lanes. With 98% hypothetical encoding and 85% protocol efficiency, 128 GB/s one-way payload requires 20 lanes in each direction, 40 per duplex link. A 2×4 mesh has 10 undirected links, thus 400 directional lanes across the assembly. There is NO proven PHY or available die-edge layout.
- 0.3 pJ/bit *delivered*, 275 W per compute package, 20 W per HBM stack, 150 W host, 20% cooling allowance, 1400 W per-package heat ceiling, and 2200 W total hypothetical compute power are **assumption sensitivity inputs**. They are not a power specification, power meter reading, thermal solution, or physically derived estimate.
- The toy sparse matrix data reduction is exact *only for its constructed matrix*. A 32B-parameter trained model's structural zeros and answer quality have NOT been tested.
- Rubin's advertised 22 TB/s and our assumed 22.4 TB/s are similar **peak capacity classes**, not equal runtime throughput or proof our design is competitive.

## Benchmark comparability protocol

Before claiming GPU superiority: same task and acceptance-quality threshold, input/output lengths, batch/concurrency, model/configuration, precision/KV format, quantization metadata, silicon and memory generation class, system scale, runtime/software versions, thermal state, cold/warm timing, wall power and multiple-run uncertainty. If the model architecture changes, quality-equalize on held-out tasks and count prefill, preprocessing, retrieval and training costs where relevant.

**Do not convert an abstract analytical 'output step/s' into a published MLPerf 'tokens/s' result.** Neither the workload/precision, service rules, system boundary nor result quality would match.
