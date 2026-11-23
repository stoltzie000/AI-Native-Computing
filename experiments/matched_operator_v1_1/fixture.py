"""Frozen mathematical contract and generated test vectors for equal-work comparisons.

Contract V1: signed INT8 W[64,4] @ signed INT8 x[4], exact signed INT32 y[64].
Float32 is exact for this *particular* 4-term int8 product range, not in general.
No physical memory, timing, precision or energy comparison is implied here.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import argparse
import json
from pathlib import Path
from random import Random

ROWS = 64
COLS = 4
VERSION = 'shared-int8-matvec-v1'
SEED = 0x5A19A123


def exact_oracle(weights: list[list[int]], vector: list[int]) -> list[int]:
    if len(weights) != ROWS or any(len(row) != COLS for row in weights) or len(vector) != COLS:
        raise ValueError('invalid fixed workload shape')
    if any(type(v) is not int or v < -128 or v > 127 for row in weights for v in row + []) or any(type(v) is not int or v < -128 or v > 127 for v in vector):
        raise ValueError('input outside signed INT8')
    return [sum(weights[r][c] * vector[c] for c in range(COLS)) for r in range(ROWS)]


def make_cases() -> dict:
    rng = Random(SEED)
    # Fixed positive and negative controls. No pretrained-model distribution claims.
    specs = [
        ('dense_random', lambda i: rng.choice(tuple(range(-128, 0)) + tuple(range(1,128))), [-91, 127, -128, 17]),
        ('dense_all_positive', lambda i: rng.randint(1, 127), [127, 1, 65, 5]),
        ('dense_negative', lambda i: rng.randint(-128, -1), [-128, -12, -3, -1]),
        ('dense_extremes', lambda i: (-128 if i % 2 == 0 else 127), [127, -128, 127, -128]),
        ('all_zero_vector', lambda i: rng.randrange(-128,128), [0, 0, 0, 0]),
        ('one_active', lambda i: rng.randrange(-128,128), [0, -128, 0, 0]),
        ('half_active', lambda i: rng.randrange(-128,128), [0, 27, 0, -41]),
        ('three_active', lambda i: rng.randrange(-128,128), [18, 0, -32, 111]),
        ('mixed_zero_weights', lambda i: (0 if i % 3 == 0 else rng.randrange(-128,128)), [-20, 41, -13, 27]),
        ('dense_unit', lambda i: (1 if i % 7 else -1), [1, 1, 1, 1]),
        ('dense_random_two', lambda i: rng.choice((-128, -1, 1, 127)), [-127, 3, -17, 22]),
    ]
    cases=[]
    for name, fn, x in specs:
        w=[[fn(r*COLS+c) for c in range(COLS)] for r in range(ROWS)]
        y=exact_oracle(w,x)
        cases.append({'name':name,'weights_row_major':w,'vector':x,'expected_int32':y,
                      'active_cols':sum(v != 0 for v in x)})
    return {'contract':VERSION,'rows':ROWS,'cols':COLS,'seed':SEED,'cases':cases}


def canonical(data:dict)->bytes:
    return (json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')


def write_memh(artifact: dict, dst: Path)->dict:
    dst.mkdir(parents=True,exist_ok=True)
    m={}
    for case in artifact['cases']:
        name=case['name']
        w=case['weights_row_major']
        # One packed column at a time: col*ROWS+row.
        weights=[w[r][c]&255 for c in range(COLS) for r in range(ROWS)]
        input_bytes=[a&255 for a in case['vector']]
        y=[v&0xFFFFFFFF for v in case['expected_int32']]
        for key,values,width in [('weights',weights,2),('vector',input_bytes,2),('expected',y,8)]:
            filename=dst/f'{name}_{key}.hex'
            filename.write_text(''.join(f'{v:0{width}x}\n' for v in values),encoding='ascii')
            m[f'{name}_{key}']=sha256(filename.read_bytes()).hexdigest()
    return m


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    x=make_cases()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'fixtures.json').write_bytes(canonical(x))
    hashes=write_memh(x,a.out/'memh')
    result={'contract':VERSION,'case_count':len(x['cases']),
            'fixture_sha256':sha256(canonical(x)).hexdigest(),'hex_file_sha256':hashes,
            'evidence':'deterministic synthetic mathematical fixture only'}
    (a.out/'manifest.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('GENERATED_SHARED_OPERATOR_FIXTURES',result['case_count'],result['fixture_sha256'])

if __name__=='__main__':main()
