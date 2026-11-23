"""Exact signed matrix-vector oracle and request-level column-major layout model."""
from dataclasses import dataclass

def signed(x,bits):
    if not isinstance(x,int) or isinstance(x,bool) or bits<2:raise ValueError("integer required")
    v=x&((1<<bits)-1)
    return v-(1<<bits) if v&(1<<(bits-1)) else v

@dataclass(frozen=True)
class Config:
    n:int=4
    bits:int=8
    accum_bits:int=32
    def __post_init__(self):
        if not isinstance(self.n,int) or self.n<1 or self.bits<2 or self.accum_bits<2*self.bits:
            raise ValueError("invalid geometry")

def run_dense_and_column_fetch(rows,inputs,cfg=Config()):
    n=cfg.n
    if len(rows)!=n or len(inputs)!=n or any(len(r)!=n for r in rows):
        raise ValueError("shape mismatch")
    a=[signed(x,cfg.bits) for x in inputs]
    w=[[signed(value,cfg.bits) for value in row] for row in rows]
    column_major=[w[r][col] for col in range(n) for r in range(n)]
    active=[col for col in range(n) if a[col]]
    expected=[signed(sum(w[r][col]*a[col] for col in range(n)),cfg.accum_bits) for r in range(n)]
    out=[0]*n
    for col in active:
        for r in range(n):
            out[r]=signed(out[r]+column_major[col*n+r]*a[col],cfg.accum_bits)
    assert out==expected
    return {
        "sums":out,
        "column_major":column_major,
        "requested_columns":active,
        "column_requests":len(active),
        "elementwise_requests":n*len(active),
        "fetched_weights":n*len(active),
        "skipped_weights":n*n-n*len(active)
    }

def transferred_bytes(n,active_columns,bytes_per_weight=1,minimum_transaction_bytes=1):
    if n<1 or active_columns<0 or active_columns>n or bytes_per_weight<1 or minimum_transaction_bytes<1:
        raise ValueError("invalid memory granularity")
    payload=n*bytes_per_weight
    # Explicit pessimistic case: every request transfers at least one burst.
    return {
        "column_fetch_bytes":active_columns*max(payload,minimum_transaction_bytes),
        "element_fetch_bytes":active_columns*n*max(bytes_per_weight,minimum_transaction_bytes),
        "useful_weight_bytes":active_columns*payload
    }
