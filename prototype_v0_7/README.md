# AI-Native-Computing — v0.7 research PE and verification

**Project goal:** experimentally develop a superior AI-native processor/computer, not a graphics card. No current processor or motherboard has demonstrated superiority over modern GPUs.

This milestone strengthens hardware verification and investigates how parallel multiplier lanes trade cycles for likely logic area and critical path. The *historical* v0.6 RTL is unchanged. v0.7 adds an input-latched PE, an independent CPU signed-integer reference, an enhanced legacy differential testbench, and parameterized randomized RTL regression.

## Behavioral contract

- A 4x4 block and vector are captured on `start && ready` (unlike v0.6, input pins may then change).
- `LANES` can be 1, 2, 4, 8, or 16 for the 4x4 configuration, so a dense block uses 16, 8, 4, 2, or 1 compute cycles, respectively; these are **RTL scheduling targets**, not measured time or throughput.
- `certified_nonzero_block=0` bypasses multiplication only if the weights are genuinely all zero. A false certificate produces wrong answers.
- Integer inputs are signed 8-bit by default; accumulation wraps in signed `ACC_W` bits. No saturation or floating-point semantics.
- `busy` is asserted until `done` is produced, at which time `ready` returns.
- No SRAM, HBM controller, fabric PHY, PCIe replacement, motherboard, AI compiler or trained model has been implemented.

## Tests

Python reference (run in repository root):

```bash
python -m unittest discover -s prototype_v0_7/tests -p 'test_*.py' -v
```

Verilog tests require Icarus Verilog and are configured through [the CI workflow](../.github/workflows/rtl-v07-verification.yml). The workflow compiles the unchanged v0.6 RTL against 256 randomized cases, then runs the v0.7 RTL at 5 lane configurations times 2 accumulator widths. It also attempts generic Yosys synthesis. **A workflow definition is not a passing run.**

## Evidence

Six Python unit tests passed locally against source subsequently Git-blob-verified on the PR branch. A full historical v0.2–v0.6 Python rerun passed 169/169 in a clean extraction. Actual Verilog compilation, simulation and synthesis are **unverified** unless attached GitHub Actions logs demonstrate a completed run.

See [verification and failure criteria](docs/DESIGN_REVIEW.md). The branch is submitted as a draft pull request; do not merge until the HDL regressions and review pass.
