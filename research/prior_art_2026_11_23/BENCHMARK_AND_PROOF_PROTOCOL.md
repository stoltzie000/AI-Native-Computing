# Pre-registered benchmark and proof protocol — 2026-11-23

**Status:** Proposed experiment specification, **not completed GPU testing**. Intended for our candidate systems, strong contemporary GPUs and specialized accelerators. Never substitute vendor peak bandwidth, TOPS, “token/s” marketing or generic synthesis cells for these measurements.

## 1. Fair baseline inventory
- **Current high-end GPU:** NVIDIA Rubin GPU if *actually accessible*, model/software version pinned; [published peak](https://www.nvidia.com/en-us/data-center/hgx/) 288GB HBM4/22TB/s is only a specification. If unavailable, benchmark the latest actual hardware accessible and label the missing Rubin comparison as **OPEN**.
- **Independent competitor GPU:** [AMD MI355X](https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html) with published 288GB HBM3E/8TB/s; use ROCm optimized inference, same model/quality.
- **Established accessible control:** optimized NVIDIA H200/B200/RTX system, with exact SKU, memory, kernels and power logged; do not pretend old cards are the state of the art.
- **Special-purpose non-GPU controls:** [Google TPU7x](https://docs.cloud.google.com/docs/compute-area/tpus), [Tenstorrent](https://github.com/tenstorrent/tt-metal), [Cerebras](https://www.cerebras.ai/) where service access allows fair measurements. Do not mix third-party estimates into measured result tables.

Compare **1 device vs 1 device**, **same node power budget**, **same total memory capacity**, and **equal-system-scale** variants separately. Do not give our 8-node design credit for simply having eight times more memory/compute.

## 2. Workload suite — at least four materially different tasks

| Workload | Representative experiment | Required correctness/quality evidence | Main measurements |
|---|---|---|---|
| W1 dense language inference | Frozen small (0.5–1B), medium (~7–8B), large (30B-class) *trained* models; contexts 512/4096/32768 if supported, batches 1/8/32 | Model weights+tokenizer SHA; exact same model first, per-answer quality suite, numerical/logit comparison with declared format | Prefill separate from decode; TTFT, per-output latency p50/p95, tokens/s/user and aggregate, host/device energy |
| W2 long context and stateful | Retrieval and reasoning questions including attention/SSM, varying prompt length | Same source facts, answer scoring rubric and confidence intervals | Entire time-to-correct-answer, memory/state reads, model load and accuracy |
| W3 dense/sparse vision or embeddings | ResNet50 or comparable real task plus a block-sparse control | Exact tensors for DSP correctness, published dataset or labeled set, top-1/top-5 or recall | Samples/s, joules/correct-sample, bandwidth/caches, burst utilization |
| W4 event/temporal or multimodal | Audio/sensor or event detection, one alternative architecture | Identical sensor stream, comparable task accuracy/F1, latency bound | Event/sequence latency, energy/task, idle power, conversion I/O |
| W5 optional training/update | Fine-tuning or adapter-update workload | Converged validation quality and total training steps/data | Total energy to quality, throughput, update cost and final model size |

**SSM/diffusion/non-token models:** compare *completed tasks at equivalent quality*. Do NOT compare raw generated tokens/sec to diffusion iterations/sec. Show both model-training resources and inferential time where training differs materially. Report how answer length, samples and algorithmic steps are defined.

## 3. Accuracy and numerical contract
- Freeze datasets, prompts, tokenizer, model checkpoint hash, compiler, precision, batch, cache policies and random seeds **before** performance collection.
- For exact signed integer kernel substitution, the result must be bit-exact (modulo explicitly documented accumulator wrap).
- For FP/analog/low-bit algorithms, establish **non-inferiority margin in advance** (e.g. within 1 percentage point on each accuracy metric if statistically defensible), and enforce minimum quality per task class. Never conceal degradation in one task with average gain elsewhere.
- Human/LLM judging needs blinded/randomized scoring, judge/version controls and disagreement reporting; do not allow candidate architecture to optimize on the held-out test suite.
- Measure hallucination/long-context regressions for novel model representations.

## 4. Performance and energy measurement
- Use at least **30 steady-state trials per configuration** as a starting rule; increase if the 95% bootstrap confidence interval remains wide. Run multiple seeds and randomize run order. Log every run and excluded samples with reasons.
- Separate cold boot / model load, warmed prefill, decode, concurrency, queueing, full end-user task and p95/p99 tails. Start/end timing boundaries must include all required preprocessing and output transfer.
- Measure **wall-plug joules per *correct/accepted* task** and peak/steady watts, plus chip/device numbers only if instrumented. Document meter accuracy/sample period; include PSU, host, storage, interconnect and optional cooling as named boundary layers.
- Include idle energy, memory refresh, DRAM/HBM activity, on-package/between-board bytes and optical driver/laser energy if relevant.
- Report power/die temp/clocks, throttling, target process, area, packaging and resource utilization; no numeric throughput without configuration details.
- Baseline GPU kernels must be tuned (appropriate graph compilation, batching, quantization and sparse kernels available to that GPU). Same accuracy floor and training-format budget applies on each platform.
- Always include a **dense negative control** and a synthetic sparse positive control when testing zero-gating. The synthetic positive control is never evidence for actual pretrained-model behavior.

## 5. Statistical and claims rules
1. Report raw dataset, measurement harness revision/commit, aggregate mean/median and 95% CI. Where possible, use paired repeated sampling under controlled order.
2. Primary criteria: *time to accepted useful result*, *wall energy per accepted result*, and application quality. Also report capacity, tail latency, sustained throughput and engineering reliability separately.
3. Declare in advance whether claiming lower latency, better energy efficiency, or Pareto improvement. Example **provisional** pass gate: >20% improvement in at least one primary metric with 95% confidence and no statistically meaningful decline in another, task quality non-inferior. This numeric threshold is a **proposed decision gate**, not observed improvement.
4. One narrow workload win permits a **narrow workload claim only**. "General AI-native computer outperforms GPUs" requires wins across multiple independent representative workload families, acceptable flexibility and repeatable physical-system results.
5. A claim of silicon superiority requires physically measured hardware, not a simulator, RTL cycle count, generic Yosys cells, or pre-layout/ideal PDK result.
6. Archive failed designs, benchmark logs, tool versions, assumptions and exact reversal conditions.

## 6. Immediate correctness/traffic experiment for current v1.0
- Hardware under study: our `prototype_v1_0`, 64-row buffer; 2- and 4-lane PE, **only RTL generic synthesis presently verified**. It has **registers, not SRAM macro**, one outstanding request, and no actual HBM controller.
- Compare its transaction scheduling against openTPU/Gemmini-style buffered controls on identical operations.
- Collect real activation exact-zero fractions via **read-only pinned model inference** (MicroT TinyStories attention and MicroMixer attention-free; later an actual 7B model) with at least 100 representative inputs of varied lengths, and per-layer/column raw and post-quantization distributions. Record whether zero values arise from ReLU/gating or quantization. Do not infer activity zeros from zero-weight audit.
- Calculate *actual burst* traffic under a selected physically available memory controller, not merely logical 4B vs 64B packet counts.
- If real exact-zero fraction is insufficient to offset dispatcher/memory latency versus optimized dense model, **stop prioritizing activation gating** rather than inventing 74% sparsity.
- First actual FPGA trial should include one existing systolic + scratchpad baseline and use measured core clock, board-level joules, controller stalls, and host transfers. A v1.0 win without the rest of the AI computation is only a tile-level win.

## 7. Reproduction record required for every accepted result

`run_id, UTC datetime, commit SHA, build+tool version, model checkpoint+hash, dataset+hash, task rubric, algorithm/precision, full hardware SKU and memory, runner OS, batch/concurrency, input/output lengths, device and host utilization, clock/temperature, measured input & transfer bytes, prefill/decode/total latency, whole system energy, idle watts, actual accuracy, confidence interval, anomalies/retries, baseline comparison`.

**No benchmark execution is claimed in this document.**
