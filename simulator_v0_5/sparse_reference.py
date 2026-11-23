"""Correctness-only demonstrator for exact structural-zero block skipping.

NOT neural inference, not an LLM, not AI model-quality improvement, not an ASIC.
Never confuse a specially crafted sparse matrix with a real dense trained model.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Block:
    block_row:int
    block_col:int
    values:tuple[tuple[float,...],...]


@dataclass(frozen=True)
class Packed:
    rows:int
    cols:int
    block_size:int
    blocks:tuple[Block,...]
    skipped_blocks:int
    index_bytes_per_active:int=4

    @property
    def block_count(self):return self.skipped_blocks+len(self.blocks)
    @property
    def dense_data_bytes(self):return self.rows*self.cols*4
    @property
    def packed_bytes(self):
        # Toy FP32 representation: 4B nonzero block cells, 4B index per
        # surviving block, and >=1bit per possible block in bitmask.
        return len(self.blocks)*(self.block_size**2*4+self.index_bytes_per_active)+math.ceil(self.block_count/8)
    @property
    def saved_fraction(self):return 1-self.packed_bytes/self.dense_data_bytes


def dense_reference(matrix,vector):
    if not matrix or not vector or not all(len(row)==len(vector) for row in matrix):
        raise ValueError('matrix and vector dimensions must agree')
    return [math.fsum(a*b for a,b in zip(row,vector)) for row in matrix]


def pack_exact_zero_blocks(matrix,block_size=8)->Packed:
    if type(block_size) is not int or block_size<1: raise ValueError('block_size integer >0')
    if not matrix or not matrix[0] or not all(len(row)==len(matrix[0]) for row in matrix):
        raise ValueError('rectangular matrix required')
    rows=len(matrix);cols=len(matrix[0]);
    if rows%block_size or cols%block_size:raise ValueError('matrix must align to block boundaries')
    if any(not math.isfinite(v) for row in matrix for v in row):raise ValueError('finite values only')
    blocks=[]; skipped=0
    for i in range(0,rows,block_size):
        for j in range(0,cols,block_size):
            m=tuple(tuple(row[j:j+block_size]) for row in matrix[i:i+block_size])
            if all(v==0 for row in m for v in row):skipped+=1
            else:blocks.append(Block(i//block_size,j//block_size,m))
    return Packed(rows,cols,block_size,tuple(blocks),skipped)


def sparse_exact_mv(packed:Packed, vector):
    if len(vector)!=packed.cols or any(not math.isfinite(v) for v in vector):
        raise ValueError('vector length/values invalid')
    terms=[[] for _ in range(packed.rows)]
    b=packed.block_size
    for block in packed.blocks:
        for di,row in enumerate(block.values):
            ri=block.block_row*b+di
            for dj,w in enumerate(row):
                terms[ri].append((block.block_col*b+dj,w*vector[block.block_col*b+dj]))
    # Preserve column order and use the same numerical reduction rule as dense_reference.
    return [math.fsum(value for col,value in sorted(ts)) for ts in terms]


def demo():
    n=16;b=8
    a=[[0.0 for j in range(n)] for i in range(n)]
    for i in range(8):
        for j in range(8):
            a[i][j]=float((i+3*j)%7+1)
    v=[float(j%5-2) for j in range(n)]
    p=pack_exact_zero_blocks(a,b)
    dense=dense_reference(a,v)
    sparse=sparse_exact_mv(p,v)
    assert dense==sparse
    return {'example':'Constructed 16x16 FP32 matrix, 8x8 block sparsity, 3 zero blocks',
            'dense_weight_bytes':p.dense_data_bytes,'packed_weight_and_metadata_bytes':p.packed_bytes,
            'zero_blocks':p.skipped_blocks,'total_blocks':p.block_count,
            'weight_traffic_saving_fraction':p.saved_fraction,
            'exact_vector_equality':dense==sparse,
            'qualification':'Only a contrived exactly sparse matrix. Real model sparsity and task quality are unverified.'}
