# AI-Native-Computing — PROJECT_STATE
Last updated: 2026-11-23

## Current phase
Project baseline established; first-principles architecture research and experiment design. No competitive processor has yet been demonstrated.

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
