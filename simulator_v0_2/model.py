"""E1 analytical resource/traffic model; NOT a chip simulator or benchmark.

Units: bytes decimal unless GiB explicitly stated; GB/s decimal; TOPS=10**12 ops/s.
Peak-bandwidth results are optimistic conditional upper bounds, not measured speed.
"""
from dataclasses import dataclass
import math

GB = 10**9
GIB = 2**30


def positive(name, value, zero_ok=False):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or (value < 0 if zero_ok else value <= 0):
        raise ValueError(f"{name} must be {'nonnegative' if zero_ok else 'positive'} and finite")


@dataclass(frozen=True)
class DecodeWorkload:
    name: str = 'Qwen2.5-32B-Instruct proxy'
    parameters: float = 32.5e9  # approx., not exact architectural parameter count
    weight_bits: float = 4
    weight_metadata_fraction: float = .10  # scenario assumption
    kv_bits: float = 16
    layers: int = 64
    query_heads: int = 40
    kv_heads: int = 8
    head_dim: int = 128  # hidden_size (5120) / query_heads (40)
    hidden_size: int = 5120
    context: int = 32768
    batch: int = 1
    scratch_gb: float = 2

    def __post_init__(self):
        for key in ('parameters', 'weight_bits', 'kv_bits', 'layers', 'query_heads', 'kv_heads', 'head_dim', 'hidden_size', 'context', 'batch'):
            positive(key, getattr(self, key))
        for key in ('weight_metadata_fraction', 'scratch_gb'):
            positive(key, getattr(self, key), zero_ok=True)
        for key in ('layers', 'query_heads', 'kv_heads', 'head_dim', 'hidden_size', 'context', 'batch'):
            if not isinstance(getattr(self, key), int):
                raise ValueError(f'{key} must be an integer')
        if self.hidden_size != self.query_heads * self.head_dim or self.query_heads % self.kv_heads:
            raise ValueError('Inconsistent attention head geometry')

    @property
    def weight_bytes(self):
        return self.parameters * self.weight_bits / 8 * (1 + self.weight_metadata_fraction)

    @property
    def kv_bytes_per_context_token(self):
        return 2 * self.layers * self.kv_heads * self.head_dim * self.kv_bits / 8

    @property
    def kv_resident_bytes(self):
        return self.kv_bytes_per_context_token * self.context * self.batch

    @property
    def resident_bytes(self):
        return self.weight_bytes + self.kv_resident_bytes + self.scratch_gb * GB

    @property
    def decode_weight_bytes_per_step(self):
        # Across a batched step, weights read once and reused by batch members (ideal).
        return self.weight_bytes

    @property
    def decode_kv_bytes_per_step(self):
        # Read prior K/V and write one new K/V per batch member.
        return self.kv_bytes_per_context_token * (self.context + 1) * self.batch

    @property
    def operations_per_step(self):
        # Approximate dense model forward pass plus QK/AV attention; excludes many operations.
        return self.batch * (2 * self.parameters + 4 * self.layers * self.query_heads * self.head_dim * self.context)


@dataclass(frozen=True)
class Architecture:
    name: str
    modules: int
    bulk_gb_per_module: float
    bulk_gbs_per_module: float
    tops_per_module: float
    fast_gb_per_module: float = 0
    fast_gbs_per_module: float = 0
    weight_fast_fraction: float = 0
    kv_fast_fraction: float = 0
    bandwidth_utilization: float = 1
    compute_utilization: float = 1
    fabric_gbs: float = 0
    fabric_latency_us: float = 0
    collectives_per_layer: int = 2
    assumed_system_watts: float | None = None
    provenance: str = 'hypothetical'

    def __post_init__(self):
        if not isinstance(self.modules, int) or self.modules < 1:
            raise ValueError('modules must be a positive integer')
        for key in ('bulk_gb_per_module', 'bulk_gbs_per_module', 'tops_per_module'):
            positive(key, getattr(self, key))
        for key in ('fast_gb_per_module', 'fast_gbs_per_module', 'fabric_gbs', 'fabric_latency_us'):
            positive(key, getattr(self, key), zero_ok=True)
        for key in ('weight_fast_fraction', 'kv_fast_fraction'):
            v = getattr(self, key)
            if not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
                raise ValueError(f'{key} must be between 0 and 1')
        for key in ('bandwidth_utilization', 'compute_utilization'):
            v = getattr(self, key)
            if not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 < v <= 1:
                raise ValueError(f'{key} must be in (0, 1]')
        if (self.weight_fast_fraction or self.kv_fast_fraction) and (self.fast_gb_per_module == 0 or self.fast_gbs_per_module == 0):
            raise ValueError('Fast memory placement requires nonzero fast capacity and bandwidth')
        if self.modules > 1 and self.fabric_gbs <= 0:
            raise ValueError('Multimodule architecture requires a fabric bandwidth')
        if not isinstance(self.collectives_per_layer, int) or self.collectives_per_layer < 0:
            raise ValueError('collectives_per_layer must be nonnegative integer')
        if self.assumed_system_watts is not None:
            positive('assumed_system_watts', self.assumed_system_watts)


def analyze(workload: DecodeWorkload, arch: Architecture):
    fast_resident = workload.weight_bytes * arch.weight_fast_fraction + workload.kv_resident_bytes * arch.kv_fast_fraction
    bulk_resident = workload.resident_bytes - fast_resident
    fast_cap = arch.modules * arch.fast_gb_per_module * GB
    bulk_cap = arch.modules * arch.bulk_gb_per_module * GB
    w_fast = workload.decode_weight_bytes_per_step * arch.weight_fast_fraction
    kv_fast = workload.decode_kv_bytes_per_step * arch.kv_fast_fraction
    fast_step_bytes = w_fast + kv_fast
    bulk_step_bytes = workload.decode_weight_bytes_per_step + workload.decode_kv_bytes_per_step - fast_step_bytes
    fit = fast_resident <= fast_cap + 1e-6 and bulk_resident <= bulk_cap + 1e-6
    result = {
        'architecture': arch.name, 'provenance': arch.provenance,
        'fits_memory': fit, 'required_total_gb': workload.resident_bytes / GB,
        'fast_resident_gb': fast_resident / GB, 'bulk_resident_gb': bulk_resident / GB,
        'fast_capacity_gb': fast_cap / GB, 'bulk_capacity_gb': bulk_cap / GB,
        'weight_gb': workload.weight_bytes / GB, 'kv_gib': workload.kv_resident_bytes / GIB,
        'fast_bytes_per_step_gb': fast_step_bytes / GB, 'bulk_bytes_per_step_gb': bulk_step_bytes / GB,
        'operations_per_step_tops': workload.operations_per_step / 1e12,
        'optimistic_tokens_per_second': None, 'optimistic_step_ms': None,
        'limiting_resource': None, 'conditional_energy_j_per_token': None,
    }
    if not fit:
        result['status'] = 'REJECT_CAPACITY'
        return result
    t_fast = fast_step_bytes / (arch.modules * arch.fast_gbs_per_module * GB * arch.bandwidth_utilization) if fast_step_bytes else 0
    t_bulk = bulk_step_bytes / (arch.modules * arch.bulk_gbs_per_module * GB * arch.bandwidth_utilization) if bulk_step_bytes else 0
    t_compute = workload.operations_per_step / (arch.modules * arch.tops_per_module * 1e12 * arch.compute_utilization)
    # Deliberately generous to all designs: peak channels and compute fully overlap.
    t_parallel = max(t_fast, t_bulk, t_compute)
    times = {'fast_memory': t_fast, 'bulk_memory': t_bulk, 'compute': t_compute}
    limiting = max(times, key=times.get)
    # Simplified tensor-parallel all-reduce proxy, not a real schedule or topology model.
    # Not imposed on single-module systems. Transfers and messages are serialized after
    # the overlapping compute stage: a deliberately explicit architecture penalty.
    fabric_time = 0.0
    if arch.modules > 1:
        messages = workload.layers * arch.collectives_per_layer
        transfer_bytes = messages * workload.hidden_size * 2 * (arch.modules - 1) * workload.batch
        fabric_time = (transfer_bytes / (arch.fabric_gbs * GB) + messages * arch.fabric_latency_us * 1e-6)
    step_s = t_parallel + fabric_time
    result.update({
        'status': 'CONDITIONAL_ROOFLINE_ONLY',
        'optimistic_step_ms': 1000 * step_s,
        'optimistic_tokens_per_second': workload.batch / step_s,
        'limiting_resource': limiting,
        'fabric_ms': fabric_time * 1000,
        'parallel_ms': t_parallel * 1000,
        'conditional_energy_j_per_token': arch.assumed_system_watts * step_s / workload.batch if arch.assumed_system_watts is not None else None,
    })
    return result


def generic_roofline(operations: float, bytes_transferred: float, resident_gb: float, arch: Architecture):
    """One architecture-neutral AI work unit; separate task quality/semantics not modeled."""
    for name, value in [('operations', operations), ('bytes_transferred', bytes_transferred), ('resident_gb', resident_gb)]:
        positive(name, value, zero_ok=True)
    if resident_gb > arch.modules * arch.bulk_gb_per_module:
        return {'fits_memory': False, 'status': 'REJECT_CAPACITY'}
    compute = operations / (arch.modules * arch.tops_per_module * 1e12 * arch.compute_utilization)
    memory = bytes_transferred / (arch.modules * arch.bulk_gbs_per_module * GB * arch.bandwidth_utilization)
    return {'fits_memory': True, 'status': 'CONDITIONAL_ROOFLINE_ONLY',
            'optimistic_seconds_per_work_unit': max(compute, memory),
            'limiting_resource': 'compute' if compute >= memory else 'bulk_memory'}
