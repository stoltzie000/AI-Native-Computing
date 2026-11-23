# Reversible concept decision ledger — 2026-11-23

**Disposition definitions:** ADOPT = use an existing capability as an evaluation component; ADAPT = modify/reuse elements after license/verification; TEST = falsifiable experiment not yet selected; HOLD = defer because evidence, compatibility or rights missing; REJECT = disproven *mechanism under stated conditions*; DUPLICATE = independently solved in existing work, so avoid rebuilding it; INSUFFICIENT EVIDENCE = cannot yet rank. Codes are **research recommendations**, not a completed chip architecture selection. Primary refs and code/provenance: [matrix](PRIOR_ART_MATRIX.md).

Evidence A independently replicated physical; B reported fabricated-device measurements; C FPGA/emulation; D RTL/synthesis; E modeling; F assertion. All physical superiority comparisons still need identical workload/quality/power boundaries. No candidate is permanently removed from history.

## Mechanism-level ledger (C01–C15 from handoff)

| ID | Mechanism / disposition | Evidence and confidence | Critical falsifier / failure mode | Revisit condition & next test |
|---|---|---|---|---|
| C01 | **TEST** model-in-silicon / fixed weights | B (Taalas fabricated), D/E (OpenTallas), **medium** | Model updates, changing precision, chip area, accuracy and re-fabrication; source contains no independent matched Rubin comparison | Revisit as *selectively immutable* expert/embedding modules after measured workload stability and layout density |
| C02 | **TEST** 3D DRAM + compute | E (ATLAS/DeepStack), B on existing memory stacks but not proposed complete accelerator, **medium** | DRAM timing, bonding parasitics, thermal hotspot, yield | Revisit on bounded microarchitecture with thermal simulation calibrated to measured parts and manufacturable package |
| C03 | **TEST** processing in memory (PIM) | E NeuPIMs; B for PCM analog arrays on other workloads, **medium** | Refresh, limited operations, ADC/DAC, address/memory coherence, analog noise and power | Measure complete data-movement+conversion energy and quality on comparable workload, not array TOPS alone |
| C04 | **HOLD 48GB SRAM-only die; TEST bounded local SRAM** | E our v0.2 area bound; B NorthPole evidence for locality, **high** | 12GB-per-node SRAM area exceeds ordinary reticle under cited density, fanout/routing and overflow | Revisit *multi-die* or much smaller distributed SRAM after physical placement and thermal feasibility |
| C05 | **ADAPT** spatial/dataflow / mesh | C openTPU and Tenstorrent systems; E our v0.4/0.5 equal-resource mesh, **high** | Collective latency, congestion, underutilization; our equal-resource 8-node mesh lost to centralized proxy | Revisit mesh only with mapped traffic and measured end-to-end > best shared/2-package alternative |
| C06 | **TEST** new board/backplane/chiplets | B physical co-packaged optics, E our links, **medium** | Package vs motherboard signaling conflation, PHY lane and energy budget, topology/routing | Prototype differential link/channel loss and packet latency, include retimers, connectors and cooling |
| C07 | **TEST** low-bit/ternary/mixed precision | B current commercial hardware, but no quality-matched new representation measured here, **medium** | Task quality, outlier compensation, scaling and accumulation precision | Compare trained model at same quality and total energy, not just bits/weight or TOPS |
| C08 | **REJECT natural exact-zero weight blocks as primary mechanism for two measured models; TEST trained structured sparsity** | **Direct checkpoint data** in our project, high within two models | 0/874,624 and 0/296,960 exact zero eligible 2D weight elements, thus no 4x4/8x8 all-zero blocks | Reconsider after intentionally structured-sparse **trained** model preserves task quality and saves actual burst traffic; never generalize negative sample to all models |
| C09 | **TEST** event-driven/neuromorphic | B Intel Loihi 2; medium | Conversion overhead and ANN/SNN model quality gap | Choose temporal sensor/robotics task where true event rate is low; compare end-to-end to CPU/GPU |
| C10 | **TEST** photonic matrix compute | B fabricated optical tensor chip on MNIST/CIFAR; medium | Accuracy, nonlinear handling, ADC/DAC/laser and calibration power | Require full electrical-to-electrical task energy with calibration and quality-matched digital baseline |
| C11 | **TEST** alternative sequence models (Mamba/diffusion) | B real GPU software, no dedicated new silicon, **high** research value | State update dependency, diffusion iterative passes, memory and quality differences | Evaluate matched end-task quality + sequence length and *whole-system* latency/energy; build operator trace |
| C12 | **ADAPT** AI-guided co-design tournament | C/D R11 and D/E R12 methodology, **high** | Reward hacking, seed cherry-picking, correctness failures, source mutation | Pre-register immutable evaluation harness, multiple seeds, hold-out workload, reproducible P&R |
| C13 | **INSUFFICIENT EVIDENCE** non-token representations | F broad idea unless a formal encoding and decoder are defined, **high** | Different semantics/quality obscure comparison; label change alone no speedup | Define reversible codec or task-equivalent native representation and prove measured useful-work advantage |
| C14 | **HOLD** asynchronous/clockless interconnect | B event-based Loihi proof but no generic high-bandwidth link result, **medium** | Handshake overhead, worst-case latency, timing/debug/testing, physical variability | Chiplet-scale prototype with measured joules/bit, latency distribution and error rate |
| C15 | **ADOPT measurement; ADAPT** AI-specific OS/runtime | B Tenstorrent software and deployed GPUs, **high** | Scheduler overhead may be negligible vs bulk compute; replacing OS cannot eliminate compute bounds | Profile end-to-end scheduler/copy costs; implement only if measurable opportunity exceeds complexity |

**Conditions for rejection are scoped.** C08 rejecting natural zero-weight blocks for two models does not reject compression, pruning, or all sparse architectures. C04 rejects an ordinary-single-die 48GB SRAM interpretation, not multi-die SRAM architectures. C05 rejects *one assumed equal-resource configuration*, not every possible mesh.

## Per-project decision and reversal trigger (R01–R15)

| Project | Decision | Why / reuse | What would reverse or qualify the decision |
|---|---|---|---|
| R01 openTPU | ADAPT | Real FPGA integrated toolchain available; quality/energy matched GPU win unshown | Replicate frozen FPGA bitstream/inputs; measure wall-power and correctness; change to ADOPT specific module if tests hold |
| R02 OpenTallas | TEST | Rich mask-ROM and ABI studies, but no product silicon | Promote specific ROM/ABI only after independently reproducing RTL and target-node macro/area; HOLD if geometry invalid |
| R03 OpenTaalas | TEST | Published LLaMA RTL co-sim, no verified chip | Repeat 8B cosimulation, quantify full weights/ROM integration and actual process area; reject claimed chip if impossible |
| R04 APEX | ADAPT | FPGA bit-exact methodology, transparent failures; narrow measured path | Adopt golden-model/test harness after verified coverage and dependency/license audit; revise model-wide claims if FPGA differs |
| R05 Gemmini | ADOPT baseline | Mature configurable alternative, already solves basic systolic+scratchpad generator | Deprioritize as final architecture when independently demonstrated novel compute exceeds it fairly |
| R06 Chipyard | ADOPT infrastructure | Integrates simulation/FPGA/EDA workflows | Replace with leaner toolchain if integration cost dominates experiments and equivalent gates are retained |
| R07 NVDLA | HOLD | Legacy RTL excellent reference, special license | Use isolated reference knowledge or licensed components after legal review and workload relevance shown |
| R08 DeepStack | TEST | 3D memory explorations; proprietary opaque .so weakens inspectability | Adopt transparently auditable submodel only; replace binary model if no calibration/code access |
| R09 ATLAS | ADAPT | Thermal + performance simulation desirable | Replace with calibrated physical evidence or alternative if unvalidated anonymized assumptions dominate result |
| R10 NeuPIMs | TEST | Useful simulated NPU+PIM partition; no clear repo reuse permission | Independent reproduce, obtain license terms, compare same compute/memory budget; change to ADAPT after verification |
| R11 auto-arch-tournament | ADAPT | Multi-seed FPGA fitness and correctness gate | Modify to AI task/quality/energy and immutable guardrails; abandon automated optimization if hold-out regressions |
| R12 SparseCraft | ADAPT methods / HOLD code | Reported RTL traffic/cycles, modeled energy, no verified root license | Independent repeat Pareto/accuracy; get permission before code inclusion; require meter for energy claims |
| R13 tt-metal | ADAPT | Valuable kernel/runtime on actual Tenstorrent hardware, not open processor RTL | Compare same fused kernels/shape on equivalent hardware; restrict hardware reproduction assumptions |
| R14 Mamba | TEST | Hardware-aware SSM changes memory scaling | Quality-matched long-context vs transformer; check training and selective scan throughput/memory; choose hybrid if wins |
| R15 LLaDA | TEST | Real non-autoregressive generation route | Compare effective quality vs diffusion step count, memory and complete time; code/model licensing review |

## New mechanism concepts (links to expanded register)
- **C16** activation-aware exact-zero prefetch: TEST; our v0.8–v1.0 HDL works but real model activation zero rate unmeasured.
- **C17** trained low-rank/state-compressed operators: TEST; quality/energy must be matched.
- **C18** heterogeneous fixed-weight + programmable compute modules: TEST; avoids all-or-nothing model-in-silicon lock-in.
- **C19** on-chip memory-aware multi-level scheduling/coalescing: ADAPT from tested v1.0 and existing accelerators, needs real cache/burst controller.
- **C20** hybrid attention + state-space runtime/processor: TEST with task equivalence.
- **C21** on-package optical I/O for multi-module board: TEST only if electrical link power/latency is dominant.
- **C22** PCM/analog memory tiles with adaptive digital error correction: TEST physical and quality model.
- **C23** task-quality-constrained per-layer precision: TEST; account for all calibration overhead.
- **C24** model/compiler/processor multiobjective tournament with immutable tests: ADAPT method, not automatic superiority.
- **C25** dynamic execution subgraph selection with correctness certificates: TEST; traffic/count benefit must survive scheduling.

## Scientific bookkeeping template
For each experiment, retain:
`ID; hypothesis; upstream source+commit+license; design state & configuration; control baseline; model/accuracy floor; workload; code and dataset SHA; clock; batch/context; physical power boundary; samples; measured CI/test logs; uncertainty; rejection criterion; changed assumption; new status; reconsideration trigger`.

No existing repository source was copied or merged during this research audit. Conclusions do **not** authorize destructive project changes, commercial code reuse, fabrication or license acceptance.
