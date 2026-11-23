# AI-Native Computing — Researcher assessment (2026-11-23)

**Prepared against:** the user's AI-Native Processor Researcher Handoff dated 2026-11-23. This research addresses all 15 R## projects and 15 C## concepts, extends the scope with physical evidence and 13 new concepts, and recommends falsifiable experiments. It **does not select a final processor** or claim physical superiority. All earlier design and negative-result history remains authoritative.

## Delivered research artifacts
1. [Prior-art matrix](PRIOR_ART_MATRIX.md): R01–R15 reviewed from their current GitHub READMEs/licenses, plus X01–X09 physical/alternative technologies. Evidence tiers, implementation and limitations, dispositions, licensing flags, links and README Git blob SHAs.
2. [Reversible decision ledger](CONCEPT_DECISION_LEDGER.md): all C01–C15 classified with reasons/falsifiers/reversal conditions; every R01–R15 has a reconsideration trigger.
   - [Evidence completeness and missing performance metrics](PERFORMANCE_EVIDENCE_AND_GAPS.md): explicitly distinguishes published measured throughput, memory, latency, energy, output quality, scaling and unavailable matched comparisons for each candidate.
3. [Expanded mechanism register](NEW_CONCEPT_REGISTER.md): C16–C28 ranked with overlaps, hypotheses, likely failure modes and experiment.
4. [Quality-matched GPU and physical benchmark protocol](BENCHMARK_AND_PROOF_PROTOCOL.md): model/task matrix, matched baselines, measurements, correctness, power boundaries, uncertainty and claims standard.
5. [Prioritized experimental roadmap and risk register](EXPERIMENTAL_ROADMAP_AND_RISK_REGISTER.md): specific gates with stop criteria, system-level physical challenges and 14 critical risks.

## Final recommendations (research recommendations, no architecture lock)

| Recommendation | Decision | Why |
|---|---|---|
| **Gemmini + Chipyard** | **ADOPT** as open research controls and implementation/toolchain where feasible | Existing proven generator/simulator infrastructure removes basic duplication and gives independent reference |
| **openTPU and APEX methods** | **ADAPT** | Real FPGA and bit-exact reference workflows create a more credible path to physical hardware than repeating toy RTL |
| **ATLAS thermal co-simulation + available DeepStack concepts** | **ADAPT/TEST** with strict licensing and calibration | Our previous models did not physically close package/thermal/per-link assumptions; opaque binaries require caution |
| **Automated architecture tournament** | **ADAPT** under frozen correctness, multiple seeds and immutable quality/power controls | Efficient exploratory research, not autonomous evidence-free claims |
| **Real-model activation zero audit** | **TEST FIRST** | Current v0.8–v1.0 direction relies on exact-zero activation behavior **never measured** on actual model inference |
| **Mamba/SSM, diffusion and hybrid model/processor co-design** | **TEST** | May alter fundamental memory/state/sequential bottlenecks, not just rearrange existing GPU operations |
| **Partial model-specific fixed silicon, near-memory compute and digital/analog tile hybrids** | **TEST** after successful physical sanity bounds | Taalas, NorthPole and IBM PCM show such classes can be fabricated, but tradeoffs differ |
| **Natural unpruned exact-zero weight-block acceleration in the two audited TinyStories models** | **REJECT for those samples** | SHA-verified checkpoints had zero eligible exact-zero 4x4/8x8 blocks. Reconsider with *trained structured sparsity and quality verification*, not wishful toy matrices |
| **Assume an 8-node mesh wins solely on more HBM4** | **REJECT under previous equal-resource simulation** | Rubin-class GPU published peak bandwidth is already similar; our own equal-resource mesh estimate lost to central memory proxy |
| **Copy NVDLA code, DeepStack binaries, or no-license projects immediately** | **HOLD** | Special/restricted/unverified terms; must audit before incorporating code into project |

## Priority experiment sequence

**(1) Measure actual intermediate activation zeros on pinned trained models → (2) reproduce a complete external AI accelerator baseline (Gemmini/openTPU/APEX) → (3) compare same-resource memory/controller/compute scheduling, including a dense negative control → (4) physical FPGA side-by-side and power measurements → (5) qualified package, memory and board feasibility → (6) fabricate only if real, repeatable head-to-head superiority becomes plausible.** In parallel test at least one non-attention/hybrid AI model path and retain all failed designs.

## What "superior" means
Do not optimize nominal TOK/s or TOPS alone. Report quality-matched successful task completions per second and wall-plug joules per correct task, including preprocessing, memory, routing and system overhead. Hardware rankings are **workload- and evidence-specific**. A physically measured win in one task does not establish universal superiority.

## Research limitations
- Upstream source **reviewed, not independently rebuilt**. GitHub README blob hashes in matrix record exact material seen.
- Physical published results are first-party or academic measurements unless specifically stated; no tier-A independent hardware replication claimed.
- Restricted licenses must be reviewed separately. No source code was imported from external projects and no licenses accepted.
- No actual model inference or FPGA physical experiment was run as part of **this prior-art audit**. The main project's previously verified results remain in [PROJECT_STATE.md](../../PROJECT_STATE.md).
- All research is placed on an isolated branch for review. **No replacement of canonical project state and no merge into main are implied by research publication.**

### Primary evidence anchors
[openTPU](https://github.com/FeSens/openTPU) · [APEX](https://github.com/SigmanticAI/apex-inference-chip) · [Gemmini](https://github.com/ucb-bar/gemmini) · [Chipyard](https://github.com/ucb-bar/chipyard) · [DeepStack](https://github.com/tile-ai/DeepStack) · [ATLAS](https://github.com/pku-gsun/ATLAS-MICRO-2026) · [NorthPole](https://research.ibm.com/publications/neural-inference-at-the-frontier-of-energy-space-and-time) · [Taalas](https://taalas.com/products/) · [IBM PCM](https://www.nature.com/articles/s41467-025-63794-4) · [Cerebras SEC filing](https://www.sec.gov/Archives/edgar/data/2021728/000162828026029503/cerebras-sx1amay2026.htm) · [Loihi 2](https://www.intel.com/content/www/us/en/newsroom/news/intel-builds-worlds-largest-neuromorphic-system.html) · [2026 photonic tensor study](https://www.nature.com/articles/s41467-026-71599-2) · [NeuPIMs paper](https://arxiv.org/abs/2403.00579) · [Tri-Stack-PIM preprint](https://arxiv.org/abs/2611.13644) · [NVIDIA Rubin specifications](https://www.nvidia.com/en-us/data-center/hgx/).
