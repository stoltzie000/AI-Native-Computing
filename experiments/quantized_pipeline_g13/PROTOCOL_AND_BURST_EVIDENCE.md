# G1.3 protocol RTL and synthetic burst-model checkpoint — 2026-11-24

## Independent RTL protocol stress (verified)
GitHub Actions [run 45419680146](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45419680146), job 138535450362, completed **success** at commit afe6adbb6c322a37ed8f208981bd8e03060527c6. Job logs directly inspected; tests use upstream-pinned G1.2 generated 24 ISA fixtures.

- Original 48 cases: PASS_MEMORY_RTL 48/48 (24 unstalled, 24 stalled).
- Four deterministic stress suites: PASS_RESET request_wait, response_wait and compute, **12/12** aborted cases.
- Eight consecutive completed jobs: 402 accepted byte requests, 402 responses, 40 active integer groups each; 8/8 matched 48-bit ISA-derived five-output oracle plus exact dropped-group counts.
- All four PASS_PROTOCOL_SUITE records present. No overlapping requests accepted; request remains stable while stalled, launch follows all 402 responses, no spurious completion after reset and no duplicate completion.
- Observed total cycles per successful randomized job: 4211, 4060, 4048, 4201, 4274, 4301, 4339, 4124. These are **Icarus functional simulation cycles under arbitrary deterministic responder delays**, not DRAM timings or clock-frequency/energy measurements.
- Evidence artifact 14931129874, GitHub-reported ZIP digest sha256:4cc8bc4f492341eb73afa77ae1f5b5568e04dc76bffdcfadc1db1b90540f344f, expires 2027-02-22; summary retained permanently here. ZIP bytes were not independently downloaded or rehashed.
- Existing G1.2 RTL emits generic missing-time-unit and array sensitivity warnings, no compilation failure.

**Reset interface boundary:** The untagged byte-read wrapper assumes the external responder shares rst_n and cancels/flushes every accepted but incomplete request. It does not tolerate stale responses crossing an asynchronous reset. This is an explicit contract, not proof of robust independently-reset memory. Hardware redesign should introduce transaction epochs/tags or a quiescence/flush handshake.

## Independent software tagged-burst research candidate
`burst_reference.py` is a data-bearing synthetic scheduler/resequencer. It uses one request and one response port per modeled cycle, finite outstanding credits, per-tag deterministic latency jitter, response reordering, request/response stalls, aligned address calculations and head/tail byte masks. A byte-level scoreboard rejects duplicate or out-of-range output writes. It is **not synthesizable RTL** or a physical SRAM/HBM controller.

The isolated Python 3 runtime executed 5/5 independent local tests (300 randomized unaligned reads; 1/8/16/32/64/128-byte width sweep, depths 1/2/4/8; negative masks/storage/credit checks; deterministic byte-level equivalence). Sixth test checks the 24 generated pinned ISA operand fixtures; pending remote CI confirmation at this checkpoint. Exact tested source has been matched using Git blob hashes.

Synthetic comparison, fixed 402-byte operand payload, modeled 8-cycle response latency, no stalls/jitter, one request issue and one response service per cycle:
- 1-byte transfers, depth 1: 402 transactions, **3217 synthetic cycles**.
- 64-byte bursts, depth 1: 7 transactions, **57 synthetic cycles**.
- 64-byte bursts, depth 4: 7 transactions, **19 synthetic cycles**.
- 64-byte mode transfers 448 bytes, of which 46 are padding. These are simulated scheduling differences under *changed bus widths* and equal assumed per-transaction latency, not a speedup against a real controller/GPU or equivalent-resource proof.

## Next mandatory implementation
Implement and differentially test synthesizable, finite-credit tagged-burst RTL (out-of-order completion, head/tail masking, tagged transaction cancellation/reset contract, two consecutive ISA jobs) against these frozen fixtures. Establish issue/completion/compute-cycle boundaries, throughput sensitivity, resource/timing synthesis and realistic memory/PHY service assumptions. Continue G1 capacity, interconnect, power and thermal feasibility in parallel. G1 remains OPEN.
