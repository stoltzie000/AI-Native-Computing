# Measured real-model activation sparsity — verdict (2026-11-23)

**Evidence:** Real **CPU FP32 inference** on two SHA256-authenticated pretrained TinyStories checkpoints, using upstream `llaa33219/MicroMixer-4` code pinned at `8300d64843dd9e0baa9270600632c25e5aa15dc5`, strict state loading, 128 distinct unpadded deterministic byte-level prompts per model, lengths 16/32/48/64. GitHub Actions run [45269327361](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45269327361), job **138024617965**, completed **success** (8 unit tests, both checkpoint hash checks, both model inference scans and JSON artifact upload).

This measurement checks exact zeros in inputs observed through PyTorch `nn.Linear` hooks. It does **not** intercept low-level `torch.nn.functional.linear`/`conv1d`, fusion kernels, or attention internals. All fractions are based on *executed* model graph elements, not measured DDR/HBM transfers. No token-output quality study or GPU performance comparison is implied.

## Main measured results

| Model | Linear-input elements | Exact zeros | Zero fraction | Logical linear MAC work zero-associated | Logical MAC skip fraction |
|---|---:|---:|---:|---:|---:|
| MicroMixer V87 attention-free 1M | 43,366,400 | 65,984 | 0.1522% | 8,445,952 / 4,289,331,200 | 0.1969% |
| MicroT V88 transformer 300K | 13,762,560 | 45,016 | 0.3271% | 3,601,280 / 1,415,577,600 | 0.2544% |

These fractions are genuinely small and **do not support a substantial whole-model acceleration claim** from naturally occurring exact-zero gating for these particular models and prompts. `logical MAC skip fraction` weights zero inputs by the corresponding linear layer's output dimension, and is a theoretical arithmetic count, **not** an implemented reduction in memory bytes, clock cycles, energy or physical GPU time.

### Layer-specific exceptions

Some small layers contain more exact zeros even though the entire model is mostly dense. Preserve the possibility of *targeted, locality-aware* optimization but do not attribute a global speedup to them. Top observed layers:

**MicroMixer V87 attention-free 1M:**

- `Linear:blocks.3.remixer.pool_up`: 27.63% zero input elements (81,920 observed).
- `Linear:blocks.1.remixer.pool_up`: 19.88% zero input elements (81,920 observed).
- `Linear:blocks.5.remixer.pool_up`: 16.59% zero input elements (81,920 observed).

**MicroT V88 transformer 300K:**

- `Linear:blocks.3.mlp.fc2`: 1.71% zero input elements (1,392,640 observed).
- `Linear:blocks.2.mlp.fc2`: 1.02% zero input elements (1,392,640 observed).
- `Linear:blocks.1.mlp.fc2`: 0.51% zero input elements (1,392,640 observed).

## Previous baseline and correction

An earlier CI run [45268509259](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45268509259) also succeeded with 32 forward passes, but used **only eight distinct prompt/length combinations repeated four times**. The original full JSON reports are preserved under `results/initial_32_repeated/`; those runs found 0.1127% (MicroMixer) and 0.3646% (MicroT) exact zeros at measured linear inputs. The unique-128 expansion was performed to remove that input-diversity limitation, and it confirms the same low-sparsity direction. Both runs were real inference tests; neither is a randomized, statistically representative broad-language quality trial.

A preceding **failed** CI run [45268313248](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45268313248) identified a missing clean-runner `packaging` dependency. The workflow was corrected and later verified successful; this failure remains part of the test history. Actions workflow uses **push to the experiment branch only when its own YAML file changes**, plus an optional manual dispatch; it intentionally avoids duplicate push-and-PR triggers to reduce email notifications.

## Research decision and scope

**REJECT as the primary acceleration justification for the two measured checkpoints:** natural exact-zero activation gating through the observed FP32 linear layers. v0.8/v0.9/v1.0 remain functional RTL designs, but they cannot be claimed superior or useful across general models based on these sparse-zero observations. Do not remove previous models or files; this is an experimental *mechanism* rejection under tested conditions.

**Retain as conditional research:** models deliberately trained for sparse activity with task-quality validation, threshold/quantization-induced sparsity only if quality and conversion costs are proved, and specialized layers with high exact-zero rates. Do not apply today's small-model fractions to 30B models by assumption.

**Shift first-priority work to:** (1) physical/generic compute-memory locality and burst-efficient streaming independent of zeros; (2) an existing Gemmini/openTPU/APEX baseline on the same numerics and memory resources; (3) testing alternative SSM/Mamba, partially fixed compute, near-memory/analog/photonic technologies with end-to-end quality and electrical power accounted for. The project remains open to a nonstandard motherboard and interconnect.

## Evidence level and remaining validation

- Verified **CPU trained-model activation measurement**, not FPGA or silicon.
- Earlier RTL passed Icarus/Yosys functional/generic synthesis checks; no physical chip/motherboard measured.
- No native SRAM macro, real HBM PHY, physically mapped critical path, wall-plug joules, matched optimized GPU end-to-end baseline, or full-model quality parity test.
- Small byte-level TinyStories models and deterministic prompt set limit generality; larger models and independent task datasets remain necessary.
- Exact-zero post-quantization fractions are **not** estimated here because the correct quantizer, calibration, conversion overhead, and task accuracy were not measured.

Full per-layer output: `results/128_unique/mixer_activation.json` and `results/128_unique/transformer_activation.json`. Compact structured measurements: `results/128_unique/aggregate.json`.
