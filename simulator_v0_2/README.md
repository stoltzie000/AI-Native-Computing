# AI-Native Computing — Architecture Screening MVP v0.2

**Status: E1 analytical screening only. No AI processor, motherboard, FPGA, or complete system has been built or shown superior to a GPU.**

The objective is a complete first-principles AI-native computer: new processor, custom motherboard/backplane, memory hierarchy, chip-to-chip communication, power/cooling, and software/model methods if advantageous. Token generation is only one diagnostic workload; productive AI capability is the eventual metric.

## What v0.2 implements

- Correctly accounts for the **K/V cache traffic** on every decode step, not just resident K/V capacity.
- Enforces resident model weight, KV cache and scratch capacity at both fast and bulk memory tiers.
- Distinguishes GB (1e9 bytes) and GiB (2^30 bytes), weight quantization metadata and KV precision.
- Supports model weights and KV cache distributed across bulk/off-chip memory and fast/on-chip SRAM, module count, fabric bandwidth, message latency, and simple data-parallel batch reuse.
- Calculates approximate weight+attention ops, fast/bulk memory movement, a naive parallel roofline, and an explicit serialized fabric overhead proxy.
- Includes a generic work-unit calculation independent of transformers or tokens.
- Keeps every unverified compute/efficiency/power parameter explicit; unknown power yields no fabricated energy efficiency.
- Audits 17 unit tests and stress-tests speculative SRAM bandwidth and residency.

## Run (Python 3.10+, standard library)

```bash
cd simulator_v0_2
python -m unittest discover -p 'test_model.py' -v
python run_experiments.py > results/summary.json
```

## Baselines and unit conventions

| Reference | Peak bulk bandwidth | Capacity | Evidence |
|---|---:|---:|---|
| RTX 5090 | 1,792 GB/s | 32 GB | NVIDIA spec |
| H200 | 4,800 GB/s | 141 GB | NVIDIA spec |
| MI355X | 8,000 GB/s | 288 GB | AMD spec |

All modeled compute ceilings (including the reference GPUs' **100 TOPS**), bandwidth/compute utilization, memory/attention overlap, fabric topology and scheduling are artificial comparison assumptions. **No observed tokens/sec are used.** Thus every reported result is a **conditional, optimistic scenario calculation**, NOT an actual throughput benchmark nor a universal upper bound on optimized implementations.

Reference proxy: 32.5B parameters, 4-bit weights + 10% estimated metadata, 16-bit KV cache, Qwen2.5-32B-Instruct architecture (64 layers, 40 attention heads, 8 KV heads, hidden size 5,120; head dimension 128). At context 32,768 and batch 1 the KV footprint is 8 GiB. Weight storage including metadata is 17.875 decimal GB. Both values are independently tested. The 32.5B parameter count is approximate; metadata/scratch are explicit engineering scenarios, not measured model allocations.

## Candidate system topologies (all unverified)

1. **Distributed near-memory board:** eight modules each holding local compute and 16 GB bulk memory, connected through a custom fabric. Bottleneck: aggregate memory reads and collective synchronization.
2. **Distributed SRAM-centric board:** four hypothetical 12 GB fast-memory modules, on-module processing, fabric connected to a control/host board. Weight and KV state fully resident in on-chip fast memory **only by assumption**. Biggest risks: SRAM physical area, fabrication/packaging, actual bandwidth, power and partitioning. It is NOT verified feasible.
3. **16-node PIM proxy board:** a research placeholder that models bulk-memory bandwidth, NOT actual PIM internal logic or energy behavior. Must be replaced with PIM-aware access tracing before credible comparison.

The motherboard/backplane is a **design variable**: no PCIe or conventional CPU/GPU board layout is required. Current interconnect is a serialized all-reduce-like proxy, not a tested network implementation.

## Initial results and falsification

See `results/summary.json` and `docs/DECISION_LEDGER.md`. At 32k context the hypothetical four-node SRAM scenario outputs ~1,036 token/s under assumed peak limits versus ~302 token/s for MI355X under similarly optimistic assumptions; **this is not a physical demonstration**. A 25% drop in on-chip residency/bandwidth reduces the candidate sharply, and 25% SRAM residence does not fit the hypothesized bulk capacity. That means the design is fragile and presently **fails readiness for hardware construction**.

These diagnostic token rates do not establish quality or practical speed across other AI systems. Full proof requires implementation-specific silicon area, reliable power data, functional RTL and physical memory/interconnect measurements, model quality parity, and real GPU systems tested under matched software/workloads.

## Known limitations (explicit)

- Not cycle-accurate; no circuit, electrical, timing closure, thermal, compiler or gate-level model.
- Assumes full memory-channel parallelism, perfect partitioning and data reuse, and a very simplified collective fabric cost; the resulting time may be optimistic or pessimistic in individual subsystems.
- Does not simulate power, dynamic traffic, congestion, faults, row locality, bank conflicts or PIM computation.
- GPU on-chip caches, specific formats/capabilities, actual kernels and scheduling are deliberately not modeled. Do **not** use this calculator to rank physical systems.
- Attention operations exclude softmax, normalization, routing and other overhead.
- Batching and decoding are architectural probes, not substitutes for measuring completed real-world AI tasks.
- Non-token task support is only a generic roofline stub; no algorithm/quality/accuracy tests yet.

## Research sources

See `docs/SOURCES.md` for direct primary citations and checked facts.
