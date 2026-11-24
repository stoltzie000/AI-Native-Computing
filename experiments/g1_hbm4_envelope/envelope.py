"""G1.4 HBM4 controller/data-pin analytical feasibility screen (E1 only).

A nominal data-rate calculation does not establish a compatible physical PHY,
achieved bandwidth, package layout, power, cooling or a GPU benchmark.
SI decimal GB/GB/s throughout; no hidden GiB conversion.
"""
from dataclasses import dataclass
import json
import math


def positive(name: str, x: int | float, *, zero: bool = False) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{name}: finite number required")
    if x < 0 if zero else x <= 0:
        raise ValueError(f"{name}: invalid nonnegative/positive value")
    return float(x)


@dataclass(frozen=True)
class ControllerEnvelope:
    stacks: int
    capacity_gb_per_stack: float
    data_pins_per_stack: int
    controller_gbps_per_pin: float
    usable_fraction: float | None = None
    reserved_capacity_fraction: float | None = None
    measured_achieved_bandwidth_gb_s: float | None = None

    def __post_init__(self):
        if type(self.stacks) is not int or self.stacks < 1:
            raise ValueError("stacks positive integer")
        if type(self.data_pins_per_stack) is not int or self.data_pins_per_stack < 1:
            raise ValueError("data_pins_per_stack positive integer")
        positive("capacity_gb_per_stack", self.capacity_gb_per_stack)
        positive("controller_gbps_per_pin", self.controller_gbps_per_pin)
        for name in ("usable_fraction", "reserved_capacity_fraction"):
            v = getattr(self, name)
            if v is not None:
                positive(name, v, zero=(name == "reserved_capacity_fraction"))
                if v > 1: raise ValueError(name + ": must be <= 1")
        if self.measured_achieved_bandwidth_gb_s is not None:
            positive("measured_achieved_bandwidth_gb_s", self.measured_achieved_bandwidth_gb_s)

    def screen(self, *, weight_traffic_gb: float, state_traffic_gb: float,
               resident_gb: float | None = None) -> dict:
        weights = positive("weight_traffic_gb", weight_traffic_gb, zero=True)
        state = positive("state_traffic_gb", state_traffic_gb, zero=True)
        total = weights + state
        if total == 0: raise ValueError("traffic must be positive")
        capacity = self.stacks * self.capacity_gb_per_stack
        raw = self.stacks * self.data_pins_per_stack * self.controller_gbps_per_pin / 8
        # One Gbit/s converts to 1/8 GB/s, both SI.
        if resident_gb is not None:
            positive("resident_gb", resident_gb, zero=True)
        assumed_usable_capacity = None
        status = "BLOCK_RESIDENCY_AND_PACKAGE_FEASIBILITY_UNKNOWN"
        if self.reserved_capacity_fraction is not None:
            assumed_usable_capacity = capacity * (1 - self.reserved_capacity_fraction)
            if resident_gb is not None:
                status = ("REJECT_ASSUMED_CAPACITY" if resident_gb > assumed_usable_capacity
                          else "UNVERIFIED_PHY_PACKAGE_AND_THERMAL")
        useful_rate = raw * self.usable_fraction if self.usable_fraction is not None else None
        if self.measured_achieved_bandwidth_gb_s is not None:
            # A raw controller headline is an envelope; external measured data
            # greater than this envelope indicates configuration mismatch.
            if self.measured_achieved_bandwidth_gb_s > raw * (1 + 1e-9):
                raise ValueError("measured throughput exceeds stated controller interface")
        return {
            "evidence_class": "E1_ANALYTICAL_CONDITIONAL_NOT_HARDWARE",
            "stack_count": self.stacks,
            "nominal_capacity_gb": capacity,
            "hbm_data_pins_at_package_boundary": self.stacks * self.data_pins_per_stack,
            "controller_peak_gb_s": raw,
            "controller_peak_tb_s": raw / 1000,
            "bytes_traffic_gb_per_step": total,
            "memory_only_min_time_ms_at_peak": 1000 * total / raw,
            "memory_only_max_steps_per_s_at_peak": raw / total,
            "assumed_usable_capacity_gb": assumed_usable_capacity,
            "capacity_status": status,
            "assumed_fraction_not_measured": self.usable_fraction,
            "scenario_bandwidth_gb_s": useful_rate,
            "memory_only_scenario_steps_per_s": useful_rate / total if useful_rate is not None else None,
            "memory_only_scenario_time_ms": 1000 * total / useful_rate if useful_rate is not None else None,
            "actual_measurement_supplied": self.measured_achieved_bandwidth_gb_s is not None,
            "actual_achieved_bandwidth_gb_s": self.measured_achieved_bandwidth_gb_s,
            "physical_gate": "OPEN_PDK_PHY_PACKAGE_IO_POWER_THERMAL_UNMEASURED",
            "strict_assumptions": [
                "SI decimal GB; controller data-pin math only, not verified sustained HBM bandwidth",
                "All indicated bytes counted exactly once; excludes metadata/cacheline/refresh and compute/PHY/interconnect overhead",
                "HBM data pins are on-package/stack connections, never board/backplane serial lanes",
                "No QACT/FP32/runtime/network or complete-system power modeled",
                "The assumed usable fraction is not observed silicon data",
                "No AI task-quality or GPU timing/energy comparability established",
            ],
        }


def research_example() -> dict:
    # Published *independent* component specifications. Combination/assembly
    # is hypothetical, not a physically proven platform.
    base = ControllerEnvelope(8, 36, 2048, 10)
    assumed = ControllerEnvelope(8, 36, 2048, 10, usable_fraction=0.70,
                                 reserved_capacity_fraction=0.10)
    traffic = dict(weight_traffic_gb=17.875, state_traffic_gb=8.590)
    original = base.screen(**traffic)
    scenario = assumed.screen(**traffic)
    vendor_rubin_peak_gb_s = 22_000  # vendor specification, not measurement
    return {
        "baseline": "Rubin nominal HBM4 vendor spec: 288GB, 22TB/s; no actual benchmark",
        "proposed_hypothesis": "Eight separate 36GB HBM4 stacks using nominal 10Gb/s Rambus-class 2048-bit controller(s)",
        "published_sources": [
            "https://www.micron.com/products/memory/hbm/hbm4",
            "https://go.rambus.com/hbm4-controller-product-brief",
            "https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/",
        ],
        "controller_spec_envelope": original,
        "assumed_70pct_scenario": scenario,
        "rubin_peak_comparator_only": {
            "vendor_peak_tb_s": vendor_rubin_peak_gb_s / 1000,
            "controller_peak_fraction_of_vendor_peak": original["controller_peak_gb_s"] / vendor_rubin_peak_gb_s,
            "rubin_memory_only_ceiling_steps_per_s_at_peak_for_same_proxy_bytes":
                vendor_rubin_peak_gb_s / original["bytes_traffic_gb_per_step"],
            "gpu_measured_tokens_per_second": None,
            "quality_matched": False,
        },
        "decision": "NO_ACCEPTANCE: A controller interface nominal peak plus HBM capacity cannot establish whole-system feasibility or superiority",
    }


if __name__ == "__main__":
    print(json.dumps(research_example(), sort_keys=True, indent=2))
