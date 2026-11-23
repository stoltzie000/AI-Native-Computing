"""Memory-only silicon area lower bound, not a floorplan or yield estimator.

Default 38.1 Mbit/mm^2: TSMC 2025 reported 2nm high-density SRAM macro.
Memory GB are decimal bytes; 1 byte = 8 bits. No logic/PHY/routing included.
"""
from model import positive, GB


def min_sram_area_mm2(capacity_gb: float, macro_density_mbit_per_mm2: float = 38.1) -> float:
    positive('capacity_gb', capacity_gb)
    positive('macro_density_mbit_per_mm2', macro_density_mbit_per_mm2)
    return capacity_gb * GB * 8 / (macro_density_mbit_per_mm2 * 1e6)


def reticle_footprint_equivalents(capacity_gb: float, macro_density_mbit_per_mm2: float = 38.1,
                                  exposure_field_mm2: float = 858) -> float:
    positive('exposure_field_mm2', exposure_field_mm2)
    return min_sram_area_mm2(capacity_gb, macro_density_mbit_per_mm2) / exposure_field_mm2


if __name__ == '__main__':
    for gb in (12, 48):
        print(f'{gb} GB SRAM: >= {min_sram_area_mm2(gb):,.0f} mm^2 memory macro area; '
              f'>= {reticle_footprint_equivalents(gb):.2f} conventional reticle areas (memory only)')
