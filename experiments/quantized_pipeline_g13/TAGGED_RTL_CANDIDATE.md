# G1.3 tagged-burst RTL validation — verified functional simulation

**RTL_RESULT:** GitHub Actions [run 45421279226](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45421279226), job 138541159856, SUCCESS on commit 5db3caf3501edf3dcbfdabb3df23efad9c19e74f. Actual Icarus log inspected. Existing 48 baseline byte-memory cases, 12 reset-abort stresses, 8 byte-wrapper consecutive jobs, and 6/6 tagged-burst Python reference tests also passed in this run.

## Tagged-burst contract and observed results
- Seven 64-byte tagged requests per 402-byte prequantized ISA fixture (64 q, 320 w, 8 activation offsets, ten weight offsets), final response has 18 useful bytes and 46 masked padding bytes.
- Four concurrent outstanding requests max; independent responder delivers responses out of issue order. All eight tagged RTL jobs passed across four fixture/seed suites, with 4–6 observed reordered response positions per job and no duplicate or lost transaction.
- Every job was bit-exact against the same five 48-bit pinned-upstream-derived integer results and drop count. Exactly 40 active computation cycles; each job took **70 Icarus simulation cycles under this synthetic responder**.
- Four forced resets cancelled outstanding memory reads after a delayed independent responder flush handshake. No new load starts until flush_ack and no stale rsp_valid.
- Four PASS_TAGGED_SUITE completions. No PHY, real memory controller, measured clock period or energy.
- CI artifact 14933669067, metadata digest sha256:542f034dbbe6f08f2b298a9d3ab97fe15da39eea9efe4ca5fa647d38722f9f1c; metadata inspected, bytes not independently downloaded. GitHub reports expiry 2027-02-22.

**Critical limitations:** Bus width, response service distribution and backpressure differ from prior 402-byte RTL runs, so 70 vs 849/2049 cycles is **NOT a controlled hardware speedup**. Combinational and register area, frequency, power, layout, PHY, memory capacity, DDR/HBM timing, model quality and baseline GPU are not measured. These tests use already-quantized inputs, not a complete QACT/FP32 pipeline. The flush handshake is only safe if the independent responder truthfully cancels outstanding responses before asserting flush_ack, and CDC/recovery are not validated.

## Next verification
Add fault injection for unknown/duplicate tags and blocked flush-ack with stale responses. Attempt same-flow Yosys generic synthesis of byte and tagged wrappers including identical integer core to measure generic resource sensitivity, not physical PPA. Then perform controlled same-service-model comparisons and expand full-system G1 feasibility. No final architecture or physical advantage established. PR #11 stays draft and main is preserved.


## Static byte-enable RTL synthesis and equivalence — verified
At commit c78897d234c2f7f4d42a93bdca514041802c4bfd, GitHub Actions [run 45423639794](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45423639794) passed the independent 8-job *original vs static* tagged RTL log equality and all fault cases. Separate Yosys 0.33 `synth -top` generic netlist included 16,320 cells for the full exact INT8 core + static tagged loader hierarchy (per-module 12,767 exact core and 3,554 wrapper reported). CI artifact 14936352849 metadata SHA256 3fbe3be09d79dc0af7e902a2b2f45729abed60ca0ca75d6cb2e94745e1e42ec8. This is a generic cell-level synthesis estimate, not mapped FPGA/ASIC timing, area or power. The original variable-index design and byte wrapper were **not** part of that successful static-only synthesis run; no area/performance ratio established. An earlier separately running comparative synthesis 45421862810 awaits its actual outcome.
