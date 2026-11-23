# Simulator v0.4 — bounded topology, routing and collectives

**Date:** 2026-11-23. **Status:** E1 scheduling/constraint experiment, NOT a chip, EDA flow, measured GPU benchmark, PCB layout, physical model or proof of superiority.

## What is implemented

* Directed, full-duplex per-link calendar scheduler; store-and-forward multi-hop routing and a link bandwidth budget allocated consistently across physical ring, mesh, star, and full topologies.
* Real module-port-count rejection, shortest-path routing, per-hop and injection service assumptions, optional shared star-switch serialization.
* Two collective patterns: ring reduce-scatter/all-gather *traffic pattern*, and recursive-doubling *traffic pattern*; each has explicit stage barriers and link contention.
* Per-hop wire-byte accounting, per-node logical injection volume, port/wire/bandwidth budget checks, and optional **assumed** link-energy accounting (no default physical energy claim).
* CPU mathematical correctness reference for recursive doubling, checked against independent serial reductions.
* Integration with unchanged v0.3 compute+memory model: compute v0.3 with effectively zero collective service, then add the physically routed serial collectives. This remains an approximation; there is no concurrent distributed kernel execution.
* Published Micron HBM4 one-stack **bandwidth/capacity as a reference envelope** (36 GB per stack, >2.8 TB/s nominal); v0.4 assumes eight such stacks plus *hypothetical* 70% sustained memory rate and hypothetical compute modules.

## Execute locally

From the repository root, with Python 3.11 or newer, standard library only:

```bash
python -m unittest discover -s simulator_v0_3 -p 'test_*.py' -v
python -m unittest discover -s simulator_v0_4 -p 'test_*.py' -v
python simulator_v0_4/run_experiments.py > simulator_v0_4/results/summary.json
```

The v0.4 test suite passes **24/24 tests** in the isolated execution environment, and previous v0.3 passes **43/43**. The JSON report is deterministic and committed with the exact code that generated it. GitHub CI is configured separately; remote execution results are not represented as already completed.

## Experiment interpretation

The example constrains every topology to the same total physical link capacity of 1,024 GB/s (sum of undirected full-duplex links counted once); any individual link has an *assumed* 128 GB/s nominal directional ceiling. A synthetic 85% payload efficiency and 120 ns/hop are *inputs*, not independently verified PHY metrics. Eight compute nodes each have at most four ports. A full mesh needs seven ports and is rejected; a hypothetical eight-port variant is modeled but not claimed physically realizable.

At context 32768, 8-node HBM4 proxy, batch 1, output rates are conditional scheduling results:

| Topology and collective | Conditional output steps/s |
|---|---:|
| Ring + ring traffic | 468.43 |
| 2×4 mesh + ring traffic | 467.28 |
| 2×4 mesh + recursive doubling | 507.99 |
| Switched star + recursive doubling | 395.88 |
| Full mesh + recursive doubling with 4-port cap | REJECT_PORTS |
| Full mesh + recursive doubling with hypothetical 8 ports | 510.57 |

The ~0.5% gain of the seven-port full mesh over the three-port 2×4 mesh under these assumed conditions is not evidence that more routing wires are worth the cost, packaging or power. Replacing on-package link assumptions with slower, board-like *hypothetical* inputs decreases mesh + recursive-doubling to ~317 or ~186 calculated steps/s. No real PCB link was characterized.

**Interpretation limitation:** An eight-node fabric is NOT compared fairly with one MI355X or RTX 5090 for overall performance or efficiency. These results are not matched for power, silicon area, system cost, generation of HBM, total compute, task accuracy, or inference software. A system with eight published HBM4 stacks inherently has an enormous memory-bandwidth advantage over an older single-GPU reference irrespective of novel processing hardware.

## Non-negotiable next work

1. Fabricate/electrically verify (or obtain lab measurements of) candidate chiplet/package/board links, or keep timing ranges as assumptions.
2. Assess interposer/organic substrate, differential pair lane count, retimers and reach; UCIe data rates are for package links, NOT proof of motherboard wiring.
3. Independently benchmark equivalently configured modern single and multi-GPU systems; compare matched task quality and energy per successful task.
4. Extend to measured memory transaction traces, power delivery/thermal budgets, longer context/batches and workloads other than autoregressive decode.
5. Improve the dataflow and model co-design: reducing collective count/bytes and weight state traffic may outperform adding raw link bandwidth.

Read [`docs/TOPOLOGY_REVIEW.md`](docs/TOPOLOGY_REVIEW.md) for failure analysis, [`docs/PHYSICAL_BOUNDARIES.md`](docs/PHYSICAL_BOUNDARIES.md) for physical assumptions, and [`results/summary.json`](results/summary.json) for all scenario details. The project scope remains a new full-system AI-native computer, not merely a PCIe GPU replacement.
