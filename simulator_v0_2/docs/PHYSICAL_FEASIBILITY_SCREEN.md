# Physical feasibility screen v0.2.1 — SRAM-centric architecture

**Date:** 2026-11-23. **Evidence:** silicon-memory area lower bound (E1), no physical processor or detailed floorplan.

## Research evidence

- TSMC reports **38.1 Mbits/mm²** for a high-density SRAM macro at 2 nm, with **0.021 µm²** high-density bitcells. [TSMC memory research](https://research.tsmc.com/page/memory/4.html).
- A conventional lithography exposure field is approximately **26 × 33 mm = 858 mm²**. [JKU integrated circuits course](https://iic-jku.github.io/design-complex-ic/dcic.html). Reticle stitching, wafer-scale and multi-die packaging may exceed a single exposure-field footprint.
- An actual **wafer-scale** accelerator exists with **44 GB SRAM** on a **46,225 mm²** wafer: [Cerebras WSE-3 product disclosure](https://www.cerebras.ai/press-release/cerebras-announces-third-generation-wafer-scale-engine) and [Cerebras WSE-3T](https://www.cerebras.ai/chip). These are examples of physical possibilities, not proofs of this new design.

## Arithmetic screen (optimistic memory-only)

At reported macro density of 38.1 million bits/mm²:

\[
A_{SRAM} \geq \frac{C_{GB}\, 10^9\, 8}{38.1\,10^6}\;\mathrm{mm^2}
\]

| Desired SRAM | Minimum macro area | Equivalent 858 mm² reticle footprints |
|---|---:|---:|
| 12 GB per proposed module | 2,520 mm² | 2.94 |
| 48 GB across four modules | 10,079 mm² | 11.75 |

**These minima exclude** compute, communication network, peripherals, routing, test infrastructure, SRAM redundancy, power delivery, heatsinking, packaging, manufacturing yield, spare capacity, and runtime overhead. Actual required silicon or interposer/wafer area will be larger. These estimates inherit the 2 nm macro's demonstrated density, not a guaranteed manufacturing option for a proposed processor.

## Engineering consequence: reject single-die interpretation

A **single conventional reticle-sized die cannot hold 12 GB SRAM** at the cited 38.1 Mbits/mm² density. The earlier four-node SRAM design is **invalid if each node means one monolithic reticle-limited die**. That interpretation is rejected. Do not call that design manufacturable.

## Revised competing system options

1. **Multi-die SRAM module:** divide each logical node among several SRAM chiplets plus compute/interface chiplets; model extra cross-die links, latency, energy and package losses.
2. **Stitched wafer-scale memory-compute module:** exploit reticle stitching and distributed compute/memory; model wafer defects, redundant routing and large-scale cooling.
3. **Hybrid stacked-memory board:** reduce large SRAM requirement using near-compute stacked DRAM and a smaller SRAM working set; evaluate lower bandwidth and improved density tradeoff.

The present numeric simulator treats each 12 GB node as an **abstract logical module**, not a demonstrated single die. Its predicted speed remains contingent on unrealistic/unvalidated data movement assumptions.

## Required before selecting hardware architecture

Source test silicon/design-technology data for area/power; create physical memory-macro floorplans, map active and idle banks, estimate wiring and switching power, check real interconnect throughput, and replace abstract module assumptions with measurable technology components. Run negative sensitivity tests. Do not fabricate a motherboard before memory/compute placement and electrical constraints are independently plausible.
