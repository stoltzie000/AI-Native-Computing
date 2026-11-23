# AI-Native-Computing simulator v0.3 — transaction/dependency model

**Status:** 2026-11-23. E1 deterministic experimental simulator, **not measured AI hardware, not RTL, not cycle-accurate, and not evidence of GPU superiority**. Continues (does not overwrite) the historical [v0.2 model](../simulator_v0_2/README.md).

## Demonstrated artifact

The simulator executes one analytical autoregressive decode step of a Qwen2.5-32B-Instruct-like dense transformer. It tracks:

- 64 sequential layers and four ordered phases per layer: QKV projection, attention KV read/write, attention output projection, and feed-forward network.
- Two tensor-parallel reductions per layer, with a simplified shared-fabric latency/bandwidth cost.
- Separately banked bulk and optional SRAM fast tiers, per-bank serialized transactions, configurable bank placement/contension, tile-level memory-to-compute readiness, independent processing modules.
- Full weight plus quantization-metadata capacity; KV-cache residency and reads/writes; GQA replication for supported head-sharded topologies; scratch memory.
- Explicit rejection of unrepresentable tensor-head layouts and capacity overcommit.
- Independent arithmetic oracle, capacity tests, traffic-conservation tests, monotonicity tests, bad-layout tests, deterministic report tests and stress conditions.
- Functional proof-of-concept: a column-sharded matrix-vector operation with an explicit synchronous ring reduce-scatter/all-gather, checked against serial numerical output. It is a **CPU software reference**, not a manufactured accelerator or full neural network.

The architecture examples use *published peak capacities and bandwidths* for GPUs, but are **not calibrated GPU implementations**. Their compute throughput, bank counts, utilized bandwidth, transfer latencies and service assumptions are invented experiment inputs unless explicitly marked otherwise.

## Commands (Python standard library only)

From repository root:

```sh
python -m unittest discover -s simulator_v0_3 -p 'test_*.py' -v
python simulator_v0_3/run_experiments.py > simulator_v0_3/results/summary.json
```

To verify deterministic report reproduction:

```sh
python simulator_v0_3/run_experiments.py | cmp - simulator_v0_3/results/summary.json
```

Tested with Python 3.13 in an isolated runtime. No laptop hardware, GPU, custom chips or physical memory devices were exercised.

## Important modeling limitations

1. **No model correctness or accuracy tests.** Equivalent task quality to alternative methods has not been established.
2. **No physical time/energy calibration.** Rates are conditional service-time calculations, not actual tokens/second. Wall energy and thermal limits cannot be estimated responsibly yet.
3. Single-stream, **decode-only** execution. No prefill, training, MoE, vision, speech, diffusion, graph computation, etc.; does not define universal AI performance.
4. Idealized homogeneous weight sharding and per-node compute; no real compiler, kernel implementation, cache line alignment, tensor decomposition, activation/bank address trace, physical HBM timing, row buffers or detailed DRAM/controller queueing.
5. Head-sharded TP only. The simulator rejects certain module counts (such as 16 for 40 query heads). This is a limitation of this mapping, **not proof the physical architecture is impossible**.
6. All transfer bytes are abstract decimal quantities (GB vs GiB explicitly distinguished). Collective is a simplified aggregate-bandwidth proxy, not a 2D-mesh, ring, dragonfly, optical or UCIe link model; serialization/coherence/fanout unspecified.
7. An optimistic memory-only SRAM area lower bound does not establish a buildable memory+compute die or sufficient memory bandwidth.
8. All results represent one chosen proxy model and parameterization. Architecture ranking may change completely when accurate compute, memory service, or networking models are introduced.

## Files

- `engine.py`: deterministic transaction/dependency engine and rejection cases.
- `scenarios.py`: three GPU memory-peak proxies, four research candidates, and one adversarial bank-layout case.
- `run_experiments.py`: batch of 2K/8K/32K context experiments, sensitivity cases, unsupported layout rejection.
- `test_engine.py`: arithmetic reference and engineering invariants.
- `functional_microkernel.py` and `test_microkernel.py`: distributed algebra demonstration and independent correctness checks.
- `results/summary.json`: reproducible conditional outputs; **not** hardware benchmark data.
- `docs/ARCHITECTURE_REVIEW.md`: decisions, failure tests, near-term co-design direction.
- `docs/RESEARCH_SOURCES.md`: traceable public citations and provenance.

## Engineering decision

The **eight-module HBM fabric is the highest-priority *next research hypothesis***, not an accepted design: it has an optimistic upper-bound advantage over the modeled single-device HBM reference, but it is highly sensitive to bandwidth utilization and fabric latency. A modest near-memory SRAM addition did not improve the nominal eight-module scenario because the scenario assumes slower bulk-HBM channels. Neither a real advantage nor total-system efficiency has been demonstrated.

Advance it by acquiring actual GPU and HBM traces, implementing per-link topology and controller queues, and proving achievable bandwidth, physical area, power delivery and cooling. See `docs/ARCHITECTURE_REVIEW.md`.
