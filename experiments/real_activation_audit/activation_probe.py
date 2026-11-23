"""Exact-zero inputs to trained neural-network weight operators.

This runs *pinned* externally reviewed PyTorch model implementations and
hash-verified, read-only pretrained Safetensors checkpoints. It does not
benchmark a physical accelerator or claim that skipped logical operations
translate into DRAM/HBM transfer reductions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import torch
from safetensors.torch import load_file

UPSTREAM_SOURCE_COMMIT = "8300d64843dd9e0baa9270600632c25e5aa15dc5"

SOURCES = {
    "mixer": {
        "repo": "llaa33219/MicroMixer-4-1M-TinyStories",
        "sha256": "f2d97561d43a1588e2a6b44a0c71fdd0069d03dc7e169a17c3a5f0082c15186e",
        "name": "MicroMixer V87 attention-free 1M",
    },
    "transformer": {
        "repo": "llaa33219/MicroT-test1-300K-TinyStories",
        "sha256": "9bf0a9c2f84ef8e17a9cdabfec0ab566da526de099d3e928d96b359306b89224",
        "name": "MicroT V88 transformer 300K",
    },
}

# Fixed generated corpus; no prompts downloaded, no artificial padding zeros.
SENTENCES = (
    "Once upon a time, a little bird looked for its nest.",
    "The red boat sailed along a quiet river at dawn.",
    "A robot counted seven stars in the cold night sky.",
    "The child opened the blue door and found a small garden.",
    "The cat hid under the table while thunder echoed outside.",
    "Every morning the farmer carried fresh apples to the market.",
    "The engineer measured the circuit twice before powering it.",
    "The tiny dragon learned to fly above the mountain.",
)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


class ActivationCollector:
    """Capture inputs immediately *before* nn.Linear/Conv1d reads weights."""

    def __init__(self):
        self.stats = defaultdict(lambda: {"calls": 0, "elements": 0, "exact_zeros": 0,
                                          "logical_zero_weight_macs": 0, "logical_total_weight_macs": 0,
                                          "nonfinite": 0, "shape_examples": []})
        self.handles = []

    def _hook(self, name, kind, output_channels):
        def fn(_module, inputs):
            if not inputs or not isinstance(inputs[0], torch.Tensor):
                raise ValueError(f"Unexpected non-tensor input to {name}")
            t = inputs[0].detach()
            if not t.is_floating_point():
                raise ValueError(f"Expected real floating activations at {name}")
            if not bool(torch.isfinite(t).all()):
                raise ValueError(f"Nonfinite model activation encountered at {name}")
            zeros = int((t == 0).sum().item())
            elems = int(t.numel())
            row = self.stats[f"{kind}:{name}"]
            row["calls"] += 1
            row["elements"] += elems
            row["exact_zeros"] += zeros
            if len(row["shape_examples"]) < 3:
                shape = list(t.shape)
                if shape not in row["shape_examples"]:
                    row["shape_examples"].append(shape)
            if kind == "Linear":
                # Logical MACs for independent output rows. This is not a DRAM
                # traffic estimate and does not cover low-level F.linear calls.
                row["logical_zero_weight_macs"] += zeros * output_channels
                row["logical_total_weight_macs"] += elems * output_channels
        return fn

    def attach(self, model):
        for name, module in model.named_modules():
            if isinstance(module, torch.nn.Linear):
                self.handles.append(module.register_forward_pre_hook(
                    self._hook(name, "Linear", module.out_features)))
            elif isinstance(module, torch.nn.Conv1d):
                self.handles.append(module.register_forward_pre_hook(
                    self._hook(name, "Conv1d", module.out_channels)))
        if not self.handles:
            raise ValueError("No instrumented weight-consuming operators found")
        return self

    def close(self):
        for handle in self.handles:
            handle.remove()
        self.handles.clear()

    def report(self):
        if not self.stats:
            raise ValueError("No activation-bearing forward calls captured")
        layers = {}
        group = defaultdict(lambda: {"elements": 0, "exact_zeros": 0,
                                      "logical_zero_weight_macs": 0,
                                      "logical_total_weight_macs": 0})
        for name, row in sorted(self.stats.items()):
            kind = name.split(":", 1)[0]
            for key in group[kind]:
                group[kind][key] += row[key]
            layers[name] = {**row, "exact_zero_fraction": row["exact_zeros"] / row["elements"]}
        totals = {kind: {**d, "exact_zero_fraction": d["exact_zeros"] / d["elements"]}
                  for kind, d in sorted(group.items()) if d["elements"]}
        return {"summary_by_operator": totals, "per_operator": layers}


def construct_model(kind: str):
    if kind == "mixer":
        from src.model_v87_final import MicroMixerV87Final, v87_final_1m
        return MicroMixerV87Final(v87_final_1m())
    if kind == "transformer":
        from src.model_v88_transformer import MicroMixerV88Transformer, v88_transformer_300k
        return MicroMixerV88Transformer(v88_transformer_300k())
    raise ValueError(f"Unknown model kind: {kind}")


def analyze(kind: str, weight_path: Path, max_prompts=32) -> dict:
    if kind not in SOURCES:
        raise ValueError("Unknown model kind")
    if max_prompts < 1 or max_prompts > 64:
        raise ValueError("Prompt count outside configured finite bound")
    expected = SOURCES[kind]
    actual_hash = file_sha256(weight_path)
    if actual_hash != expected["sha256"]:
        raise ValueError(f"Checkpoint SHA256 mismatch for {kind}: {actual_hash}")

    torch.manual_seed(271828)
    model = construct_model(kind)
    state = load_file(str(weight_path), device="cpu")
    model.load_state_dict(state, strict=True)
    model.eval()
    monitor = ActivationCollector().attach(model)
    output_digests = []
    prompt_byte_lengths = []
    try:
        with torch.inference_mode():
            # Lengths 16 / 32 / 48 / 64, different text sources; real prefill.
            for i in range(max_prompts):
                length = (16, 32, 48, 64)[i % 4]
                txt = SENTENCES[i % len(SENTENCES)]
                repeated = (txt * ((length // len(txt)) + 2)).encode("utf-8")[:length]
                tokens = torch.tensor(list(repeated), dtype=torch.long).unsqueeze(0)
                logits = model(tokens)[0]
                if not logits.is_floating_point() or logits.shape[:2] != tokens.shape:
                    raise ValueError("Unexpected pretrained model output shape/type")
                if not bool(torch.isfinite(logits).all()):
                    raise ValueError("Nonfinite logits on pretrained model")
                # Deterministic task-operation sanity signal, not a quality grade.
                predicted = logits.argmax(dim=-1).to(torch.int32).cpu().numpy().tobytes()
                output_digests.append(hashlib.sha256(predicted).hexdigest())
                prompt_byte_lengths.append(length)
    finally:
        monitor.close()
    result = monitor.report()
    return {
        "kind": kind, "model": expected["name"], "checkpoint_repo": expected["repo"],
        "upstream_source_commit": UPSTREAM_SOURCE_COMMIT,
        "checkpoint_sha256": actual_hash, "checkpoint_file_bytes": weight_path.stat().st_size,
        "prompts": max_prompts, "prompt_byte_lengths": prompt_byte_lengths,
        "output_token_id_digest_sha256": output_digests,
        "measurement": "exact zeros in pre-weight module inputs, no model training or parameter mutation",
        "quantization": "none; pretrained torch float inference", "device": "CPU",
        "known_limitations": [
            "Only nn.Linear/nn.Conv1d module inputs are hooked, not functional F.linear/F.conv1d calls.",
            "Conv1d input zeros are not directly interchangeable with per-column linear weight gating.",
            "Values zero due to masking/padding or layers with other operators may affect generalizability.",
            "These are activation element statistics, NOT physical memory read savings or GPU timings.",
            "Short byte-level TinyStories models are not representative of state-of-the-art LLMs.",
        ],
        **result,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=list(SOURCES), required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--prompts", type=int, default=32)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    result = analyze(a.model, a.checkpoint, a.prompts)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("MEASURED_ACTIVATION_AUDIT " + json.dumps({
        "kind": a.model, "sha256": result["checkpoint_sha256"],
        "prompts": result["prompts"], "operator_types": result["summary_by_operator"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
