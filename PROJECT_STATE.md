# AI-Native-Computing — PROJECT_STATE
Last updated: 2026-11-23

## Current phase
E1 transaction/dependency modeling and CPU functional dataflow proof-of-concept complete (v0.3); calibration, real hardware, E2+ and competitive validation pending. No competitive processor has yet been demonstrated.

## Decisions
- Design a complete AI-native computer, not merely a GPU replacement card.
- Processor, memory, motherboard/backplane, interconnect, power, cooling and software may all change.
- Challenge established assumptions, including token-centric execution and transformer-only workloads.
- Optimize real AI capability, task performance and efficiency; profitability is not a primary objective.
- Compare with strong GPU and purpose-built accelerator baselines using reproducible, fair measurements.
- Redesign failing candidates; archive negative results rather than claiming success.

## Verified progress
- Existing GitHub repository: stoltzie000/AI-Native-Computing, main branch.
- GitHub repository is public as of this checkpoint.
- Initial GitHub README pre-existed and was preserved.
- Previous local analytical prototype v0.1 exists and its four elementary unit tests passed in the assistant's isolated runtime on 2026-11-23. It is a simplified 30B low-bit inference roofline calculation, NOT a validated processor or GPU benchmark.

## Known shortcomings of previous v0.1
- Counts an assumed KV-cache capacity but does not model KV read traffic in its decode throughput estimate.
- Does not enforce physical memory capacity in evaluate().
- Uses assumed utilization, electrical power and cost; none are physical measurements.
- Tests confirm only arithmetic identities; no calibrated simulator or benchmark is available.
- Focuses on a PCIe-connected LLM accelerator and is superseded as product scope by full-system co-design.

## Current project artifacts
- docs/PRODUCT_DEFINITION.md — requirements and system scope.
- docs/VALIDATION_PLAN.md — evidence standards, benchmarking, iteration gates.
- Previous analytical prototype is historical evidence, not proof of superiority.

## Immediate next work
1. Establish reproducible reference workloads and optimized contemporary GPU baselines.
2. Create independent, audited architecture models with explicit capacity and movement accounting.
3. Explore multiple candidate topologies (including custom motherboard and memory) and document tradeoffs.
4. Implement testable simulator and use failure analysis to revise candidates.
5. Prototype physical subsystems only after modeling evidence merits it.

## Open constraints / unknowns
Real-world GPU measurements, candidate manufacturing technology, lab instruments, funding/resources, and physical benchmark data are not established. Do not invent them.

## Task-sequence continuity
No new executable Codex/GPT task number is assigned here. Before issuing a numbered handoff, reconcile the last task number in the active workflow; do not silently restart numbering.

## Safety / repository handling
Preserve existing work and uncommitted changes. Inspect repository state before future changes; do not overwrite, reset, wipe, or reconfigure repository visibility without approval.

## 2026-11-23 checkpoint — analytical simulator v0.2
**Status:** Implemented and independently executable in isolated Python 3 environment. All 17 unit tests passed. Source files and deterministic JSON output committed to `simulator_v0_2/`, then re-fetched from GitHub and verified with exact Git blob SHA against local artifacts (8/8 exact matches). The initial README and archived v0.1 were preserved. No user's local PC or hardware was modified.

### Model improvements
- Capacity validation includes compressed weights + metadata, KV resident state and scratch.
- KV cache reads and writes contribute to long-context decode traffic.
- Fast/bulk memory tiers, module count, simplified fabric bandwidth/latency, dense-operation lower bounds, generic work-unit roofline, optional assumed power with unknown energy otherwise.
- Explicit arithmetic assumptions, falsification and capacity failures.
- Sources: `simulator_v0_2/docs/SOURCES.md`. Decision/failure log: `simulator_v0_2/docs/DECISION_LEDGER.md`.

### Conditional scenario outcomes (Qwen2.5-32B proxy, 4-bit weights, context=32768, batch=1)
All rates are optimistic **analytical scenarios**, NOT measured GPU or new-processor results.
- RTX 5090 memory-spec proxy: 67.7 output units/s
- H200 memory-spec proxy: 181.4
- MI355X memory-spec proxy: 302.3
- Proposed 8-node near-memory: 251.4
- Proposed 16-node PIM *proxy*: 401.5 (not a physical PIM model)
- Proposed 4-node 48GB SRAM concept: 1036.4, assumes total 32 TB/s SRAM, full weight+KV residence, unrealistic unverified component parameters
- SRAM scenario at only 75% fast residency: 290.2; at 50%: 148.1. At 25%: REJECT_CAPACITY. Sensitivity falsifies robust superiority.

### Decision
G0 partially completed: published model/GPU memory specifications verified, no measured optimized GPU workload yet. E1 analytical model implemented, tests passed. **No physical design proven, no reproducible hardware advantage claimed.** SRAM-centric route remains a high-risk hypothesis; no architecture selected for hardware.

### Next work
1. Measure or retrieve appropriately matched GPU benchmark traces and quantify kernel efficiency.
2. Separate true SRAM physical area, yield, thermal, I/O, fabric and power viability from hypothetical numbers.
3. Build an event/transaction-level memory/fabric simulator with at least one independent reference implementation.
4. Compare non-transformer and task-quality-matched AI workloads; explore monolithic, on-package, optical/analog/PIM where justified.
5. Iterate/reject on failure. Only then consider RTL/FPGA and hardware experiments.

### Task sequencing
No Codex/GPT executable task number assigned by this checkpoint; number continuity remains unresolved.

## 2026-11-23 checkpoint — v0.2.1 physical feasibility correction
Physical feasibility check added to `simulator_v0_2/physical_limits.py`, `test_physical_limits.py`, and `docs/PHYSICAL_FEASIBILITY_SCREEN.md`. Current local suite: **21/21 unit tests passed**. The five changed/new files were re-fetched from GitHub and matched their local Git blob SHA exactly (5/5). Prior v0.2 result estimates retained as **unmeasured**, conditional arithmetic tests.

**Evidence:** TSMC published high-density SRAM macro density 38.1 Mb/mm². A 12 GB SRAM store needs >= 2,520 mm² of SRAM macro at that density, or ~2.94 conventional 858 mm² reticle footprints **without compute/routing/PHY overhead**. Four such stores need >= 10,079 mm² aggregate. Therefore the interpretation “one 12 GB SRAM node equals one ordinary reticle-size silicon die” is **rejected**. Candidate must be reworked as stitched-wafer or multi-chiplet logical modules with realistic interconnect, thermal and energy costs. No revised physically validated design is available.

**Gate status:** E1 calculations validated for selected assumptions; G0 benchmarking incomplete; G1 capacity constraints modeled, real physical feasibility remains OPEN; G2-G5 NOT PASSED. No physical superiority claim.

**Next implementation priority:** event-level trace simulator with attention/weight transfers, bank-level routing/latency and topology; examine wafer-scale/stacked/hybrid alternatives with physical data and compare to measured optimized GPU benchmarks. Preserve failed architectures and hypotheses.

## 2026-11-23 checkpoint — v0.3 transaction/dependency simulator and functional reference
**Completed/verified:** `simulator_v0_3/` was built in an isolated Python 3.13 runtime with only the standard library. **43/43 automated tests passed**, including independent single-tile closed-form timing reference, storage/traffic conservation, GQA head-layout rejection, bandwidth/interconnect/bank stress tests, and a randomized CPU-only sharded matrix-vector + ring-all-reduce functional demonstration. Deterministic JSON results reproduced byte-identically. All 11 simulator project files were individually created on GitHub, fetched back, and verified by exact matching Git blob SHA to the tested local files. Existing README, archived v0.1 and v0.2.1 were preserved.

**Results (32K context, batch 1; all E1 conditional calculations, no measured throughput):**
- RTX 5090 peak-memory proxy: 66.736 output steps/s.
- H200 peak-memory proxy: 174.5358.
- MI355X peak-memory proxy: 283.7645.
- 4-node hypothetical HBM fabric: 433.1111.
- 8-node hypothetical HBM fabric: 460.7876.
- 8-node hybrid HBM+small SRAM hypothetical: 448.7078.
- 4-node 48GB wafer/multi-die SRAM hypothesis: 814.4617; **not a validated physically realizable node**.
- 8-node hot-bank stress case: 45.546 (fails comparator).
- 8-node HBM with 40% useful bulk bandwidth: 240.6689 (fails uncalibrated MI355X proxy).
- 8-node HBM with fabric latency increased to 20 microseconds: 110.1055 (fails comparator).
- 16-node head-sharding case: rejected by this simulator's strict divisibility constraint, not necessarily impossible hardware.
- Toy 8×12 matrix-vector across 4 nodes: zero absolute error vs independent serial reference, 24 logical ring messages; not a full neural network.

**Decision:** Prioritize the 8-module HBM fabric as the next **falsifiable research candidate**, not an accepted processor/motherboard design. Existing SRAM-only hypothesis remains high-risk. Small-SRAM hybrid did not win under current asymmetric HBM assumptions, so redo with controlled equal bulk HBM settings. The report's baseline GPU rates are synthetic service-time calculations based on vendor memory-peak specs, not optimized/measured GPU performance. No claim of superiority is warranted.

**Files:** `simulator_v0_3/{engine.py,scenarios.py,run_experiments.py,functional_microkernel.py,test_engine.py,test_microkernel.py,README.md}`; `simulator_v0_3/docs/{ARCHITECTURE_REVIEW.md,RESEARCH_SOURCES.md}`; `simulator_v0_3/results/{summary.json,test_run.txt}`. New regression workflow: `.github/workflows/simulator-v0-3-tests.yml`; configured, its remote execution has NOT been verified.

**Next gate (pending):** implement per-link network topology and arbitration with finite issue queues, physically grounded memory/bank timings, power and area; obtain matched optimized GPU traces and a task-quality suite before any superiority comparison. Design and electrically test an initial prototype module only after its constraints survive falsification. No real motherboard, ASIC or FPGA has been built, ordered or modified.

**Task numbering:** No executable AI-assistant handoff task is assigned; do not silently reset task sequencing.

## 2026-11-23 checkpoint — v0.4 bounded topology, routing and collective simulation
**Work performed:** Added `simulator_v0_4/` with directed per-link scheduling, store-and-forward multi-hop routing, equal aggregate link-capacity budget across ring/mesh/star/full topologies, compute-module port-count checks, ring and recursive-doubling allreduce traffic patterns, sensitivity analysis, and CPU numerical reference for recursive doubling. The timing model is an E1 scheduling/constraint model, not cycle-accurate silicon or measured GPU data.

**Tests:** 24/24 new v0.4 tests pass in isolated Python 3.13; 43/43 prior v0.3 regression tests pass. Full JSON regenerated byte-identically. All 11 newly committed v0.4 project files re-fetched from GitHub and matched the local tested originals' exact Git blob SHA. GitHub Actions workflow `.github/workflows/simulator-v0-4-tests.yml` was created; remote execution NOT verified.

**Physical data:** Verified Micron published HBM4 36GB per stack and >2.8TB/s nominal bandwidth; UCIe 3.0 48/64GT/s refers to package-level chiplet interfaces; AMD MI355X published 288GB/8TB/s/TBP 1400W. These are SPECIFICATIONS, not matched AI benchmarks. In scenario 8 nodes each with 36GB HBM4, 2.8TB/s per node, **assumed** 70% sustained, hypothetical 200 TOPS/node, 128GB/s hypothetical per link, 1024GB/s total link budget, four max compute ports, synthetic latency and payload efficiency, the 32768-context 2x4 mesh + recursive doubling yields 507.99 *conditional* output steps/s. Ring + ring yields 468.43; switched star + recursive doubling yields 395.88. Full mesh requires seven ports/node and is rejected under the four-port constraint; changing to eight ports yields 510.57, only ~0.5% above mesh with the same aggregate link budget.

**Falsification:** With hypothetical 32GB/s board-like link inputs and 1us/hop, mesh + recursive doubling drops to 317.04 conditional steps/s; at 16GB/s and 3us/hop, 185.58. No actual PCB/PHY tested. The mesh choice is **not** finalized, and its performance gain could simply reflect using newer/more HBM, not a superior new processor.

**Functional evidence:** 8-node 17-element recursive-doubling CPU mathematical demonstration passed with maximum numerical difference 8.88e-16 relative to an independent math.fsum oracle, with 24 logical messages. This is not a full LLM, ASIC or clocked hardware implementation.

**Evidence gates:** E1 constrained analytical and transaction scheduling (partial) only. G0 matched optimized measured GPU baselines OPEN; G1 physical package/board/power/thermal/area OPEN; G2-G5 NOT PASSED. No new processor/motherboard/hardware performance demonstrated.

**Next mandatory engineering work:** (1) Obtain real GPU baseline measurements on comparable memory generation, task quality and whole-system power; (2) create physical package/board link/lane count, area, energy/thermal models grounded in verified data; (3) evaluate model/dataflow changes that reduce weight/state movement and collective count; (4) refine event model and experiment with verifiable FPGA or chiplet-level subsystems. Keep rejecting architectures that fail, including this mesh if evidence does not support it.

**Files:** `simulator_v0_4/README.md`, `network.py`, `functional_collectives.py`, `scenarios.py`, `run_experiments.py`, `test_network.py`, `test_functional_collectives.py`, `docs/PHYSICAL_BOUNDARIES.md`, `docs/TOPOLOGY_REVIEW.md`, `results/summary.json`, `results/test_run.txt`.

**Task-sequence continuity:** No new numbered executable assistant prompt was assigned. Existing task identifiers remain unchanged.

## 2026-11-23 checkpoint — v0.5 equal-resource falsification and exact sparse proof

**GitHub artifacts:** `simulator_v0_5/` contains 16 files (model, constraints, thermal/lane checks, sparse functional CPU proof, tests, documentation, deterministic JSON result). Every new file was re-fetched from GitHub and verified against its locally tested original by the exact Git blob SHA (16/16). Earlier v0.1-v0.4 retained. `.github/workflows/simulator-v0-5-tests.yml` configured, but remote execution NOT verified. ZIP contains v0.2-v0.5 dependencies and passed clean-extraction testing.

**Tests:** v0.2 21 + v0.3 43 + v0.4 24 + v0.5 70 = **158 passing local tests** on isolated Python 3.13; v0.5 deterministic report regenerated byte-identically after ZIP extraction. Tests establish arithmetic and small CPU-kernel correctness ONLY.

**Critical new external evidence:** NVIDIA's 2026 HGX Rubin specifications publish **288 GB HBM4 and 22 TB/s** peak memory bandwidth per Rubin GPU. This directly undermines the premise that our earlier eight-HBM4 288GB/22.4TB/s concept establishes an original memory advantage. Prior GPU-generation comparison is CONFONDED and superseded, not erased. UCIe 4.0 consortium documentation describes on-package memory connectivity; it does not establish viable motherboard-level electrical links.

**Equalized E1 experiment:** Same eight 36GB HBM4 stacks (288GB), same *nominal aggregate* 22.4TB/s, same hypothetical 70% sustained, 1600 synthetic TOPS, same Qwen2.5-32B 4-bit/16-bit-KV proxy and 32K context for 1/2/4/8 compute packages. Rates calculated: **1 package 569.70**, 2 packages **557.74**, 4 **546.27**, 8-mesh **507.99** *hypothetical output steps/s*. The mesh is about 10.8% slower than single-domain in this controlled scheduler, due to communication, absent unmodeled central bottlenecks. The single-domain device is not an actual GPU/ASIC. With severe hypothetical board links the eight-module result falls to **193.57**.

**Conditional physical gate:** Under illustrative assumptions 2200W aggregate compute + eight stacks at 20W each and 1400W per-package heat cap, one compute package is rejected (2360W partial heat), and two x four-stack packages are fastest among those not rejected (1180W/package before PHY/regulators). Actual power, heat flux, package floorplan, HBM controller, power-delivery and cooling remain UNKNOWN. An assumed 64 Gbit/s raw lane with 98% encoding and 85% payload efficiency needs 20 one-way lanes (40 full duplex) per 128 GB/s link; a 2x4 mesh with 10 links requires 400 directional lanes. This is a lane-count *hypothesis*, NOT UCIe 64 GT/s evidence or measured PHY.

**Algorithmic opportunity and counterexample:** At 32K, proxy weight bytes **17.875GB** and KV-step bytes **8.590GB**; a 2x traffic reduction with KV unchanged and equal bandwidth requires eliminating **at least 74.03%** of weight traffic. A CPU-only toy 16x16 FP32 matrix with 75% EXACT zero 8x8 blocks was represented in 261B instead of 1024B (74.51% savings with metadata); dense vs sparse outputs matched exactly for that example, and randomized tests passed. This does NOT establish 75% block sparsity, performance gain, or unchanged quality in actual AI models. 1-bit weight-storage sensitivity yields a calculated 2.03x byte-rate improvement vs 4-bit at this context, but model-quality equivalence is UNKNOWN.

**Decision:** Reject selecting the eight-module HBM4 mesh as a proven advantage. Retain centralized and 2-package memory-compute hypotheses as unresolved, physically constrained options. Prioritize architecture-level reduction of necessary compute/data movement and scientifically validated AI-task capability; keep non-transformer and non-token representations in scope. **No superior new processor, motherboard, RTL/FPGA prototype, electrical measurements or real GPU throughput measurements exist.**

**Next gates:** verify matched optimized and measured Rubin/other GPU AI task baselines; measure truly trained model's real block-sparsity plus task-quality; estimate complete HBM-controller/package thermal power with electrical/floorplan evidence; prototype one small hardware compute+memory block, validate timing/energy against independently reproduced numerical oracle. No manufacturing or PC changes authorized by this checkpoint.

**Task continuity:** No numbered external AI task was issued here. Preserve the previously unresolved last task number; do not reset or fabricate numbering.

## 2026-11-23 checkpoint — v0.6 block-sparse RTL candidate

**Goal unchanged:** Original AI-native full system, including processor, memory, motherboard, cooling and potentially non-transformer/non-token algorithms; measurable superiority to strong GPU systems on quality-matched AI tasks. No performance superiority established.

**Source work:** Added `prototype_v0_6/` with a small sequential 4×4 signed INT8×INT8→INT32 block-sparse PE, start/done handshake, correct-by-contract skip of externally certified all-zero blocks, cycle and multiply counters, three RTL testbench examples, Python reference model, randomized and adversarial unit tests, verification caveats and reference test log. All seven source/docs/results files uploaded to GitHub and re-fetched with exact Git blob SHA match against locally verified files (7/7).

**Test evidence:** Python reference passed **11/11 tests** in isolated runtime. Earlier v0.2–v0.5 passed **158/158**, so total **169/169 Python tests** passed across five project iterations in clean-extraction ZIP. v0.5 deterministic output also matched byte-for-byte. RTL source/testbench has been AUTHORED but **not compiled or simulated locally**: Icarus Verilog, Verilator and Yosys are absent from the available runtime. `.github/workflows/sparse-rtl-tests.yml` was created to install Icarus Verilog, compile and run the HDL; **no successful remote workflow run was verified**. No FPGA synthesis, waveform proof, silicon or electrical measurements exist.

**Limitations:** The default PE is intentionally serial (16 multiplications in 16 active cycles per 4×4 block), not high-throughput production hardware. The upstream `block_valid` metadata must be true for correct skip; invalid metadata creates incorrect results. No HBM/SRAM controller, compressed-block index stream, network, voltage/area/power layout, advanced arithmetic, model-quality test or GPU comparison. No user computer modifications, hardware purchases or tapeout performed.

**Next engineering gate:** Obtain verified RTL compilation and numeric testbench success; add randomized RTL-vs-independent-oracle tests and reset/overflow/parametric cases. Only then attempt synthesis and memory/metadata datapath scaling, using real trained-model sparsity and quality data. Physically validate package and PHY requirements before claiming chip speed/efficiency.

**External task numbering:** No numbered executable AI prompt issued; previous continuity remains unresolved.

## 2026-11-23 checkpoint — v0.7 actual RTL compilation, simulation and generic synthesis

**Development location:** draft PR #1, branch `research/rtl-v07-verification`; main branch unchanged until reviewed/merged. Source, testbenches and numerical reference committed and individually fetched back from GitHub. Historical v0.6 RTL preserved.

**Verified first failure:** GitHub Actions run 45236851823 failed compiling historical v0.6: `cell` is a Verilog/SystemVerilog reserved configuration keyword. Saved a verification-only compatible copy renaming this identifier to `cell_index`. The v0.7 new module also uses `cell_index`. See `prototype_v0_7/results/VERIFICATION_2026-11-23.md`.

**Verified success:** GitHub Actions run 45237630207, job 137913469477, completed successfully. Actual Icarus Verilog compiled and executed 256 legacy differential test cases plus 1320 v0.7 cases over five LANES settings × two accumulator widths. Python 11 v0.6 and 13 v0.7 reference/synthetic-safetensors tests passed. Historical prior v0.2–v0.6 Python suite 169/169 passed on clean ZIP extraction. Current combined Python total 182/182. Yosys generic synthesis succeeded for default v0.7 and reported 7636 generic logic cells. None of these numbers is a physical-chip or GPU benchmark.

**New architecture experiment:** The v0.7 PE latches a tile at acceptance (unlike v0.6) and parameterizes the multiplier lanes; registered row partial accumulation avoids lost same-row updates. It still lacks memory controller, interconnect, compressed indices, physical timing, power measurement, actual trained-model evaluation and a custom motherboard.

**Weight audit:** Read-only standard Safetensors/NumPy utility committed, with 7 synthetic fixture unit tests (the 13 v0.7 Python tests comprise 6 arithmetic + 7 audit). Tracks actual binary zero elements, exact zero block rates, negative floating-point zero, edge exclusions and weighted tensor aggregates. Pretrained MicroMixer checkpoint found with published hash but download attempt FAILED. **No real trained model block-sparsity measured.**

**Competitive reality:** Literature on SparseGPT (post-training unstructured pruning), TEAL (activation sparsity and accelerated GPU kernels), and preliminary RoShift (RTX 5090 activation sparsity) means exact zero-block skipping is neither guaranteed available nor automatically novel. See `prototype_v0_7/docs/ALGORITHM_COMPARISON.md`. Alternative processor and model architectures remain in scope.

**Pending gates:** Generic cell-count LANES/ACC_W sweep running under Actions; record results only after success. Obtain trained model + quality-matched baseline; synthesize physical FPGA on identifiable device; measure real full-system energy/latency. G0/G1/G4/G5 hardware superiority gates remain OPEN. No physical processor/motherboard was manufactured or modified.

**External task numbering:** No numbered Codex or GPT handoff issued. Do not reset sequence without retrieving previous identifier.

## 2026-11-23 checkpoint — v0.7.1 generic synthesis parameter sweep

**Verified:** GitHub Actions run 45237901548 job 137914422602 succeeded, re-running RTL correctness and synthesizing all LANES=1/2/4/8/16 crossed with ACC_W=16/32 using one uniform Yosys generic flow. Results: `prototype_v0_7/results/SYNTHESIS_SWEEP_2026-11-23.md`.

**ACC_W 32 generic cells by LANES:** 2996, 4606, 7679, 14041, 25315. **ACC_W 16:** 2187, 3150, 4809, 8343, 14437. Active compute cycles: 16,8,4,2,1; full controller cycles including acceptance and completion: 18,10,6,4,3.

**Design decision:** Deprioritize full 16-lane unrolling pending technology-mapped frequency/power; prioritize 2- and 4-lane modules for a first measured FPGA implementation. The 32-bit generic-cells × controller-cycles proxy is 46060 (2 lanes) vs 46074 (4 lanes), versus 75945 (16 lanes). These are NOT mapped area, clock timings or energy measurements.

**Still open:** trained-model sparsity and task-quality experiments; actual FPGA/ASIC performance; physical memory/interconnect/board topology; competitive optimized GPU task performance; proof of superiority.

## 2026-11-23 checkpoint — v0.8 exact activation-gated weight-fetch RTL

**What was built:** `prototype_v0_8/rtl/activation_gated_pe.v`, independent hardware-memory-responder testbench `tb_activation_gated_pe.sv`, signed-integer reference `reference.py` plus randomized unit tests, `traffic_model.py` and sensitivity tests, README and decision ledger. The v0.8 candidate suppresses physical **RTL memory request handshakes** for exact-zero input activations, while checking dense-equivalent arithmetic outputs. One outstanding in-order weight request is supported, with stall handling; no burst memory PHY or actual SRAM/HBM controller is built. All new files were created on a separate branch `research/activation-gated-v08`; prior v0.1-v0.7 preserved. PR #2 remains in review.

**Verified CI evidence:** GitHub Actions run 45239447045/job 137919806911 completed success: Icarus compiled and executed 99 randomized/deterministic cases for each 16- and 32-bit accumulator (198 total); v0.8 Python arithmetic reference 7/7; Yosys default generic synthesis **2250** generic cells. A more recent GitHub Actions run 45239851986/job 137921237306 completed success: **14/14** Python tests (7 functional+7 traffic sensitivity), both 99-case RTL configurations PASS, generic synthesis 2250 cells. Counts are not measured silicon area, clock or watts.

**Quantitative limiting requirement:** Prior E1 Qwen2.5-32B 32K context proxy 17.875GB/step weight and 8.590GB/step KV traffic. Even with zero gating overhead and full bypass of suppressed weights, ideal twofold bandwidth-only benefit requires **74.028% exact-zero input activations**. At a hypothetical 50% exact-zero fraction, theoretical limit is **1.51x** and at 75% **2.03x**, excluding other overhead. NO actual model activation-zero fraction was measured. Current controller serializes one weight request+response, making it likely slower than bulk-streamed/parallel PE in low-sparsity cases; architecture is not accepted as superior.

**Next:** replace one-weight request with coalesced/vectorized memory requests and multiple outstanding tagged transactions, validate with physically justified burst granularity and memory/PHY timing; audit genuine trained model activation zero distributions and quality; compare to optimized dense/sparse GPU kernels with complete-system power. Do not claim general AI performance superiority or motherboard implementation.

**Task continuity:** No numbered Codex/GPT handoff assigned; retain previous numbering.

## 2026-11-23 checkpoint — v0.9 column-major coalesced demand fetch

**Purpose:** Replace v0.8's single-weight request traffic with a column-major memory layout that fetches all row weights of an active input column in one logical memory request; exact-zero activations skip the entire column and its MAC operations.

**Verified GitHub Actions:** Run 45240716833 job 137924272265 succeeded: independent Python oracle 8/8, Icarus 132 signed/stall/reset/handshake cases per 16- and 32-bit accumulation (264 RTL cases), Yosys generic synthesis 5370 cells (not mapped physical PPA). Run 45241154124 job 137925835100 succeeded after adding burst-tiling model: **15/15 Python tests**, same 264 RTL cases passed, 5370 generic cells. Earlier v0.8 remains intact. Branch `research/column-gated-v09`, PR #3 created, original main preserved until merge.

**Falsifiable memory result:** In 4x4 INT8 with two active columns, v0.8 emits eight single-weight requests and v0.9 emits two 4-weight column requests; the number of useful weight bytes is equal. Coalescing does not inherently improve actual off-chip bandwidth utilization: with hypothetical 64B physical transactions, a logical 4B column request wastes 60B.

**Fixed-workload scale-up sensitivity:** For a fixed 64-row × 4-column matrix, two active columns, 4 MAC lanes, hypothetical 64B minimum transfer and 200-cycle first-byte latency, a 4-row tile makes 32 column requests/2048B physical for 128B useful (6.25% utilization); a 64-row tile makes 2 requests/128B physical (100% *conditional* utilization). Idealized overlapped resource cycle estimates 6576 vs 426 respectively, but pipelined model is **not implemented in v0.9 RTL**, assumptions are not real HBM measurements, and no GPU comparison exists.

**Decision:** Pursue a 64-row column tile staged in local SRAM with only 2–4 time-multiplexed MAC lanes and queued/burst-aware memory controller as next design hypothesis. Do not assume effective bursts, zero-activation sparsity, physical clocks or energy. Real AI task-quality and measured GPU baselines remain OPEN. Full chip, motherboard, physical power and silicon superiority remain NOT demonstrated.

**Evidence:** `prototype_v0_9/README.md`, `docs/VERIFICATION_AND_SELECTION.md`, `memory_tiling.py`, `reference.py`, RTL/testbench and 15 Python tests. Task numbering unchanged (no new executable AI task issued).

## 2026-11-23 checkpoint — real pretrained checkpoint audit falsifies weight-block assumption

**First real trained-model observation:** GitHub Actions run 45241981337/job 137928727818 completed SUCCESS. Two public TinyStories-trained Safetensors model checkpoints were fetched into isolated ephemeral CI runner storage and checked against the publisher's SHA256 (MicroMixer attention-free 1M: f2d97561d43a1588e2a6b44a0c71fdd0069d03dc7e169a17c3a5f0082c15186e; MicroT transformer 300K: 9bf0a9c2f84ef8e17a9cdabfec0ab566da526de099d3e928d96b359306b89224). The existing read-only auditor parsed 2D weight arrays without loading model code. All-zero eligible 4x4/8x8 block fractions were **0** in both. MicroMixer: 874624 eligible matrix elements, zero exact zero elements, 54272 eligible 4x4 blocks (0 zero), 13456 eligible 8x8 blocks (0 zero). MicroT: 296960 elements, zero exact zero elements, 18560 eligible 4x4 blocks (0 zero), 4640 eligible 8x8 blocks (0 zero). Verified model file bytes respectively 4022572 and 1193768. **These are actual trained checkpoint measurements, NOT simulations.**

**Decision:** REJECT unpruned natural 4x4/8x8 weight-block sparsity as the primary performance justification for v0.6/0.7 on these two model checkpoints. Prior 75%-exact-zero toy experiment remains true only for constructed data; don't generalize. Do NOT generalize zero-zero findings to all trained model weights or infer anything about activation sparsity. Results stored durably: `experiments/real_weight_audit/results/MEASURED_2026-11-23.json`; `RESEARCH_DECISION.md` and workflow. No model weights committed to GitHub.

**Current engineering path:** v0.7 and v0.8 and v0.9 RTL tests physically simulated by Icarus and generically synthesized with Yosys on GitHub runners. Latest v0.9 coalesced column-fetch PE and Python burst-model passed 264 RTL cases/15 Python tests and 5370 generic Yosys cells; only conditional memory utilization. Real-model activation zero fractions remain UNKNOWN. Next: instrument actual pinned model inference and compute true activation zeros; build burst-aware 64-row SRAM-buffered PE with 2–4 time-multiplexed lanes; select physical FPGA library, do timing/energy measurements; then compare to optimized GPU whole-system task outcomes.

**Hardware goal status:** no physical chip/motherboard/FPGA programmed, no measured silicon frequency/wall power, no real GPU quality-matched benchmark, no system shown superior. Stop promoting favorable E1 models as physical proof. Task number continuity unchanged.
