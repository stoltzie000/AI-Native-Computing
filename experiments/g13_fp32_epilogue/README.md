# G1.3 synthesizable FP32/FTZ integer epilogue — research candidate

Separate stacked branch `research/g13-fp32-epilogue` based on the verified G1.3 tagged-burst research. The first-order goal is IEEE binary32 finite arithmetic and exceptional-value functional equivalence, not a full QACT circuit or physical PPA.

- Signed 48-bit exact accumulator conversion to binary32, using round-to-nearest ties-to-even and signed output.
- Independent binary32 multiply with FTZ on both inputs and output, canonical quiet NaN and signed zero, handling infinity, overflow, and subnormal values which round up to the minimum normal.
- Five independent output epilogues follow the actual openTPU MM dependency order: `float32(acc[n]) * weight_scale[n]`, then `(activation_scale * 2^-16)` with separate binary32 rounding, then final multiplication. No algebraic reassociation.
- Generates 24 new per-activation-row scalar FP32 output fixtures from the **actual upstream pinned ISA**, not just a Python formula. Independently compares Python FP32 reference with upstream before authoring expected memory images.
- Separately tests 2,048 binary32 multiplication pairs spanning zeros, signed zeros, subnormals, inf/NaNs and random raw codes, and 2,048 signed int48-to-float conversions including RNE edge values. This does not exhaust the input space.

**Evidence initially pending:** GitHub CI for the dedicated branch. Tests must pass before marking RTL_RESULT. No physical chips, optimized GPU baseline, achieved frequency or power. No memory writeback, activation QACT hardware, or complete model computation in this branch. This research is not merged to the active G1.3 branch or main while validation is incomplete.

**Next action:** Inspect all failing vectors and correct RTL, preserve failures, then implement tagged writeback and full QACT input generation with independently pinned upstream numerical behavior. Synthesize using a documented library flow only after functional acceptance; never interpret generic cells as hardware power.

## CI failure and root-cause recovery — 2026-11-24
Run 45424621907 failed after successfully generating and cross-verifying all 24 actual upstream ISA reference rows and 2048 random arithmetic vectors. The first SV test stimulus used `n=0` as its initial register value, then assigned zero to the first tested vector; Icarus `always @*` had no signal transition for that first vector, so the purely combinational converter output remained `x` at time 1000. This was a **testbench initialization artifact**, not demonstrated numerical RTL failure. Raw failure log and artifact 14935413664 remain retained. Corrective action: initialize testbench DUT drive signals to unknown `'x` and explicitly assign every first stimulus, ensuring a transition. Verify by rerunning full CI. The next failure, if any, must be separately inspected; no success assumed.
