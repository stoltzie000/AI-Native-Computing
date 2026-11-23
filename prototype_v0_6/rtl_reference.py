"""Independent small signed-INT arithmetic reference and PE cycle schedule.

Not a Verilog compiler. Provides a portable functional oracle while RTL
simulation must separately verify the actual Verilog implementation.
"""
from __future__ import annotations

def signed8(v):
    if not isinstance(v,int) or v < -128 or v > 255:raise ValueError('invalid int8 value')
    v=v&255
    return v-256 if v&128 else v


def dense(rows,vector):
    if len(rows)!=4 or len(vector)!=4 or any(len(row)!=4 for row in rows):
        raise ValueError('4x4 matvec only')
    return [sum(signed8(a)*signed8(b) for a,b in zip(row,vector)) for row in rows]


def step_reference(rows,vector,block_valid):
    if not isinstance(block_valid,bool):raise ValueError('block_valid boolean')
    if not block_valid and any(signed8(v)!=0 for row in rows for v in row):
        raise ValueError('invalid skip: nonzero weights')
    if block_valid:
        result=dense(rows,vector)
        return {'sums':result,'multiplies':16,'compute_cycles':16,
                'controller_cycles_from_start_to_done':18,
                'interpretation':'cycle expectation for simple one-multiply-per-clock PE'}
    return {'sums':[0]*4,'multiplies':0,'compute_cycles':0,
            'controller_cycles_from_start_to_done':2,
            'interpretation':'zero-block skip metadata certified externally'}


def fixture():
    rows=[list(range(i*4+1,i*4+5)) for i in range(4)]
    vector=[2,-1,3,0]
    return {'matrix':rows,'vector':vector,'expected':step_reference(rows,vector,True)}
