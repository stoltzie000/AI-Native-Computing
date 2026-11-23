# v0.5 architecture decision and falsification ledger

## F6 — Treat eight HBM4 stacks as a novel GPU-beating system
**REJECTED.** NVIDIA published individual Rubin GPU 288GB HBM4 and 22 TB/s. Our eight 36GB HBM4 stack 22.4 TB/s aggregate *peak sum* is in the same specification class, not an original advantage. Comparing the new HBM4 memory to a previous HBM3E GPU inflated the perceived benefit.

## F7 — Give eight packages versus one a fair, same-resource screening
**Completed at E1.** 8 packages x 1 stack: 507.99 conditional outputs/s. Idealized single memory domain with eight identical stacks: 569.70. A two-domain option: 557.74. All use eight 36GB/2.8TB/s HBM4 stacks, 70% hypothetical sustained, 1600 synthetic TOPS, same 32K-context workload and same 4-bit weights/16-bit KV.

**Decision:** The 8-package mesh does NOT win this experiment. Its collectives are overhead. No real single-module shared memory controller or thermal solution has been demonstrated. These are upper-bound sensitivity comparisons; an actual GPU benchmark has not been measured.

## F8 — Can central eight-stack package practically dissipate heat?
**Unknown; rejected under one illustrative screen.** With a hypothetical 2200 W compute total, eight HBM x 20 W, and maximum 1400 W *per package*, one package would dissipate at least 2360 W before PHY/regulator losses. Two x four-stack packages dissipate at least 1180 W each and survive that **chosen** screen if PHY heat is assumed zero. Zero PHY power is not physically correct; the partial heat total and thermal ceiling were chosen to falsify, not prove, a package.

## F9 — Can naive reduced weight precision double the memory-bound speed?
**Possibly in bytes, not validated in AI.** At 32K context the assumed 4-bit weight traffic 17.875 GB and KV-step traffic 8.590 GB leave a fixed KV overhead. 2-bit weight storage gives ~1.51× improvement in total bytes, and 1-bit weights ~2.03×, if metadata ratios and KV format remain unchanged. No actual 1-bit version of the same model with preserved accuracy has been demonstrated.

## F10 — Can exact zero-block skipping avoid otherwise unnecessary computation?
**Toy CPU proof passed.** A constructed 16×16 FP32 matrix with 3/4 8×8 blocks exactly zero is represented in 261B instead of 1,024B (including toy index and bitmask). Output equals independent dense math.fsum oracle, and randomized tests pass. This establishes that an architecture could exploit *real structural zeros* losslessly. It does not establish useful structural sparsity in existing AI models, representational training compatibility, or physical implementation of metadata decoding.

## F11 — Will board-level links perform like on-package interconnects?
**UNKNOWN: no bridge permitted.** UCIe 4.0 adds package memory-link improvements. No evidence that the same transfer/energy/latency can operate across board traces or connectors. Illustrative 64 Gbit/s raw-lane scenario requires 20 lanes each direction to carry 128 GB/s of useful payload after assumed loss, on each of ten links in a 2×4 mesh. Fabric, PHY, trace, ground, PDN, and thermal constraints remain unmeasured.

## Selection status
No architecture is accepted as a real design. The 2-package 4-HBM-stack-per-package concept is the *least-bad thermal-sensitive architecture hypothesis under one deliberately artificial 1400 W/package limit*. New first-principles research should prioritize physically achievable **data traffic and compute reduction** at equivalent AI capability, with power and package verification. GPU-comparable measurements and silicon demonstration still absent.
