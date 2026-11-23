# Real pretrained model zero-block audit

**Purpose:** Falsify the assumption that standard trained model weights contain enough exactly-zero contiguous blocks for the v0.6/v0.7 weight-zero-block PE to substantially reduce memory bandwidth.

## Pretrained test assets

1. [MicroMixer-4-1M-TinyStories](https://huggingface.co/llaa33219/MicroMixer-4-1M-TinyStories/blob/main/epoch_2.safetensors), approximately 996,873 parameters, attention-free pretrained model, 4.02MB checkpoint. Published SHA256: `f2d97561d43a1588e2a6b44a0c71fdd0069d03dc7e169a17c3a5f0082c15186e`.
2. [MicroT-test1-300K-TinyStories](https://huggingface.co/llaa33219/MicroT-test1-300K-TinyStories), approximately 297,680 parameters, tiny attention transformer pretrained on TinyStories, about 1.19MB. Published SHA256 from its Git LFS pointer: `9bf0a9c2f84ef8e17a9cdabfec0ab566da526de099d3e928d96b359306b89224`.

These two models are deliberately small and **not matched in parameter count, intelligence or quality**. Their role is to provide genuine trained weight files from differing neural network families, not a hardware performance comparison.

## Audit protocol

CI downloads the public Apache-2.0 model weights to the runner's temporary filesystem, verifies their known SHA256 hashes before analysis, and runs the project's **read-only** Safetensors exact binary zero auditor from `prototype_v0_7/tools/safetensors_sparsity.py`. A Python summary prints weight-element fraction and all-zero 4×4 and 8×8 block fractions, excluding partial blocks. Reports are uploaded as ephemeral CI artifacts; **no model weight files are committed**.

No Python model code from the remote models is executed: the auditor only parses the .safetensors file's binary tensor bytes.

If download or hash verification fails, CI should fail and **no sparsity measurements should be claimed**. Results must not be invented or inferred from model descriptions.

## Fundamental limit

A weight-zero-block PE only skips model weights that have complete blocks of **exact zeros**. SparseGPT-style unstructured pruning or small-magnitude weight thresholds do not guarantee this condition. Even if zero blocks exist, compressed indices and fragmentation must be included in energy/latency comparisons.

Weight-zero measurements do **not** measure activation sparsity. That separately requires executing an actual pinned model on a defined dataset and recording intermediate tensor values while checking task quality.

## Current status

**Completed, independently checked:** GitHub Actions run [45241981337](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45241981337), job 137928727818, succeeded. Both pretrained checkpoint downloads matched the published SHA-256 hashes. Direct read-only measurements:

| Pretrained model | Eligible 2D elements | Exact zero elements | Eligible 4x4 blocks | Exact zero 4x4 | Eligible 8x8 blocks | Exact zero 8x8 |
|---|---:|---:|---:|---:|---:|---:|
| MicroMixer attention-free 1M | 874,624 | **0** | 54,272 | **0** | 13,456 | **0** |
| MicroT attention transformer 300K | 296,960 | **0** | 18,560 | **0** | 4,640 | **0** |

The measurements are preserved in [results/MEASURED_2026-11-23.json](results/MEASURED_2026-11-23.json). This falsifies the assumption that *these particular ordinary, unpruned models* support any exact-zero-weight block skipping; it does NOT prove all pretrained models are dense and does not measure activations or infer speed. The zero-block bypass datapath remains mathematically valid and could still apply to deliberately sparse weights if task quality is independently validated.
