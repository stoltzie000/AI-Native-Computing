# Prior-art and technology evidence matrix — 2026-11-23

**Research scope:** User's AI-Native Processor Researcher Handoff, R01–R15, plus commercially fabricated and academic alternatives. This is a **source review**, not an independent replication of each project. The project goal is demonstrated quality-matched AI computing superiority over strong GPUs; no such general victory has yet been shown by our project.

**Evidence tiers:** A independent physical replication; B published physical measurement (may be author/vendor reported); C FPGA measured/emulated; D verified RTL/generic synthesis, no physical device; E software model/simulation; F unsupported. Assign **highest evidenced tier**, without conflating mixed claims. An author's advertised verification is source evidence, not independently reproduced by our audit. Numeric published memory bandwidth is a **specification**, not model-throughput measurement.

## Named GitHub projects — source audit

| ID | Project | Implemented and evidence (highest tier) | Useful assets / present limitations | License status checked | Disposition |
|---|---|---|---|---|---|
| R01 | [FeSens/openTPU](https://github.com/FeSens/openTPU) | RTL, ISA, compiler, simulator, host and measured Kintex-7 FPGA inference; **C**, ASIC NanGate45 layout **D**, not fabricated ASIC | Strong integrated reference and test method; FPGA speed strongly bandwidth-bound, no contemporary quality/power-matched GPU comparison | Apache-2.0 | **ADAPT** |
| R02 | [bojieli/OpenTallas](https://github.com/bojieli/OpenTallas) | Model-specific ROM/weight silicon research, ABI3 compiler/runtime, functional RTL, open-PDK and numerical models; **D/E**; author explicitly says no fabricated chip | Detailed falsification checklist; mask-ROM density, analog behavior, full physical integration and real-silicon throughput unverified | MIT | **TEST** |
| R03 | [manageryzy/OpenTaalas](https://github.com/manageryzy/OpenTaalas) | Kanagawa/SystemC/Verilator LLaMA decoder modules and reported co-sim; **D claimed**, no independently verified silicon or FPGA | INT3×INT8, codebook/dequantization, model-in-logic ideas; end-to-end real hardware and total area unresolved | WTFPL v2; separate patents/IP must still be checked | **TEST** |
| R04 | [SigmanticAI/APEX](https://github.com/SigmanticAI/apex-inference-chip) | Verified transformer-layer RTL and reported **real FPGA** host-mode demonstration; measured token rate reported for Qwen2.5-0.5B; **C** | Bit-exact oracle, KV compression, detailed bug logs; not an actual complete 7B silicon design, host versus walked FPGA path must be separated | Apache-2.0 | **ADAPT** |
| R05 | [Berkeley Gemmini](https://github.com/ucb-bar/gemmini) | Reconfigurable Chisel systolic generator, scratchpad and full-stack simulator; **D**, related academic fabrication does not prove a particular configuration | Reusable experiment/control architecture, kernel and dataflow model; not assumed a final winning topology | UC Regents redistribution license (BSD-like, nonstandard SPDX) | **ADOPT research baseline** |
| R06 | [Berkeley Chipyard](https://github.com/ucb-bar/chipyard) | SoC generator and simulators, FireSim/Hammer integration; **D/C tool flows**, not one fixed benchmarkable AI chip | Full-stack reproducibility and physical-flow infrastructure; considerable environment/dependency complexity | BSD-3-Clause main project, dependency-specific terms | **ADOPT research infrastructure** |
| R07 | [NVIDIA NVDLA](https://github.com/nvdla/hw) | Older RTL, C-model and testbench, public hardware architecture; **D** for repo, deployments not audited | Golden tests, memory interface/verification reference; older CNN orientation | **Special NVIDIA Open NVDLA License**; explicit terms/acceptance; not Apache/BSD | **HOLD** |
| R08 | [DeepStack](https://github.com/tile-ai/DeepStack) | 3D-DRAM accelerator/distributed inference **simulator**, not hardware; **E** | Custom memory/interconnect sweeps and energy model; **proprietary precompiled simulator binaries/calibration withheld** | Mixed Apache-2.0 sources + restricted proprietary binaries (verified LICENSE) | **TEST**, code reuse review |
| R09 | [PKU ATLAS MICRO 2026](https://github.com/pku-gsun/ATLAS-MICRO-2026) | Cycle simulation + HotSpot thermal modeling + operator frontends; **E**, paper's 'silicon-proven' phrase does not mean ATLAS hardware exists | Strong thermal-aware methodology; industrial settings partially anonymized/simplified | Apache-2.0 | **ADAPT** |
| R10 | [KAIST NeuPIMs](https://github.com/casys-kaist/NeuPIMs) | NPU/PIM/DRAMSim3 combined **simulator**; authors report modeled 3× vs GPU-only in selected batch LLM workload; **E** | Compare heterogeneous PIM dataflows and timing; in-house PIM simulator and parameter fidelity require examination | No root LICENSE verified; **rights unresolved** | **TEST**, no code reuse yet |
| R11 | [FeSens auto-arch-tournament](https://github.com/FeSens/auto-arch-tournament) | Constrained AI RTL-edit/evaluate loop: equivalence plus multi-seed FPGA P&R; **C for measured FPGA timing flow**, CPU-specific not AI accelerator proof | Import gatekeeping, champion/archive, random seeds, anti-metric-hacking | Apache-2.0 | **ADAPT method** |
| R12 | [SparseCraft](https://github.com/SARCS-IIITH/SparseCraft) | Agentic Gemmini cross-stack loop, reported cycle/traffic improvements in **RTL simulation** and power estimated via model; **D/E** | Fitness/legality gates, multi-objective Pareto selection; published perf/W is **modeled**, not wattmeter data | No root LICENSE verified; rights unresolved | **ADAPT methods only; HOLD copying code** |
| R13 | [Tenstorrent tt-metal](https://github.com/tenstorrent/tt-metal) | Production programming stack and reported model demos on fabricated Tenstorrent systems; **B** for first-party system numbers | Dataflow kernel/runtime, communication and profiling; source is **software, not full chip RTL** | Apache-2.0 software; hardware IP proprietary | **ADAPT runtime methods** |
| R14 | [Mamba SSM](https://github.com/state-spaces/mamba) | Executable selective state-space model/training and GPU selective scan; **B for software-on-real-GPU**, not new silicon | Strong non-attention/alternative state memory candidate; must compare task quality and training effort | Apache-2.0 | **TEST** |
| R15 | [LLaDA](https://github.com/ML-GSAI/LLaDA) | Implemented diffusion language model and sampling; **B for GPU software**, no custom chip | Challenge left-to-right dependencies; many denoising passes and memory costs may negate parallelism | Repo root license **not verified**; individual public model licenses vary | **TEST**, review terms |

### Claim caveats directly from upstream
- openTPU reports FPGA Qwen3-0.6B at roughly 21.6 tok/s INT8 single stream (and other numbers). These are **their** device/workload measurements, not a Rubin/H200-matched victory. [README](https://github.com/FeSens/openTPU).
- APEX advertises 0.56 tok/s measured for a Qwen2.5-0.5B FPGA experiment and separately describes 7B-sized architecture; these are **not the same level of implementation**. [README](https://github.com/SigmanticAI/apex-inference-chip).
- SparseCraft's 2.10× simulated cycle reduction and 5.61× modeled perf/W should be tagged **RTL simulation plus energy model**. [README](https://github.com/SARCS-IIITH/SparseCraft).
- NeuPIMs' 3× GPU-only result is a **simulation study** (ISCA 2024), not a silicon measurement: [paper](https://arxiv.org/abs/2403.00579).

## Additional built hardware / proposed architectures

| ID | Source | Evidence | Reuse / bottleneck | Disposition |
|---|---|---|---|---|
| X01 | [Taalas HC1](https://taalas.com/products/) | **B:** Fabricated 6nm model-specific silicon; company reports ~17k output tokens/s/user for Llama 3.1 8B | Model parameter immutability, area and update/retrain costs; vendor quality/power comparison not independently verified | **TEST** physical idea; **HOLD** superiority claim |
| X02 | [Cerebras WSE-3](https://www.sec.gov/Archives/edgar/data/2021728/000162828026029503/cerebras-sx1amay2026.htm) | **B:** Fabricated/deployed wafer-scale chip; [2026 H100 comparison](https://ieeexplore.ieee.org/abstract/document/11652002) exists | On-wafer memory and locality; full model capacity, cooling, yield, external memory and chip economics | **ADAPT** architecture lessons |
| X03 | [IBM NorthPole](https://research.ibm.com/publications/neural-inference-at-the-frontier-of-energy-space-and-time) | **B:** Fabricated memory-compute inference chip; reported 25× FPS/W and 22× lower latency vs process-comparable GPU on ResNet50 | Strong *workload-specific* proof memory locality matters; capacity and universality remain issues | **ADAPT** |
| X04 | [IBM PCM analog inference](https://www.nature.com/articles/s41467-025-63794-4) | **B:** Fabricated 14nm chip, ALBERT transformer mapped; measurable analog drift and correction | Physical weight density; ADC/DAC, temporal drift, accuracy and generality | **TEST** |
| X05 | [Intel Loihi 2/Hala Point](https://www.intel.com/content/www/us/en/newsroom/news/intel-builds-worlds-largest-neuromorphic-system.html) | **B:** Fabricated event-driven neuromorphic processor and deployed multi-chip system | Sparse temporal events can win in event data; translating modern LLM tasks remains unproven | **TEST** on event workloads |
| X06 | [Lightmatter Passage](https://lightmatter.co/press-release/lightmatter-achieves-record-1-6-tbps-per-fiber-to-accelerate-ai-optical-interconnect/) | **B:** First-party sampled photonic chiplet/link throughput (1.6 Tb/s/fiber claimed) | Board/rack interconnect, not equivalent to full photonic AI matrix compute; optical-electric power must be counted | **TEST** link integration |
| X07 | [2026 reconfigurable photonic tensor processor](https://www.nature.com/articles/s41467-026-71599-2) | **B:** Fabricated/packaged optical tensor processor, MNIST/CIFAR inference | Physical photonic inference exists; accuracy modest for harder tasks and conversion/systems unproven | **TEST** niche precision |
| X08 | [Tri-Stack-PIM](https://arxiv.org/abs/2611.13644) | **E:** Nov 2026 proposed heterogeneous stacked DRAM/buffer/logic, modeled speedups | Valuable split-die idea; no observed physical GPU-beating system in source | **TEST** modeling only |
| X09 | [Google TPU7x](https://docs.cloud.google.com/docs/compute-area/tpus) | **B:** Commercial purpose-built tensor hardware with published capacity/throughput specifications | Important **specialized** non-GPU physical comparison, not evidence of our work | **ADOPT benchmark** |

## Baseline evidence and licensing rules

Current published *hardware peak specifications*, **not application benchmarks**:
- [NVIDIA Rubin](https://www.nvidia.com/en-us/data-center/hgx/): up to 288GB HBM4 and 22TB/s per GPU.
- [AMD MI355X](https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html): 288GB HBM3E and 8TB/s per GPU.
- [Google TPU7x](https://docs.cloud.google.com/docs/compute-area/tpus): 192GiB HBM and published ~7.38TB/s per chip (Google reports its units as GBps).

Do NOT compare those peak specifications to any candidate's measured output rate. Full matched application metrics are missing.

### Intellectual-property and provenance warnings
1. `LICENSE` for Gemmini was read directly: UC Regents 3-clause-like conditions; license metadata reported NOASSERTION. Preserve notices.
2. DeepStack has open Apache source **but proprietary .so components** with limited grants and withheld calibration code. Treat reuse of those binaries separately.
3. NVDLA is governed by NVIDIA's own Open NVDLA License; do not silently accept its terms by copying.
4. NeuPIMs, SparseCraft and LLaDA repository root license files could not be verified in this audit. **No root file found does not prove no license or permission.**
5. Academic papers do not grant unrestricted patent or semiconductor-layout rights; perform a separate IP/patent review before fabrication.

### Provenance (GitHub README Git blob SHAs read 2026-11-23)
`R01 ea24c76f4799; R02 b2f093a18e71; R03 6fc0bea1088e; R04 8c3b62059079; R05 85c22b6f5a3f; R06 84e845f14dbf; R07 fa2f9a2b5a3e; R08 5e6319b1af57; R09 5ce6af10d7a7; R10 3f0dc3adc2d3; R11 6861575e95c3; R12 3130f345537b; R13 864c89c10e1d; R14 2aa92d78987f; R15 825d909e2437`. These are **blob content hashes**, not repository commit SHAs or claims of independent test execution. Fetch upstream full commits and dependency lockfiles before reproduction.

**Open:** None of the 15 projects was independently built/retested in our runtime during this audit; claims are classified according to documented source evidence and explicit caveats.
