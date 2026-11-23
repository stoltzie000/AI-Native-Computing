# Decision and failure ledger — 2026-11-23

## A1: Reuse GPU peak bandwidth as a measured inference rate
**Rejected.** Bandwidth/weight is only a theoretical roofline. Ignoring KV traffic and system effects is misleading. GPU reference numbers in the report are **not real measured token rates**.

## A2: Eight-node near-memory bulk-memory fabric
**Not selected.** At 32k context, the example peaks at ~251 output tokens/s under assumed ideal resource ceilings, below the 8 TB/s MI355X reference scenario (~302). More modules/DDR channels do not automatically win. Must examine package cost, usable bandwidth, coherence, routing and physical power before revising.

## A3: Sixteen-node PIM proxy
**Unproven, not selected.** The proxy reaches ~402 output tokens/s under hypothetical 16 TB/s aggregate bandwidth versus the MI355X scenario at ~302, but this assumes every node provides 1 TB/s and does not model true PIM compute, energy, programming or data placement. No credible PIM advantage established.

## A4: Four-node SRAM-centric fabric
**Continue research with critical risks; not accepted as a real design.** Scenario: 4 modules x 12 GB SRAM, 8 TB/s fast-memory bandwidth per module, full weight+KV SRAM placement, 400 GB/s fabric and 1 µs per collective. E1 calc ~1,036 outputs/s vs the 302 reference scenario at 32k context. If fast residency drops to 75%, ~290 outputs/s; 50%, ~148; 25% placement is impossible with the assumed 4x4 GB bulk capacity. Halving SRAM bandwidth produces ~558 outputs/s. No verified die density, packaging, cooling, clocking, dataflow, energy, performance or manufacturability. **Do not declare victory.**

## Research pivot
Investigate **memory-on-package or wafer-scale state residence**, minimizing chip-to-chip synchronization while maintaining adequate usable capacity. Compare monolithic/wafer, chiplet SRAM/DRAM, and true near-memory/PIM alternatives. The promising 4-node model is an upper-bound *hypothesis* that likely overstates practical performance and must be physically stress tested.

## Next evidence gate
1. Integrate a measured Qwen2.5-32B baseline from appropriately tuned GPU systems (same quantization, batch, context, software revision, output quality). No measured baseline is currently available.
2. Estimate total die area/technology feasibility for 48 GB SRAM, I/O bandwidth, power, cooling and signal integrity using documented component data, not guesses.
3. Build a timed memory/interconnect transaction simulator; quantify bank conflicts, placement, network load, setup overhead and failure modes.
4. Reject or revise after each gate. Build RTL/FPGA sub-blocks only when model survives falsification.
