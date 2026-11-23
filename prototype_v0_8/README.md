# AI-Native Computing — v0.8 activation-gated weight-demand prototype

Date: 2026-11-23. State: research RTL, not physical processor/motherboard.

## Purpose
A different memory-compute execution model from v0.7: do not load a weight at all when the corresponding activation is *exactly zero*. Since w×0=0 in the tested signed-integer semantics, the output is unchanged without needing a pre-sparse weight matrix. No modification to existing pretrained weights is required. This method is not inherently novel: sparse kernels and activation-gating architectures have established precedents. Competitive superiority is the unproven requirement.

## Design implemented
- Signed INT8 activation input captured on start. Iterates a 4x4 matrix-vector multiply, scanning all 16 conceptual products.
- For a zero activation, directly skips the product and does not assert mem_req_valid.
- For other activations, requests the associated weight using row/col indices, waits for an in-order memory response, and accumulates signed INT8×INT8 into wrapped signed 16- or 32-bit output.
- Externally visible issued_weight_reads, issued_multiplies and skipped_products counters.
- One outstanding response at a time. Backpressure and delayed response allowed, but out-of-order returns are NOT supported.
- The accompanying testbench models actual request handshakes/response traffic, and checks both output and external requests against an independent dense arithmetic oracle.
- Python reference and parameterized traffic/latency bounds.

## Verified evidence
GitHub Actions run 45239447045, job 137919806911, completed successfully. Icarus ran **99 cases each** at ACC_W=16 and ACC_W=32 (198 total); Python arithmetic oracle **7/7** passed at this checkpoint. Yosys generic synthesis of default 4×4 ACC32 source completed with **2,250 generic cells**. Values are NOT silicon area or clock timing, and Yosys cell counts across v0.7 and v0.8 are not a fair physical implementation comparison.

The independent traffic model in `traffic_model.py` and its 6 tests were added after this run. Verify their completed CI results separately before claiming them.

## Fundamental performance constraint
For the previous Qwen2.5 32B 32K decode proxy, prior v0.5 assumptions give **17.875 GB** of weight traffic + **8.590 GB** of KV traffic per output step. Even if all weight reads are suppressed for a fraction f of exactly-zero activations and there is no metadata or control cost, the ideal bandwidth-only speedup is

`(17.875 + 8.590) / (17.875*(1-f) + 8.590)`.

To reach 2× requires **f >= 0.74028** (74.028%). At f=50%, limit is about 1.51×; at 75%, ~2.03×. These numbers are *conditional estimates*; they are not actual zero percentages measured in pretrained models, nor performance measurements.

**Important negative finding:** The current FSM scans every row/column and serializes each nonzero weight request. Even if traffic decreases, controller and random-access latency can make it much **slower** than bulk loading and four parallel multipliers. A simple lower bound is `2 + 16 + active_weight_count*(request_cycle_cost + response_cycle_cost)`; it omits queueing, power, memory burst behavior and compute/memory overlap.

## Reproduce
```bash
python -m unittest discover -s prototype_v0_8/tests -p 'test_*.py' -v
# Verilog simulation and Yosys are configured in .github/workflows/rtl-v08-verification.yml
```

## Next mandatory design gate
1. Verify all RTL and Python tests on the latest source commit.
2. Measure actual model activation-zero fractions and end-task accuracy on a pinned trained model and sparse GPU software baseline; no such measurements currently exist.
3. Replace serialized row/column single-weight requests with *coalesced column-group requests* and queueing, while preserving demand suppression and correctness.
4. Model real memory burst granularity and payload efficiency; test zero fractions from 0 to 1, not only favorable cases.
5. Only after a justified design emerges, perform FPGA timing, power and complete system comparison against contemporary GPU implementations.

A successful block-sparse or activation-gated microkernel is not by itself a superior AI-native computer.
