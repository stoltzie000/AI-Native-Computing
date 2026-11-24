# G1.3 bounded tagged-burst RTL candidate — pending remote verification

Commit scope: new isolated Verilog module and independent randomized/OOO-responder bench, with the existing tested byte wrapper untouched.

## Frozen test contract
- Read exactly 402 prequantized bytes in order after local reassembly: 64 q, 320 w, 8 da, 10 dw.
- Default 64-byte response bus: seven accepted request tags, last burst contains 18 useful bytes and 46 masked padding bytes.
- At most four outstanding requests; one issue handshake/cycle and at most one tagged response/cycle.
- Out-of-order response arrivals are reassembled by the exact transaction tag. Duplicate/unknown response tags cause protocol_error and a fail-closed state until reset.
- reset asserts flush_req; no new job is accepted until independent responder confirms prior responses were cancelled via flush_ack and rsp_valid is no longer asserted.
- Integer computation launches only after all seven responses have been applied, checking the same five 48-bit accumulators and dropped-group count from the real pinned upstream ISA fixture as the previous byte wrapper.
- The bench deliberately cancels outstanding transactions across reset, and runs two distinct jobs without a reset between them.

**Evidence class:** authored RTL candidate, not yet a verified RTL_RESULT until the new GitHub Actions Icarus job completes and logs are inspected. No synthesized timing/area or energy claims. The flush-ack interface guarantees safety only if the external memory subsystem actually cancels all responses before acknowledging flush; electrical and reset-domain synchronizer design remains open.

Next: inspect failures, correct/retest, archive exact CI results and synthesis/area analysis. G1 is OPEN.
