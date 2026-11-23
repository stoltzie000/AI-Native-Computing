# Real pretrained activation-zero audit — controlled research experiment

**Purpose:** Falsify the hypothesis that exact-zero activations are common enough to make our v0.8–v1.0 activation-gated weight fetch materially faster than an optimized GPU. This is not a GPU speed or power benchmark.

## Reproducible source and weights

The model implementation is pinned at `llaa33219/MicroMixer-4` commit `8300d64843dd9e0baa9270600632c25e5aa15dc5` (Apache-2.0). It is checked out in an isolated GitHub Actions runner without credentials for the source model. Only its documented, pinned PyTorch model classes are imported. No user secrets or model repository code from unpinned branches is executed. `main` changes after that revision are excluded.

Two checkpoints were already measured and SHA-verified during the project's real-weight audit:

| Model | Checkpoint filename | SHA-256 |
|---|---|---|
| MicroMixer-4-1M-TinyStories (attention-free) | epoch_2.safetensors | `f2d97561d43a1588e2a6b44a0c71fdd0069d03dc7e169a17c3a5f0082c15186e` |
| MicroT-test1-300K-TinyStories (transformer) | epoch_2.safetensors | `9bf0a9c2f84ef8e17a9cdabfec0ab566da526de099d3e928d96b359306b89224` |

The runner downloads and hashes checkpoints **before** loading them, then calls `load_state_dict(strict=True)` to reject architecture/weight mismatches. Source is Apache-2.0; license notices remain in the upstream checked-out tree. The trained weight files are never pushed or attached; JSON reports contain only aggregate tensor statistics, metadata, and hashed deterministic output-token IDs.

## What exactly is measured

For 128 unique deterministic byte-level text prompts (8 template sentences plus distinct sequence identifiers, four unpadded sequence lengths 16/32/48/64), trace forward *prefill* through actual pretrained models, in FP32 CPU mode:

- Exact binary/numerical zeros in the inputs to every `torch.nn.Linear` (zero including `-0.0`) and separately every `torch.nn.Conv1d`.
- Total operator-input elements, exact zeros, fractions, per-layer variation and shape examples.
- Derived **logical** `nn.Linear` multiply terms associated with those zeros; this is **not** measured memory read traffic or speedup.
- Finite output logits and hashed argmax-token IDs as a deterministic operation sanity check (not quality evaluation).

No post-training pruning, quantization, or weight mutation is performed. Does **not** intercept direct `torch.nn.functional.linear`/`F.conv1d`, custom kernels, attention SDPA internals, or operation fusion; thus measured coverage is a **subset** of model work. Convolution input zeros cannot be directly treated as skipped weight *columns*.

## Verification and noise control

Run locally if pinned pretrained weights and the source package are available. No checkout or downloads are forced by the Python tests:

```bash
python -m unittest discover -s experiments/real_activation_audit/tests -p 'test_*.py' -v
python experiments/real_activation_audit/activation_probe.py --model mixer --checkpoint /path/to/epoch_2.safetensors --prompts 128 --output /tmp/mixer.json
```

GitHub Actions is configured for **one branch push trigger**, *not* both pushes and pull requests; no scheduled workflow. No extra GitHub Actions run is triggered by adding docs or editing research files afterward. Further reruns are only when explicitly chosen by changing the audit workflow on the working branch or GitHub UI `workflow_dispatch`. This reduces notification volume but does not change the user's GitHub account notification preferences.

The evidence is considered valid only if both SHA256 checks, strict model checkpoint loads, 8 unit tests and both full real inference scans pass and the JSON reports are inspected. Failure is not silently upgraded to a positive measurement.

## Decision gate

If actual exact-zero rates at the measured linear inputs are negligible, reject naturally occurring exact-zero activation gating as the primary performance argument for the **measured models**. A separate nonlinearity or model family can have different sparsity; no generalization is warranted without its data. Even a high zero rate must survive physical burst granularity, dispatch overhead, clock/power and matched GPU comparisons.

## Verified result — November 23, 2026

GitHub Actions [run 45269327361](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45269327361), job 138024617965, completed **success** with **8 passing unit tests, two SHA256-verified pretrained model files, two strict weight loads, and 128 unique prompt inferences per model**.

| Model | Linear-input exact zero elements | Exact zero fraction | Logical MAC terms associated with zero inputs |
|---|---:|---:|---:|
| MicroMixer 1M attention-free | 65,984 / 43,366,400 | **0.1522%** | 8,445,952 / 4,289,331,200 (**0.1969%**) |
| MicroT 300K transformer | 45,016 / 13,762,560 | **0.3271%** | 3,601,280 / 1,415,577,600 (**0.2544%**) |

**Decision:** Natural exact-zero input gating cannot justify a major whole-model acceleration gain for these measured CPU FP32 models. [Full results and reversible decision](RESULTS_AND_DECISION_2026-11-23.md) · [Machine-readable aggregate](results/128_unique/aggregate.json). The first successful smaller run (32 passes with eight unique cases repeated) is preserved separately under `results/initial_32_repeated/`.

These data are not whole-system DRAM traffic, silicon energy, clock timing, larger-model benchmarks or optimized GPU comparisons. The project's tested 64-row RTL remains useful as a numerical and memory-controller research vehicle, but it is **not** selected as the winning processor architecture.
