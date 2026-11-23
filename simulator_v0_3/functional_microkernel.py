"""Small *functional* distributed matrix-vector reference, not a fast AI chip.

Illustrates sharded multiply-accumulate and a ring all-reduce. Pure Python;
validated independently against serial matvec. Does not compute transformers.
"""
from __future__ import annotations
import math


def matvec_reference(matrix: list[list[float]], vector: list[float]) -> list[float]:
    if not matrix or not vector or any(len(row) != len(vector) for row in matrix):
        raise ValueError('matrix must be rectangular and match a nonempty vector')
    if any(not math.isfinite(x) for row in matrix for x in row) or any(not math.isfinite(x) for x in vector):
        raise ValueError('nonfinite input')
    return [math.fsum(a*b for a,b in zip(row,vector)) for row in matrix]


def ring_allreduce(partials: list[list[float]]) -> dict:
    """Simulate synchronous ring reduce-scatter + all-gather over equal chunks.

    Each node initially holds a vector of partial sums of equal length. Return
    one fully reduced vector per node; all messages are explicit point-to-point
    logical messages, with no physical latency/energy or actual network.
    """
    n = len(partials)
    if not n or any(len(v) != len(partials[0]) for v in partials):
        raise ValueError('nodes must be nonempty with equal vector lengths')
    width = len(partials[0])
    if not width or width % n:
        raise ValueError('vector length must divide evenly across nodes')
    if any(not math.isfinite(x) for v in partials for x in v):
        raise ValueError('nonfinite partial')
    chunk_width = width // n
    chunks = [[list(v[i*chunk_width:(i+1)*chunk_width]) for i in range(n)]
              for v in partials]
    message_count = 0
    for step in range(n-1):
        packets = [list(chunks[r][(r-step) % n]) for r in range(n)]
        for r in range(n):
            rx_index = (r-step-1) % n
            sender = (r-1) % n
            chunks[r][rx_index] = [a+b for a,b in zip(chunks[r][rx_index],packets[sender])]
            message_count += 1
    # Each node r now owns fully reduced chunk (r+1)%n.
    for step in range(n-1):
        packets = [list(chunks[r][(r+1-step) % n]) for r in range(n)]
        for r in range(n):
            rx_index = (r-step) % n
            chunks[r][rx_index] = packets[(r-1) % n]
            message_count += 1
    return {'vectors': [[x for part in node for x in part] for node in chunks],
            'messages': message_count,
            'transmitted_bytes': message_count*chunk_width*8}  # FP64 reference only


def sharded_matvec(matrix: list[list[float]], vector: list[float], modules: int) -> dict:
    """Shard input columns of matrix; compute partial output per module; ring sum."""
    serial = matvec_reference(matrix, vector)  # independent validation contract
    if type(modules) is not int or modules < 1:
        raise ValueError('invalid modules')
    if len(matrix) % modules:
        raise ValueError('output length must be divisible by modules')
    partials = []
    for node in range(modules):
        partials.append([
            math.fsum(matrix[row][col]*vector[col]
                      for col in range(node,len(vector),modules))
            for row in range(len(matrix))
        ])
    reduced = ring_allreduce(partials)
    actual = reduced['vectors'][0]
    return {'reference': serial, 'distributed': actual,
            'max_abs_error': max(abs(a-b) for a,b in zip(serial,actual)),
            'all_modules_equal': all(all(abs(a-b) <= 1e-10*max(1,abs(b))
                                         for a,b in zip(v,actual))
                                     for v in reduced['vectors']),
            'messages': reduced['messages'], 'transmitted_bytes': reduced['transmitted_bytes']}


def demo():
    # Deterministic small model; no external ML dependencies. Explicit data.
    matrix = [[((r*7+c*3)%17-8)/16 for c in range(12)] for r in range(8)]
    vector = [((c*5)%11-5)/8 for c in range(12)]
    result = sharded_matvec(matrix,vector,4)
    return {'matrix_shape':[8,12], 'modules':4,
            'max_abs_error':result['max_abs_error'], 'all_modules_equal':result['all_modules_equal'],
            'reference_output':result['reference'], 'distributed_output':result['distributed'],
            'ring_messages':result['messages'], 'ring_transmitted_bytes':result['transmitted_bytes']}
