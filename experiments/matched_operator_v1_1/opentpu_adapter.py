"""Run one exact mathematical contract on *real pinned* openTPU ISA/RTL VPU.

Crucial: This uses openTPU's FP32 VOP multiply/reduce, NOT its MXU quantized MM.
The 4-term signed INT8 matvec is exactly representable in FP32. This is a
functional common-workload contract only, NOT speed, lane, or DRAM parity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from fixture import ROWS, COLS, VERSION, canonical, exact_oracle


def program_and_dram(case):
    from opentpu import Config, isa as I
    weights = np.asarray(case['weights_row_major'], dtype=np.float32)
    activations = np.asarray(case['vector'], dtype=np.float32)
    dram = np.zeros(8192, dtype=np.uint8)
    dram[:ROWS*COLS*4] = weights.view(np.uint8).reshape(-1)
    dram[4096:4096+COLS*4] = activations.view(np.uint8).reshape(-1)
    # VOP MUL supports column-broadcast from x across the 64 rows.
    # RSUM reduces the four FP32 products to one result per row.
    program = [
        I.ld(0, 0, ROWS*COLS),
        I.ld(4096, 320, COLS),
        I.vop(I.V_MUL, 512, 0, 320, ROWS, COLS, COLS, COLS, 0, I.B_COL),
        I.vop(I.V_RSUM, 1024, 512, 0, ROWS, COLS, 1, COLS, 0),
        I.halt(),
    ]
    return Config(S=1), program, dram


def execute(case, backend='isa'):
    from opentpu.isasim import Machine
    cfg, program, dram = program_and_dram(case)
    if backend == 'isa':
        s = Machine(cfg, [program], [dram]).run().slices[0]
        output = s.tget(1024 + np.arange(ROWS)).copy()
    elif backend == 'rtl':
        from opentpu import rtlsim
        _,tmems,_ = rtlsim.run(cfg, [program], [dram])
        output = np.asarray(tmems[0], dtype=np.uint32)[1024:1024+ROWS].view(np.float32)
    else:
        raise ValueError('invalid backend')
    if not np.all(np.isfinite(output)):
        raise AssertionError('Non-finite result produced')
    # FP32 is exactly equal to the signed int32 sum on this deliberately
    # bounded 4-column workload (no overflow, no rounding in multiplications).
    expected = np.asarray(exact_oracle(case['weights_row_major'],case['vector']), dtype=np.float32)
    if not np.array_equal(output, expected):
        idx=np.flatnonzero(output!=expected)
        raise AssertionError(f"{case['name']} {backend}: mismatch rows={idx[:8].tolist()} got={output[idx[:8]].tolist()} expected={expected[idx[:8]].tolist()}")
    return {'name':case['name'],'backend':backend,'rows':ROWS,'cols':COLS,
            'output_sha256_int32': hashlib.sha256(np.asarray(output,dtype='<i4').tobytes()).hexdigest(),
            'same_exact_integer_outputs':True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--fixtures',type=Path,required=True)
    p.add_argument('--backend',choices=['isa','rtl'],default='isa')
    p.add_argument('--rtl-cases',default='dense_random,half_active,all_zero_vector')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    data=json.loads(a.fixtures.read_text(encoding='utf-8'))
    if data['contract']!=VERSION or data['rows']!=ROWS or data['cols']!=COLS:
        raise ValueError('wrong common workload contract')
    cases=data['cases']
    if a.backend=='rtl':
        names=set(a.rtl_cases.split(','))
        cases=[c for c in cases if c['name'] in names]
        if len(cases)!=len(names):raise ValueError('missing named RTL fixture')
    results=[execute(c,a.backend) for c in cases]
    output={'contract':VERSION,'source':'FeSens/openTPU pinned external source',
            'operator':'openTPU FP32 VOP multiply+reduce, not openTPU quantized MXU MM',
            'backend':a.backend,'passed':len(results),'cases':results,
            'physical_hardware':False,'latency_comparison':False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('PASS_SHARED_OPENTPU_'+a.backend.upper(),len(results))

if __name__=='__main__':main()
