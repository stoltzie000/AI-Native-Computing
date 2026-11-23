"""Independent reference for exact-zero activation-gated matrix-vector processing.
Arithmetic only; not measured RTL or hardware performance.
"""
from dataclasses import dataclass

def signed(value: int, bits: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or bits < 2:
        raise ValueError("invalid signed integer or width")
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >= (1 << (bits - 1)) else value

@dataclass(frozen=True)
class Config:
    size: int = 4
    data_bits: int = 8
    accum_bits: int = 32

    def __post_init__(self):
        if self.size < 1 or self.size > 65535 or self.data_bits < 2 or self.accum_bits < 2 * self.data_bits:
            raise ValueError("invalid PE configuration")

def evaluate(weights, vector, config: Config = Config()):
    n = config.size
    if len(weights) != n or len(vector) != n or any(len(row) != n for row in weights):
        raise ValueError("invalid matrix/vector shape")
    w = [[signed(x, config.data_bits) for x in row] for row in weights]
    x = [signed(value, config.data_bits) for value in vector]
    values = [signed(sum(weight * activation for weight, activation in zip(row, x)), config.accum_bits) for row in w]
    active_columns = sum(value != 0 for value in x)
    requested_coordinates = [(row, col) for row in range(n) for col in range(n) if x[col] != 0]
    return {
        "sums": values,
        "active_columns": active_columns,
        "dense_reads": n * n,
        "requested_reads": len(requested_coordinates),
        "skipped_reads": n * n - len(requested_coordinates),
        "requested_coordinates": requested_coordinates,
        "arithmetic_multiplies": len(requested_coordinates),
        "weight_bytes_saved": (n * n - len(requested_coordinates)) * config.data_bits / 8,
    }
