# Activation-gated demand-fetch PE — verification and decision log (2026-11-23)

## Motivation and invariant

The v0.7 block-sparse PE can skip a whole weight block only if its weights are exactly zero. The v0.8 candidate instead observes exact-zero *input activations* and avoids requesting the corresponding weight entries. This is an exact identity for the implemented signed integer arithmetic, including modular accumulator wrap. It is not a guaranteed property of trained AI workloads.

## Verified source and first Actions execution

- Branch: research/activation-gated-v08; PR #2 (draft).
- GitHub Actions run 45239447045, job 137919806911 **completed success**:
  - Icarus Verilog testbench **99 cases at 16-bit accumulation** and **99 cases at 32-bit accumulation**, independently computing dense matrix-vector expected sums and checking external accepted memory request count.
  - 7 standalone Python arithmetic reference tests passed (before traffic model tests were added).
  - Generic Yosys synthesis completed: **2250 generic cells**, not real area, performance, clock, power or transistor count.
- Testbench exercises every-zero, mixed-zero, dense inputs, signed arithmetic, random weights/activations, backpressure, host-input mutation after capture, reset and done pulse.
- The traffic model and additional 7 tests were added later; DO NOT claim they passed the first CI run. Obtain latest successful run logs before acceptance.

## Architectural tradeoff

For a 4x4 tile:
- Dense 4/4 active columns: **16** accepted external weight requests.
- 3/4 active: **12**.
- 2/4 active: **8**.
- 0/4 active: **0**.
- These are integer message/request counts from the numerical oracle and covered cases in RTL, *not measured off-chip DRAM/HBM bursts*. A memory subsystem may fetch a cache line or full burst even if one element is requested, losing this advantage.

The v0.8 FSM serializes each request and response. The independent analytical **optimistic** cycle bound uses two accept/done cycles, 16 scan cycles, and two extra control cycles per issued weight (e.g., 50 cycles dense, 34 at half active, 18 all zero). This is not a measured cycle count and ignores clock-frequency, latency, burst fetches, backpressure and memory/compute overlap.

## Model-level lower bound

Prior Qwen2.5-32B 4-bit 32K-context E1 scenario estimated weights 17.875GB/step and KV state traffic 8.590GB/step. With no overhead, ideal bandwidth speedup from weight suppression fraction f is:

speedup = (17.875 + 8.590) / (17.875 × (1 − f) + 8.590)

At f=0,25,50,75,100%: speedup theoretical 1.000, 1.203, 1.510, 2.027, 3.081. Achieving ideal 2× requires ≥74.028% exact-zero input activity with traffic avoided and equal system bandwidth. These are **not observations** of trained model activation zero fractions; in a real design control/metadata/fragmentation add overhead and attainable speedups can be smaller or negative.

## Decision

**Functionality:** first RTL test success for two accumulator widths, and real memory-transaction suppression in the testbench. **Performance:** unresolved; serialized request design is likely a poor high-performance accelerator at low activation sparsity. This is a *falsifiable architecture research result*, not a final silicon choice.

**Next engineering work:**
1. Confirm latest full Python and RTL regression run (including traffic model).
2. Prototype coalesced/vectorized read requests and outstanding-memory-request queue with tags and ordered commit.
3. Measure sensitivity to realistic memory burst size, latency, queue depth and actual activation sparsity.
4. Verify on a pinned trained model and compare against an optimized GPU sparse kernel at identical quality.
5. Technology-map RTL on a documented FPGA or ASIC standard cell library to estimate frequency/energy; obtain actual hardware measurements before any GPU superiority claim.
