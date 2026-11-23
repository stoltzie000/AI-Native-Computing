"""Independent signed reference; byte traffic model is not measured HBM performance."""
from dataclasses import dataclass
from math import ceil


def signed(v: int, bits: int) -> int:
    if type(v) is not int or bits < 2:
        raise ValueError("signed integer and valid width required")
    v &= (1 << bits) - 1
    return v - (1 << bits) if v & (1 << (bits - 1)) else v


@dataclass(frozen=True)
class Config:
    rows: int = 64
    cols: int = 4
    lanes: int = 4
    data_bits: int = 8
    acc_bits: int = 32
    minimum_burst_bytes: int = 64

    def __post_init__(self):
        nums = (self.rows, self.cols, self.lanes, self.data_bits, self.acc_bits, self.minimum_burst_bytes)
        if any(type(i) is not int for i in nums) or min(nums) <= 0 or self.data_bits < 2:
            raise ValueError("invalid parameter")
        if self.rows > 65535 or self.cols > 65535 or self.rows % self.lanes or self.acc_bits < 2 * self.data_bits:
            raise ValueError("unsupported geometry")


def evaluate(matrix, vector, cfg=Config()):
    if len(matrix) != cfg.rows or len(vector) != cfg.cols or any(len(row) != cfg.cols for row in matrix):
        raise ValueError("bad shape")
    w = [[signed(v, cfg.data_bits) for v in row] for row in matrix]
    x = [signed(v, cfg.data_bits) for v in vector]
    active = [c for c, v in enumerate(x) if v != 0]
    y = [signed(sum(w[r][c] * x[c] for c in range(cfg.cols)), cfg.acc_bits) for r in range(cfg.rows)]
    y_accum = [0] * cfg.rows
    for c in active:
        for base in range(0, cfg.rows, cfg.lanes):
            for lane in range(cfg.lanes):
                r = base + lane
                y_accum[r] = signed(y_accum[r] + w[r][c] * x[c], cfg.acc_bits)
    assert y_accum == y
    per_column_payload = cfg.rows * cfg.data_bits // 8
    if cfg.data_bits % 8:
        per_column_payload = ceil(cfg.rows * cfg.data_bits / 8)
    per_column_transfer = ceil(per_column_payload / cfg.minimum_burst_bytes) * cfg.minimum_burst_bytes
    return {
        "sums": y,
        "active_columns": active,
        "requests": len(active),
        "fetched_weights": len(active) * cfg.rows,
        "skipped_weights": (cfg.cols - len(active)) * cfg.rows,
        "mac_cycles": len(active) * cfg.rows // cfg.lanes,
        "useful_bytes": len(active) * per_column_payload,
        "conditional_burst_bytes": len(active) * per_column_transfer,
        "burst_utilization": len(active) * per_column_payload / (len(active) * per_column_transfer) if active else None,
    }


def tile_comparison(rows=64, cols=4, active_cols=2, lanes=4, min_burst=64):
    """Same matrix/activation, different physical row tile sizes."""
    if rows < 1 or cols < 1 or not 0 <= active_cols <= cols:
        raise ValueError("invalid workload")
    answer = []
    for tile_rows in (4, 8, 16, 32, 64):
        if rows % tile_rows:
            continue
        reqs = (rows // tile_rows) * active_cols
        useful = active_cols * rows
        transfer = reqs * ceil(tile_rows / min_burst) * min_burst
        answer.append({"tile_rows": tile_rows, "requests": reqs, "useful_weight_bytes": useful,
                       "conditional_transfer_bytes": transfer,
                       "active_compute_cycles": active_cols * rows // lanes,
                       "conditional_utilization": useful / transfer if transfer else None})
    return answer
