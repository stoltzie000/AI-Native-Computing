"""Vendor peak *memory* specifications + clearly synthetic service assumptions."""
from engine import System, Memory


def reference_systems():
    # Compute_tops/banks/sustained_fraction=100% are NOT verified performance
    # figures. Only GPU capacity and memory peak bandwidth are vendor-sourced.
    return [
        System("RTX 5090 peak-memory proxy", 1, Memory(32, 1792), 500,
               provenance="NVIDIA: 32GB/1792GB/s peak; bank count/compute hypothetical"),
        System("H200 peak-memory proxy", 1, Memory(141, 4800), 500,
               provenance="NVIDIA: 141GB/4800GB/s peak; bank count/compute hypothetical"),
        System("MI355X peak-memory proxy", 1, Memory(288, 8000), 500,
               provenance="AMD: 288GB/8000GB/s peak; bank count/compute hypothetical"),
    ]


def research_systems():
    return [
        System("Custom 4-module stacked-HBM fabric (hypothesis)", 4,
               Memory(64, 4000, 16, 0), 200,
               fabric_gbs=500, fabric_latency_us=2,
               provenance="All per-module throughput and fabric numbers hypothetical; no layout validated"),
        System("Custom 8-module HBM fabric (hypothesis)", 8,
               Memory(32, 2500, 16, 0), 200,
               fabric_gbs=800, fabric_latency_us=2,
               provenance="All per-module throughput and fabric numbers hypothetical; no layout validated"),
        System("Custom 8-module HBM + near-memory SRAM (hypothesis)", 8,
               Memory(32, 2200, 16, 0), 200,
               fast=Memory(.5, 4000, 16, 0), kv_fast_fraction=.25,
               fabric_gbs=800, fabric_latency_us=2,
               provenance="0.5GB SRAM/module (memory macro area lower bound ~105mm2 each); all bandwidth assumptions unverified"),
        System("48GB SRAM wafer-fabric logical modules (high-risk)", 4,
               Memory(4, 1000, 16, 0), 200,
               fast=Memory(12, 8000, 16, 0), weight_fast_fraction=1, kv_fast_fraction=1,
               fabric_gbs=400, fabric_latency_us=1,
               provenance="Requires multi-die/wafer nodes; single reticle die REJECTED in v0.2.1; speeds hypothetical"),
        System("8-module hot-bank stress case (failure test)", 8,
               Memory(32, 2500, 16, 0), 200,
               fabric_gbs=800, fabric_latency_us=2, bank_mapping="hot_bank",
               provenance="Intentionally adversarial bank distribution, not expected normal layout"),
    ]
