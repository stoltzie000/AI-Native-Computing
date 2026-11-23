"""Deterministic, layer/transaction-level **research** simulator.

This is not RTL, cycle-accurate silicon, an optimized inference runtime, or a GPU
benchmark. Memory, compute and fabric service times are hypothetical except for
explicitly cited *peak* hardware specification inputs. All bytes are decimal;
units are seconds, bytes, B/s and operations/s internally.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Optional
import math

GB = 10**9
GIB = 2**30


def finite_positive(name: str, value: float, *, zero_ok: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric")
    if value < 0 if zero_ok else value <= 0:
        raise ValueError(f"{name} must be {'nonnegative' if zero_ok else 'positive'}")


@dataclass(frozen=True)
class Workload:
    name: str = "Qwen2.5-32B-Instruct analytical proxy"
    parameters: float = 32.5e9
    layers: int = 64
    hidden: int = 5120
    query_heads: int = 40
    kv_heads: int = 8
    head_dim: int = 128
    context: int = 32768
    batch: int = 1
    weight_bits: float = 4
    weight_metadata_fraction: float = .10
    kv_bits: float = 16
    scratch_gb: float = 2.0
    # Splits dense weight and operation workload around attention. A proxy,
    # not a detailed per-projection model (e.g. embeddings/LM head excluded).
    pre_attention_fraction: float = .075
    attention_output_fraction: float = .055
    activation_bits: float = 16

    def __post_init__(self):
        for k in ("parameters", "weight_bits", "kv_bits", "activation_bits"):
            finite_positive(k, getattr(self, k))
        for k in ("weight_metadata_fraction", "scratch_gb"):
            finite_positive(k, getattr(self, k), zero_ok=True)
        for k in ("layers", "hidden", "query_heads", "kv_heads", "head_dim", "context", "batch"):
            v = getattr(self, k)
            if type(v) is not int or v <= 0:
                raise ValueError(f"{k} must be a positive integer")
        if self.hidden != self.query_heads * self.head_dim or self.query_heads % self.kv_heads:
            raise ValueError("inconsistent attention geometry")
        if not 0 < self.pre_attention_fraction < 1 or not 0 < self.attention_output_fraction < 1 or self.pre_attention_fraction + self.attention_output_fraction >= 1:
            raise ValueError("invalid dense-operation split")

    @property
    def weight_bytes(self) -> float:
        return self.parameters * self.weight_bits / 8 * (1 + self.weight_metadata_fraction)

    @property
    def kv_bytes_per_token(self) -> float:
        return 2 * self.layers * self.kv_heads * self.head_dim * self.kv_bits / 8

    @property
    def kv_resident_bytes(self) -> float:
        return self.kv_bytes_per_token * self.context * self.batch

    @property
    def kv_resident_after_step_bytes(self) -> float:
        return self.kv_bytes_per_token * (self.context + 1) * self.batch

    @property
    def kv_step_bytes(self) -> float:
        return self.kv_bytes_per_token * (self.context + 1) * self.batch

    @property
    def dense_ops_per_layer(self) -> float:
        return 2 * self.parameters * self.batch / self.layers

    @property
    def attention_ops_per_layer(self) -> float:
        return 4 * self.query_heads * self.head_dim * self.context * self.batch


@dataclass(frozen=True)
class Memory:
    capacity_gb: float
    gb_per_second: float
    banks: int = 16
    transaction_latency_ns: float = 0.0
    sustained_fraction: float = 1.0

    def __post_init__(self):
        finite_positive("capacity_gb", self.capacity_gb)
        finite_positive("gb_per_second", self.gb_per_second)
        finite_positive("transaction_latency_ns", self.transaction_latency_ns, zero_ok=True)
        finite_positive("sustained_fraction", self.sustained_fraction)
        if self.sustained_fraction > 1:
            raise ValueError("sustained_fraction cannot exceed one")
        if type(self.banks) is not int or self.banks < 1:
            raise ValueError("banks must be a positive integer")


@dataclass(frozen=True)
class System:
    name: str
    modules: int
    bulk: Memory
    compute_tops_per_module: float
    fast: Optional[Memory] = None
    weight_fast_fraction: float = 0.0
    kv_fast_fraction: float = 0.0
    compute_fraction: float = 1.0
    fabric_gbs: float = 0.0
    fabric_latency_us: float = 0.0
    collectives_per_layer: int = 2
    tiles_per_phase: int = 16
    bank_mapping: str = "round_robin"  # or hot_bank, an adversarial experiment
    provenance: str = "all throughput parameters hypothetical"

    def __post_init__(self):
        if type(self.modules) is not int or self.modules < 1:
            raise ValueError("modules must be a positive integer")
        if type(self.tiles_per_phase) is not int or self.tiles_per_phase < 1:
            raise ValueError("tiles_per_phase must be a positive integer")
        finite_positive("compute_tops_per_module", self.compute_tops_per_module)
        finite_positive("compute_fraction", self.compute_fraction)
        if self.compute_fraction > 1:
            raise ValueError("compute_fraction exceeds one")
        for name in ("weight_fast_fraction", "kv_fast_fraction"):
            v = getattr(self, name)
            finite_positive(name, v, zero_ok=True)
            if v > 1:
                raise ValueError(f"{name} cannot exceed one")
        for name in ("fabric_gbs", "fabric_latency_us"):
            finite_positive(name, getattr(self, name), zero_ok=True)
        if self.modules > 1 and self.fabric_gbs <= 0:
            raise ValueError("fabric_gbs required for multimodule systems")
        if (self.weight_fast_fraction or self.kv_fast_fraction) and self.fast is None:
            raise ValueError("fast tier required for selected placement")
        if type(self.collectives_per_layer) is not int or self.collectives_per_layer < 0:
            raise ValueError("collectives_per_layer must be nonnegative integer")
        if self.bank_mapping not in ("round_robin", "hot_bank"):
            raise ValueError("unsupported bank mapping")


@dataclass
class _MemoryBank:
    ready_time: float = 0.0


@dataclass
class _Node:
    bulk_banks: list[_MemoryBank]
    fast_banks: list[_MemoryBank]
    compute_ready: float = 0.0


@dataclass
class _Totals:
    bulk_bytes: float = 0.0
    fast_bytes: float = 0.0
    fabric_bytes: float = 0.0
    transactions: int = 0
    fabric_messages: int = 0
    compute_ops: float = 0.0
    traces: list[dict] = field(default_factory=list)


def _bank_index(placement: str, tile: int, count: int) -> int:
    return (tile % count) if placement == "round_robin" else 0


def _read_bank(banks: list[_MemoryBank], tier: Memory, amount: float,
               issue_time: float, tile: int, mapping: str) -> float:
    if amount <= 0:
        return issue_time
    bank = banks[_bank_index(mapping, tile, len(banks))]
    transfer_rate = tier.gb_per_second * GB * tier.sustained_fraction / len(banks)
    done = max(issue_time, bank.ready_time) + tier.transaction_latency_ns * 1e-9 + amount / transfer_rate
    bank.ready_time = done
    return done


def _phase(nodes: list[_Node], system: System, start: float, name: str,
           bulk_bytes_per_node: float, fast_bytes_per_node: float,
           ops_per_node: float, totals: _Totals, *, record: bool) -> float:
    """Tile-level memory-ready -> compute dependency, separate banks per node.

    All transfers are issued at this phase's start in increasing tile order.
    Individual compute tiles can run while later transfers remain outstanding.
    No prefetch across phase or layer barriers. Memory service time includes a
    per-bank serialized latency; this is NOT a DRAM controller model.
    """
    finish = start
    if record:
        reads = []
    for node_id, node in enumerate(nodes):
        for tile in range(system.tiles_per_phase):
            b = bulk_bytes_per_node / system.tiles_per_phase
            f = fast_bytes_per_node / system.tiles_per_phase
            ready_b = _read_bank(node.bulk_banks, system.bulk, b, start, tile, system.bank_mapping)
            ready_f = start
            if f:
                assert system.fast is not None
                ready_f = _read_bank(node.fast_banks, system.fast, f, start, tile, system.bank_mapping)
            data_ready = max(start, ready_b, ready_f)
            compute_start = max(data_ready, node.compute_ready)
            end = compute_start + (ops_per_node / system.tiles_per_phase) / (
                system.compute_tops_per_module * 1e12 * system.compute_fraction)
            node.compute_ready = end
            finish = max(finish, end)
            totals.bulk_bytes += b
            totals.fast_bytes += f
            totals.compute_ops += ops_per_node / system.tiles_per_phase
            totals.transactions += int(b > 0) + int(f > 0)
            if record and node_id == 0 and tile < 2:
                reads.append({"tile": tile, "data_ready_us": round((data_ready-start)*1e6, 4),
                              "compute_finish_us": round((end-start)*1e6, 4)})
    if record:
        totals.traces.append({"phase": name, "elapsed_us": round((finish-start)*1e6, 4),
                              "first_node_tiles": reads})
    return finish


def _collective(system: System, workload: Workload, start: float, totals: _Totals,
                *, record: bool) -> float:
    if system.modules == 1:
        return start
    # All-reduce proxy, not a measured topology: a ring-like volume proxy and
    # log2(N) latency stages across an assumed single aggregate fabric channel.
    bytes_ = workload.hidden * workload.batch * workload.activation_bits / 8 * (system.modules-1)
    delay = system.fabric_latency_us * 1e-6 * math.ceil(math.log2(system.modules))
    delay += bytes_ / (system.fabric_gbs * GB)
    totals.fabric_bytes += bytes_
    totals.fabric_messages += 1
    if record:
        totals.traces.append({"phase": "collective", "elapsed_us": round(delay*1e6, 4)})
    return start + delay


def simulate(workload: Workload, system: System, *, record_first_layer: bool = False) -> dict:
    """Execute one sequential decode step with QKV/attention/O/MLP phases."""
    n = system.modules
    # Head-sharded tensor parallelism only. Reject unsupported head layouts
    # rather than silently assuming fractional heads or zero interconnect cost.
    if workload.query_heads % n != 0 or not (workload.kv_heads % n == 0 or n % workload.kv_heads == 0):
        return {"architecture": system.name, "status": "REJECT_LAYOUT",
                "reason": "tensor-parallel modules cannot evenly map Q/KV heads in this simulator"}
    kv_replication = max(1, n // workload.kv_heads)
    per_node_weight = workload.weight_bytes / n
    per_node_kv_resident = workload.kv_resident_after_step_bytes / min(n, workload.kv_heads)
    fast_resident = per_node_weight * system.weight_fast_fraction + per_node_kv_resident * system.kv_fast_fraction
    bulk_resident = per_node_weight*(1-system.weight_fast_fraction) + per_node_kv_resident*(1-system.kv_fast_fraction) + workload.scratch_gb*GB/n
    out = {"architecture": system.name, "status": "PENDING", "provenance": system.provenance,
           "modules": n, "context": workload.context, "batch": workload.batch,
           "kv_replication": kv_replication, "fast_resident_gb_per_module": round(fast_resident/GB, 6),
           "bulk_resident_gb_per_module": round(bulk_resident/GB, 6),
           "fast_capacity_gb_per_module": system.fast.capacity_gb if system.fast else 0,
           "bulk_capacity_gb_per_module": system.bulk.capacity_gb}
    if bulk_resident > system.bulk.capacity_gb*GB*(1+1e-12) or (
        fast_resident and (system.fast is None or fast_resident > system.fast.capacity_gb*GB*(1+1e-12))):
        out.update(status="REJECT_CAPACITY", reason="per-node residency exceeds memory capacity")
        return out
    nodes = [_Node([_MemoryBank() for _ in range(system.bulk.banks)],
                   [_MemoryBank() for _ in range(system.fast.banks)] if system.fast else []) for _ in range(n)]
    totals = _Totals()
    now = 0.0
    w_l = workload.weight_bytes / workload.layers / n
    kv_l = workload.kv_step_bytes / workload.layers / min(n, workload.kv_heads)
    dense_l = workload.dense_ops_per_layer / n
    attn_l = workload.attention_ops_per_layer / n
    for layer in range(workload.layers):
        record = record_first_layer and layer == 0
        # QKV projection proxy.
        portion = workload.pre_attention_fraction
        now = _phase(nodes, system, now, "pre_attention_projection",
                     w_l*portion*(1-system.weight_fast_fraction),
                     w_l*portion*system.weight_fast_fraction, dense_l*portion, totals, record=record)
        # Attention reads history and writes one new KV element per batch member.
        now = _phase(nodes, system, now, "attention_KV_read_write",
                     kv_l*(1-system.kv_fast_fraction),
                     kv_l*system.kv_fast_fraction, attn_l, totals, record=record)
        # Attention output projection and first tensor-parallel reduction.
        portion = workload.attention_output_fraction
        now = _phase(nodes, system, now, "attention_output_projection",
                     w_l*portion*(1-system.weight_fast_fraction),
                     w_l*portion*system.weight_fast_fraction, dense_l*portion, totals, record=record)
        if system.collectives_per_layer >= 1:
            now = _collective(system, workload, now, totals, record=record)
        # Feed-forward network and second tensor-parallel reduction.
        portion = 1-workload.pre_attention_fraction-workload.attention_output_fraction
        now = _phase(nodes, system, now, "MLP",
                     w_l*portion*(1-system.weight_fast_fraction),
                     w_l*portion*system.weight_fast_fraction, dense_l*portion, totals, record=record)
        for _ in range(max(0, system.collectives_per_layer-1)):
            now = _collective(system, workload, now, totals, record=record)
    out.update({"status": "SIMULATED", "decode_step_ms": round(now*1e3, 6),
               "conditional_steps_per_second": round(1/now, 4),
               "total_bulk_bytes_gb": round(totals.bulk_bytes/GB, 6),
               "total_fast_bytes_gb": round(totals.fast_bytes/GB, 6),
               "total_fabric_bytes_gb": round(totals.fabric_bytes/GB, 9),
               "number_of_memory_transactions": totals.transactions,
               "number_of_collective_operations": totals.fabric_messages,
               "simulated_operations_tops": round(totals.compute_ops/1e12, 6),
               "first_layer_events": totals.traces if record_first_layer else None})
    # Lower bound: useful bytes and OPS cannot exceed aggregate peak resources,
    # and serial layer/model dependencies only increase elapsed time.
    bulk_lower = totals.bulk_bytes / (n*system.bulk.gb_per_second*GB*system.bulk.sustained_fraction)
    fast_lower = (totals.fast_bytes/(n*system.fast.gb_per_second*GB*system.fast.sustained_fraction)
                  if system.fast and totals.fast_bytes else 0.0)
    compute_lower = totals.compute_ops/(n*system.compute_tops_per_module*1e12*system.compute_fraction)
    out["global_roofline_lower_ms"] = round(max(bulk_lower, fast_lower, compute_lower)*1e3, 6)
    if now + 1e-10 < max(bulk_lower, fast_lower, compute_lower):
        raise AssertionError("event simulation beat global resource lower bound")
    return out
