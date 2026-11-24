"""Independent integer portion of openTPU WF=0 INT8 MM, D=32 KB=2.

No floating point or openTPU import here. The shared quantization step is executed
by upstream openTPU in adapter.py, so this does NOT independently validate QACT.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    accumulators: tuple[int, ...]
    dropped_groups: int
    group_count: int
    signed_products: int


def grouped_acc(q: list[int], w: list[list[int]], da: list[int], dw: list[list[int]]) -> Result:
    """Return exact signed integer accumulators (one activation row, N weight rows).

    INT8 codes q[64], w[N][64]; da[8] per 8 inputs; dw[N][2] per 32.
    Each group C=sum(q[i]*w[n][i]), shift=16-dw[n][k]-da[g].
    If shift<0 drop the group; otherwise accumulate C<<shift, with no
    intermediate 32-bit narrowing. Source: upstream docs/isa.md MM WF=0.
    """
    if len(q) != 64 or len(da) != 8 or len(w) < 1 or len(dw) != len(w):
        raise ValueError("expected 64 inputs, 8 offsets and at least one weight row")
    if any(len(row) != 64 for row in w) or any(len(row) != 2 for row in dw):
        raise ValueError("matrix/offset shapes mismatch")
    if any(type(x) is not int or x < -128 or x > 127 for x in q):
        raise ValueError("activation codes must be signed int8")
    if any(type(x) is not int or x < -128 or x > 127 for row in w for x in row):
        raise ValueError("weight codes must be signed int8")
    if any(type(x) is not int or not 0 <= x <= 31 for x in da):
        raise ValueError("activation group offsets must be in [0,31]")
    if any(type(x) is not int or not 0 <= x <= 31 for row in dw for x in row):
        raise ValueError("weight block offsets must be in [0,31]")
    acc = []
    dropped = 0
    for row_idx, weight in enumerate(w):
        total = 0
        for g in range(8):
            c = sum(q[8*g+i] * weight[8*g+i] for i in range(8))
            shift = 16 - dw[row_idx][g//4] - da[g]
            if shift < 0:
                dropped += 1
            else:
                total += c * (1 << shift)
        if not -(1 << 47) <= total < (1 << 47):
            raise OverflowError("expected a signed 48-bit exact integer")
        acc.append(total)
    return Result(tuple(acc), dropped, len(w)*8, len(w)*64)
