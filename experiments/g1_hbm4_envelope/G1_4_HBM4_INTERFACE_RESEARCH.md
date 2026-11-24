# G1.4 — Physically bounded HBM4 interface feasibility (E1 analytical screen)

Date: 2026-11-24. **Not a physical validation, not a controller RTL design, not a GPU benchmark.**

## Source-backed component facts (not verified together in one system)

| Component | Published source | Supported fact | Boundary |
|---|---|---|---|
| Micron HBM4 12H | [Micron product](https://www.micron.com/products/memory/hbm/hbm4) | 36 GB per 12-high stack; 2048-wide data bus; pin speed greater than 11 Gb/s; >2.8 TB/s per stack nominal | Does not prove compatible board/controller, measured sustained bandwidth or total memory power |
| Rambus HBM4 controller IP | [Rambus brief](https://go.rambus.com/hbm4-controller-product-brief), [controller overview](https://www.rambus.com/interface-ip/hbm/hbm4-controller/) | Controller IP advertised up to 10 Gb/s/pin, 2048 data bits, up to 2.56 TB/s per attached HBM4 device | IP specification, not integrated proven controller+PHY+HBM silicon; 10Gb/s controller is slower than Micron's >11Gb/s stack capability |
| NVIDIA Rubin GPU | [NVIDIA Rubin architecture](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/), [HGX specs](https://www.nvidia.com/en-us/data-center/hgx/) | 288 GB HBM4 per GPU; up to 22 TB/s nominal | Not an independently measured workload-specific performance or energy result |

## Independent arithmetic and falsification

For a hypothetical assembly of **eight** Micron-size 36GB stacks, each hypothetically attached to one controller running at the Rambus **10Gb/s** published maximum interface rate:

- Nominal installed capacity: 8 × 36GB = **288GB** (decimal units adopted for arithmetic).
- Aggregate HBM **data** interface width: 8 × 2048 = **16,384 data bits** across the stack-local interfaces. These are NOT high-speed motherboard serial links or a verified routing/bump floorplan.
- Maximum raw controller data-interface bandwidth at chosen 10Gb/s rate: 8 × (2048 data bits × 10Gb/s ÷ 8 bits/byte) = **20.48 TB/s**. This is 93.09% of Rubin's published **22 TB/s nominal** single-GPU HBM4 capacity; it does not beat that memory specification.
- Existing project's explicitly hypothetical Qwen2.5-32B 4-bit/32K context, batch-one **per-step traffic proxy**: 17.875GB weight + 8.590GB KV = **26.465GB/step**. This is transferred bytes per modeled decode step, NOT validated physical resident KV size or experimentally verified workload traffic.
- Idealized bandwidth-only lower bound: 26.465GB ÷ 20,480GB/s = **1.292ms per step**, equivalent to **773.85 modeled steps/s maximum** only if 100% of nominal bytes could be delivered usefully and compute, PHY, QACT, runtime, fabric, conversion, refresh and queue overhead all cost zero.
- Assumed 70% useful utilization is **not measured**: 14.336TB/s, **541.69 modeled steps/s** upper ceiling under that assumption; no system hardware built. For the same **unmeasured** per-step bytes, Rubin's published nominal 22TB/s gives a **831.29 modeled memory-only steps/s** ceiling, NOT measured GPU tokens/s and not proof of efficiency.

The `envelope.py` standard-library-only E1 model rejects invalid geometry, fractions, negative traffic, impossible reported bandwidth, and a workload that exceeds *user-supplied* reserved-capacity constraints. **Non-rejection is not a feasibility pass.** If residency or headroom is unknown, it blocks capacity acceptance, and the physical gate remains OPEN regardless of an arithmetic result. `test_envelope.py` independently checks units, monotonicity, input validation, capacity rejection, and external-specification separation. GitHub Actions executes both source and tests.

## G1 acceptance barriers

Actual electrical/thermal feasibility is blocked until all items are evidenced:

1. A controller + PHY + chosen HBM4 stack and clocking/bit-error/specification combination, with validated physical interoperability and achieved bandwidth under representative access patterns.
2. On-package floorplan, HBM routing and DQ bump/PHY allocation, power-delivery impedance, mechanical and thermomechanical constraints. UCIe package-level links are not equivalent to motherboard/backplane PHYs.
3. A complete heat budget for HBM, controller, PHY, compute, regulators and cooling; package hotspots/heat flux, PVT/aging and fault/recovery behavior. An unspecified wattage must NOT be silently filled with zero.
4. Demonstrated effective capacity under workload allocations, fragmentation, metadata, code, KV/state and headroom. Memory traffic is **not** resident memory occupancy.
5. Independent wall-power and performance of a usable model/task with matched accuracy against appropriate optimized GPUs, documenting context/batch, memory generation, runtime revisions and uncertainty.
6. Sensitivity to burst utilization, controller arbitration, queuing, bank activity and actual achievable utilization. The 70% scenario is **ASSUMPTION**, never a measured result.

**Decision: TEST physical package/PHY feasibility. REJECT any claim that eight bare HBM4 stacks establish a new competitive processor.** Similar aggregate nominal memory figures already exist in Rubin. Continue testing algorithmic bytes/task reduction and custom dataflow, while preserving non-transformer/photonic/analog alternatives when evidence warrants.

This branch is intentionally independent from draft PR #11's tagged-burst RTL branch, to avoid merging unverified research. No source IP is copied, no physical purchases or fabrication authorized.
