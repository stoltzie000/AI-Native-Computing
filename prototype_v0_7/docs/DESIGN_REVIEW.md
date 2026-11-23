# v0.7 review — evidence, correctness, and falsification

## Differences from v0.6
1. Latched complete weight+activation inputs prevent external-bus changes from corrupting an in-flight tile.
2. Parameterized signed multiply lanes perform 1/2/4/8/16 products each active cycle; all terms destined for one row are aggregated before the row register's one nonblocking update.
3. Ready/busy/done handshake rejects spurious start requests while busy; asynchronous reset clears partial results.
4. An independent CPU numerical reference tests negative values, 16-bit accumulation wraparound and nonzero-block certificate constraints.
5. Verilog benches include 256 randomized v0.6 transactions, and 128+ deterministic randomized v0.7 cases for each of 10 parameter combinations, plus reset, input capture, and handshake cases.

## Verification gates
| Level | Required evidence | Status |
|---|---|---|
| Python reference arithmetic | Unit tests and matching Git blob | 6/6 PASSED locally |
| Existing model regressions | Previous source isolated tests | 169/169 PASSED locally |
| Verilog compile/RTL numerical tests | Completed Icarus run log | OPEN; workflow configured |
| Generic RTL synthesis | Completed Yosys log | OPEN; workflow configured |
| Formal equivalence and overflow properties | Bounded and/or mathematical proof | OPEN |
| FPGA silicon timing/power | Instrumented real device measurements | OPEN |
| Trained-model task correctness and sparsity | Model weights and quality metrics | OPEN |
| Quality-matched GPU comparison | Measured full system benchmark | OPEN |

## Critical engineering limitations
- **Cycle count does not determine speed.** Increasing LANES can lengthen the combinational critical path, multiply area, and increase energy.
- This PE has a duplicated flat register array and no realistic compressed-weight or memory-interface logic. The cost of moving and decoding blocks may dominate.
- Zero skipping is exact only for genuinely zero blocks. Unverified model sparsity cannot be treated as available workload performance.
- Yosys generic synthesis without standard-cell characterization does not establish maximum clock, energy, die area or packaging feasibility.
- A functional 4x4 INT8 kernel is not an AI-native motherboard or a proof of greater intelligence per joule than GPUs.

## Next experiments after verified HDL
1. Inspect actual Icarus/Yosys failures, fix RTL on this branch, and rerun before merge.
2. Measure area/cell-count and estimated critical paths for each lane count using a documented cell library.
3. Build a verifiable compressed block index + memory arbiter, quantify metadata and bank conflicts.
4. Measure trained-model 4x4/8x8 exact-zero-block rates and compare task quality at identical model versions.
5. Maintain alternative algorithm families (low-rank, recurrent, state-space, novel representations) and only select a processor architecture after fair, physical performance evidence.
