"""Read-only exact-zero block audit for little-endian safetensors 2D tensors.

Numpy is required. Does not transform weights or test output quality.
"""
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import numpy as np

# Read by unsigned bit representation: sign-bit-only float patterns are +/-0.
TYPE_INFO = {
    'F16': ('<u2', 2, 0x7FFF), 'BF16': ('<u2', 2, 0x7FFF),
    'F32': ('<u4', 4, 0x7FFFFFFF), 'F64': ('<u8', 8, 0x7FFFFFFFFFFFFFFF),
    'I8': ('u1', 1, None), 'U8': ('u1', 1, None),
    'I16': ('<u2', 2, None), 'U16': ('<u2', 2, None),
    'I32': ('<u4', 4, None), 'U32': ('<u4', 4, None),
    'I64': ('<u8', 8, None), 'U64': ('<u8', 8, None),
}


def header_and_data(mm):
    if len(mm) < 10: raise ValueError('too small to be a safetensors file')
    header_size=struct.unpack_from('<Q',mm,0)[0]
    if not 2 <= header_size <= 100_000_000 or 8+header_size>len(mm):
        raise ValueError('invalid safetensors header length')
    try: header=json.loads(mm[8:8+header_size])
    except (UnicodeError,json.JSONDecodeError) as exc: raise ValueError('invalid header JSON') from exc
    if not isinstance(header,dict):raise ValueError('header root must be an object')
    return header,8+header_size


def tensor_stats(mm,data_start,info,block_sizes):
    dtype=info['dtype']; shape=info['shape']; offsets=info['data_offsets']
    if dtype not in TYPE_INFO:return {'status':'unsupported_dtype','dtype':dtype}
    if not isinstance(shape,list) or not all(type(x) is int and x >= 0 for x in shape):
        raise ValueError('bad tensor shape')
    if not isinstance(offsets,list) or len(offsets)!=2 or not all(type(x) is int and x>=0 for x in offsets):
        raise ValueError('bad tensor offset')
    spec,byte_width,mask=TYPE_INFO[dtype]
    total=int(np.prod(shape,dtype=object))
    if offsets[1]-offsets[0]!=total*byte_width or data_start+offsets[1]>len(mm) or offsets[1]<offsets[0]:
        raise ValueError('tensor offsets inconsistent with dimensions')
    if len(shape)!=2:return {'status':'skipped_nonmatrix','dtype':dtype,'shape':shape}
    rows,cols=shape
    if rows==0 or cols==0:return {'status':'skipped_empty_matrix','dtype':dtype,'shape':shape}
    # Constant-bounded chunk memory: at most largest block height x matrix width.
    max_b=max(block_sizes)
    counts={b:{'eligible_blocks':(rows//b)*(cols//b),'zero_blocks':0,
               'eligible_elements':(rows//b)*(cols//b)*b*b,
               'incomplete_edge_elements':rows*cols-(rows//b)*(cols//b)*b*b} for b in block_sizes}
    zero_elements=0
    start=data_start+offsets[0]
    # Iterate by every row to avoid double-counting when block sizes differ.
    for r0 in range(0,rows,max_b):
        rh=min(max_b,rows-r0)
        a=np.frombuffer(mm,dtype=np.dtype(spec),count=rh*cols,
                        offset=start+r0*cols*byte_width).reshape(rh,cols)
        nonzero=(a&mask)!=0 if mask is not None else a!=0
        zero_elements+=int(nonzero.size-np.count_nonzero(nonzero))
        for b in block_sizes:
            full_col=(cols//b)*b
            # A chunk may cross a block boundary for a b that does not divide max_b.
            # Evaluate complete b-row bands independently using the same shared buffer.
            for relative in range(0,rh,b):
                if (r0+relative)%b!=0 or relative+b>rh or full_col==0:continue
                window=nonzero[relative:relative+b,:full_col]
                any_values=window.reshape(b,full_col//b,b).any(axis=(0,2))
                counts[b]['zero_blocks']+=int(any_values.size-np.count_nonzero(any_values))
    out={'status':'measured','dtype':dtype,'shape':shape,'elements':rows*cols,
         'zero_elements':zero_elements,'zero_element_fraction':zero_elements/(rows*cols),
         'blocks':{str(b):{**counts[b], 'zero_block_fraction':
                 counts[b]['zero_blocks']/counts[b]['eligible_blocks'] if counts[b]['eligible_blocks'] else None}
                 for b in block_sizes}}
    return out


def audit(path,blocks=(4,8),compute_sha256=True):
    blocks=tuple(sorted(set(blocks)))
    if not blocks or any(type(b)!=int or b<1 for b in blocks) or any(max(blocks)%b for b in blocks):
        raise ValueError('block sizes must be positive, nested divisors e.g. 4,8')
    p=Path(path)
    with p.open('rb') as f:
        with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
            header,data_start=header_and_data(mm)
            result={'file_name':p.name,'file_size_bytes':len(mm),
                    'file_sha256':hashlib.sha256(mm).hexdigest() if compute_sha256 else None,
                    'block_sizes':list(blocks),'tensors':{},'notes':[
                    'Measured exact binary zero values only; no model-quality inference.',
                    'Partial edge blocks are excluded from block fractions.',
                    'Fast local chunking is row-aligned; use nested divisor block sizes.'
                    ]}
            for name,info in sorted(header.items()):
                if name=='__metadata__':continue
                if not isinstance(info,dict):raise ValueError('invalid tensor entry')
                result['tensors'][name]=tensor_stats(mm,data_start,info,blocks)
            measured=[v for v in result['tensors'].values() if v['status']=='measured']
            total_elems=sum(v['elements'] for v in measured)
            total_zeros=sum(v['zero_elements'] for v in measured)
            by_block={}
            for b in blocks:
                key=str(b)
                eligible=sum(v['blocks'][key]['eligible_blocks'] for v in measured)
                zeros=sum(v['blocks'][key]['zero_blocks'] for v in measured)
                by_block[key]={'eligible_blocks':eligible,'zero_blocks':zeros,
                               'zero_block_fraction':zeros/eligible if eligible else None}
            result['aggregate']={'measured_matrix_tensors':len(measured),
                                 'elements':total_elems,'zero_elements':total_zeros,
                                 'zero_element_fraction':total_zeros/total_elems if total_elems else None,
                                 'blocks':by_block}
            return result


def main():
    parser=argparse.ArgumentParser(description='Read-only pretrained-model block zero audit')
    parser.add_argument('safetensors',help='Existing .safetensors file path')
    parser.add_argument('--blocks',default='4,8',help='Comma separated nested block sizes')
    parser.add_argument('--no-sha256',action='store_true')
    args=parser.parse_args()
    sizes=tuple(int(x) for x in args.blocks.split(','))
    print(json.dumps(audit(args.safetensors,sizes,not args.no_sha256),indent=2,sort_keys=True))
if __name__=='__main__':main()
