# Archived analytical MVP v0.1 — historical, not validated hardware
Archived on 2026-11-23 from the prior AI-Native Processor work.

This is a first-order 30B-model, PCIe accelerator roofline calculator. It is preserved for provenance and regression comparisons, **not** as the current design or evidence that any hardware outperforms a GPU.

Its four arithmetic unit tests passed in an isolated Python environment on 2026-11-23. Limitations: KV cache is counted as capacity but its per-token memory traffic is not accounted for by default; evaluate() does not reject insufficient physical memory; electrical power, utilization, acquisition cost and bandwidth are assumed; no silicon, RTL, FPGA, motherboard, calibrated GPU benchmark or measured energy data is represented here.

The broader AI-Native-Computing project is now an unconstrained full-system co-design effort. Current requirements: ../../docs/PRODUCT_DEFINITION.md and ../../docs/VALIDATION_PLAN.md.

Run within this folder with: python -m unittest -v test_model
