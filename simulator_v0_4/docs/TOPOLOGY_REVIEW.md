# Experiment review and falsification — v0.4

## Demonstrated in software

* A deterministic scheduler enforces point-to-point link calendars, with two direction-specific resources for full-duplex channels, and serial store/forward hops.
* Ring allreduce communication has 2(n-1) stages, each node injecting tensor_size/n per stage. Recursive doubling has log2(n) stages for powers of two, each node injecting the full vector per stage.
* The recursive-doubling numerical kernel on the CPU returns the same result as independent serial reduction in the tests. Timing model **does not execute this arithmetic**.
* Port count and global PHY-count-weighted bandwidth budget are explicitly tested; independently calculated two-node closed-form timing cases pass.
* The 8-node mesh is 2x4. During initial tests the mesh was mistakenly encoded as a 4x2 grid, causing two failures; the geometry and assertions were corrected before acceptance. The tests prove this specific edge mapping, not a manufacturable floorplan.

## Failure analysis

1. **Four-port full mesh:** rejected. Requires seven compute PHY ports. Eight-port relaxation gains ~0.5% modeled 32K output throughput over 2x4 mesh + recursive doubling, under identical total nominal wire capacity. No actual die-edge area/power is measured.
2. **Central star switch:** ~396 conditional 32K output steps/s vs mesh ~508; a single shared-switch schedule adds congestion. This model assumes the switch core bandwidth is 384 GB/s; real switch silicon is not designed or validated.
3. **Ring communication on 2x4 mesh:** ~467 conditional output steps/s. Choosing a collective better aligned to latency-sensitive small activation reductions matters more than topology alone.
4. **Board-link sensitivity:** At 32GB/s nominal per link, 70% payload efficiency, 1us/hop and 0.5us injection latency, the 2x4 mesh + recursive doubling slows to ~317 conditional steps/s. With 16GB/s, 65% efficiency, 3us/hop, 1us injection, it falls to ~186. These are deliberately chosen *hypothetical* stress inputs, not claims about boards currently available.
5. **Eight HBM4 modules:** This is an assembly hypothesis with 8x36GB reference memory; the supplied 70% sustained bandwidth and 200 TOPS compute are not established, and no model quality/accuracy benchmark is included.
6. **One-generation upgrade confound:** using HBM4 while comparing with a GPU using HBM3E could create gains unrelated to a novel compute architecture. A same-generation, matched-memory experiment is mandatory.

## Research decision

The **2×4 memory-compute mesh with recursive doubling** is a candidate for **additional physically bounded investigation**, not a finalized motherboard or processor. Alternative monolithic, near-memory, PIM, wafer-scale, non-transformer, and hierarchical architectures remain active. No E2 cycle-accurate model, E3 physical prototype or E4 benchmark exists.

## Next falsifiable experiment

Build a memory-and-link *power/thermal/area* budget with measured or cited fabrication data. Compare identical memory stack counts and memory-generation baselines, allowing different compute/network topologies but no free additional hardware. Separate package-level and backplane-level fabrics; include host power and cooling. Identify whether the new architecture has any *intrinsic* improvement beyond adding more HBM4 capacity. If not, reject that architecture and test a different compute-memory paradigm.
