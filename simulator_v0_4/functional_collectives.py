"""CPU-only mathematical oracle for the recursive-doubling communication pattern.

This code verifies the arithmetic dataflow, not accelerator performance,
physical routes, signal integrity, or precision behavior of a future chip.
"""
import math
import random


def recursive_doubling_sum(shards):
    n=len(shards)
    if n<2 or n&(n-1):
        raise ValueError('power-of-two node count >=2 required')
    width=len(shards[0])
    if width<1 or any(len(v)!=width for v in shards):
        raise ValueError('nonempty equal-width vectors required')
    state=[list(v) for v in shards]
    messages=0
    for step in range(n.bit_length()-1):
        snapshot=[row[:] for row in state]
        for i in range(n):
            peer=i^(1<<step)
            state[i]=[a+b for a,b in zip(snapshot[i],snapshot[peer])]
            messages+=1
    return state,messages


def demo(seed=43):
    rng=random.Random(seed)
    shards=[[rng.uniform(-3,3) for _ in range(17)] for _ in range(8)]
    state,messages=recursive_doubling_sum(shards)
    expected=[math.fsum(v[i] for v in shards) for i in range(17)]
    error=max(abs(a-b) for row in state for a,b in zip(row,expected))
    return {'nodes':8,'vector_width':17,'messages':messages,
            'max_absolute_error':error,'reference':'math.fsum across 8 independently generated shards',
            'label':'CPU-only numerical demonstration, not silicon'}
