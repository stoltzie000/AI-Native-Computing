# AI-Native-Computing
Research and development of a next-generation AI-native computing architecture, including purpose-built processors, memory systems, motherboard design, interconnects, and software, engineered from first principles to outperform conventional GPU-based AI computing.

## Engineering status (2026-11-23)

The first reproducible research simulator is available at [simulator_v0_2](simulator_v0_2/README.md). It models fast/bulk memory traffic, KV-cache movement, compute ceilings, capacity, multi-node fabric overhead, and a simple physical SRAM area limit. An isolated local run passed **21/21 tests**. A GitHub Actions regression workflow is configured but its execution status is not yet confirmed.

**No superior physical AI processor has been demonstrated.** The optimistic SRAM-based candidate requires wafer-scale or multi-chiplet integration and real electrical/thermal verification. Simulated scenario throughput must not be interpreted as measured hardware performance.

See [product definition](docs/PRODUCT_DEFINITION.md), [validation protocol](docs/VALIDATION_PLAN.md), [project state](PROJECT_STATE.md), and [physical feasibility screen](simulator_v0_2/docs/PHYSICAL_FEASIBILITY_SCREEN.md).
