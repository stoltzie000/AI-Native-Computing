# Design and evidence ledger — v1.0

Research target: replace 4-byte request fragmentation of 4-row v0.9 with a 64-row, 64-byte contiguous signed INT8 column read, storing it locally and using only 2 or 4 arithmetic lanes.

- **Proven only by mathematics initially:** For 64 rows and two active columns, 128 useful weight bytes are needed, and a 64-byte minimum-transfer assumption gives 128 transferred bytes using two requests. Earlier 4-row tiling required 32 assumed transfers (2048 bytes) for the same work.
- **Not yet proven at file authoring:** Any Verilog compilation, waveform correctness, synthesis or hardware performance. CI results must be recorded after run completion.
- **Not physically built:** SRAM macro, HBM PHY/controller, chiplet, motherboard, power/cooling. `column_hold` is a **wide register**, not a recognized silicon SRAM specification.
- **Deliberate limitation:** One outstanding request; whole column compute occurs after response. This can be much slower than pipelined bulk streaming, even with fewer requests.
- **Quality risk:** Activation sparsity is unknown for genuine trained models; there is no reason to assume the 74% exact-zero activation threshold needed for a 2× ideal bandwidth-only benefit.
- **Next conditional decision:** Keep 2/4-lane buffering only if verified timing/resource and memory-transaction measurements suggest an advantage; otherwise change the hardware/software dataflow.
