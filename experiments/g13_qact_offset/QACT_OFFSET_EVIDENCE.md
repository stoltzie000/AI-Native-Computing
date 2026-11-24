# G1.3 QACT group-offset RTL validation evidence
- Branch research/g13-qact-offset, commit 5ad4f88ff3a1db767747dd2cb2b1dbc630caf427.
- CI run 45448838412, attempt 1, job 138639995299 SUCCESS. Actual log 32 PASS_QACT_OFFSET_RTL lines, 6 independent Python unit tests, 32 input cases x 8 group-offset outputs = 256 exact offsets. Source fixture SHA256 5ccf3dbe8a445c3808abcb39adc96076197a6e6b9f8d65a7e6d51d729684afea.
- Edge patterns: all zero, equal magnitudes, negative sign, FTZ denormals, extreme exponent differences and saturation, infinite/NaN word patterns, seeded randomized 64-word inputs. Semantics use unsigned maximum absolute FTZ word as in pinned upstream QACT stage.
- EVIDENCE CLASS RTL_RESULT and software differential, NOT synthesis area, timing, power, full QACT quantization, or physical processor.
- Decision: ADOPT validated offset sub-block as test reference; TEST reciprocal, scaling and RNE int8 conversion separately, with exact upstream QACT ISA differential and same quantized MXU fixture integration. Preserve earlier RTL.
- Remaining: full QACT, physical memory, power, thermal, model quality and optimized GPU baseline; G1 OPEN.
