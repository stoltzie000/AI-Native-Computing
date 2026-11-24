"""G1.2: compare independent exact-int core with genuine openTPU QACT + MM.

Upstream commit is pinned by the workflow. No independent validation of upstream
quantizer's FP32 reciprocal or on-chip memory read order is claimed. This
experiment exercises the actual upstream ISA MM and verifies numerical outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from exact_core import grouped_acc

N, M, K, D, KB = 5, 3, 64, 32, 2
SEED = 20261123


def generated_cases():
    rng = np.random.default_rng(SEED)
    scenarios = []
    for case_id in range(8):
        if case_id == 0:
            x = np.zeros((M, K), np.float32)
        elif case_id == 1:
            x = np.ones((M, K), np.float32)
        elif case_id == 2:
            x = -np.ones((M, K), np.float32)
        elif case_id == 3:
            x = np.tile(np.arange(-32,32,dtype=np.float32)[None,:],(M,1))
        else:
            # deliberately variable exponent groups, with quantizer offsets
            exps = rng.integers(-15,3,(M,8))
            x = (rng.standard_normal((M,K)) * np.repeat(np.exp2(exps),8,axis=1)).astype(np.float32)
            if case_id == 5: x[:,8:24] = 0
            if case_id == 6: x[0] = 0
            if case_id == 7: x *= np.float32(2**-8)
        w = rng.integers(-127,128,(N,K),dtype=np.int16).astype(np.int8)
        if case_id == 0: w[:] = 1
        if case_id == 2: w[0,:]=-127
        sw = rng.uniform(.01,.1,N).astype(np.float32)
        dw = rng.integers(0,13,(N,KB),dtype=np.uint8)
        if case_id==4:dw[:]=12
        scenarios.append((f"case_{case_id:02d}",x,w,sw,dw))
    return scenarios


def actual_upstream(x,w,sw,dw):
    from opentpu import Config, fp32 as F, isa as I
    from opentpu.isasim import Machine
    data=np.zeros(8192,np.uint8)
    data[0:M*K*4]=x.view(np.uint8).reshape(-1)
    data[1024:1024+N*K]=w.view(np.uint8).reshape(-1)
    scale=np.zeros((N,8),np.uint8)
    scale[:,:4]=sw.view(np.uint8).reshape(N,4)
    scale[:,4:6]=dw
    data[2048:2048+N*8]=scale.reshape(-1)
    prog=[I.ld(0,0,M*K),I.qact(0,M,0,KB,K),
          I.mm(1024,2048,256,N,KB,K,N,M,0,8),I.halt()]
    s=Machine(Config(S=1,D=D),[prog],[data]).run().slices[0]
    output=s.tget(256+np.arange(M*N)).reshape(M,N)
    q,sa,da=F.quantize_mx(x,8)
    # Validate upstream QACT state agrees with stand-alone quantization.
    if not np.array_equal(s.act[:M,:K],q):
        raise AssertionError("actual QACT q differs from reference quantizer")
    if not np.array_equal(s.adoff[:M,:KB].reshape(M,8),da):
        raise AssertionError("actual QACT offset differs from reference quantizer")
    if not np.array_equal(s.ascale[:M,0].view(np.uint32),sa.view(np.uint32)):
        raise AssertionError("actual QACT scale differs from reference quantizer")
    return output,q,sa,da,F


def hexwrite(path, seq, bits):
    mask=(1<<bits)-1
    path.write_text("".join(f"{int(x)&mask:0{(bits+3)//4}x}\n" for x in seq),encoding="utf-8")


def verify_and_generate(destination:Path):
    dest=destination.resolve();dest.mkdir(parents=True,exist_ok=True)
    results=[]
    for name,x,w,sw,dw in generated_cases():
        got,q,sa,da,F=actual_upstream(x,w,sw,dw)
        bit_want=np.empty((M,N),np.uint32)
        for j in range(M):
            core=grouped_acc([int(a) for a in q[j]],
                             [[int(v) for v in row] for row in w],
                             [int(d) for d in da[j]],
                             [[int(v) for v in row] for row in dw])
            # Float epilogue follows published MM order, with upstream's exact
            # FTZ FP32 primitive. The integer MAC itself is independent.
            # Still NOT independent FP32 implementation.
            raw=np.asarray(core.accumulators,np.float64).astype(np.float32)
            expected=F.mul(F.mul(raw,sw),F.mul(sa[j],np.float32(2**-16)))
            if not np.array_equal(got[j].view(np.uint32),expected.view(np.uint32)):
                raise AssertionError(f"actual upstream MM differs from independent integer core: {name} row {j}: got={got[j]},want={expected}")
            directory=dest/f"{name}_activation_{j}"
            directory.mkdir(exist_ok=True)
            hexwrite(directory/'q.hex',q[j],8)
            hexwrite(directory/'w.hex',w.reshape(-1),8)
            hexwrite(directory/'da.hex',da[j],8)
            hexwrite(directory/'dw.hex',dw.reshape(-1),8)
            hexwrite(directory/'expected.hex',core.accumulators,48)
            hexwrite(directory/'drops.hex',[core.dropped_groups],16)
            results.append({"fixture":name,"activation_row":j,"dropped_groups":core.dropped_groups,
                            "accumulators":list(core.accumulators),"output_bits":list(map(int,got[j].view(np.uint32))),
                            "output_fp32":list(map(float,got[j]))})
    expected_files=8*M
    if len(results)!=expected_files:raise AssertionError("wrong fixture count")
    summary={"input_fixtures":8,"activation_rows":M,"matrix_outputs":N,
             "signed_products_per_row":K*N,"executions":len(results),
             "upstream_reference":"FeSens/openTPU@d84db55712aba0d40811d7762cb052f05d55b7e5",
             "contract":"MM WF=0 D=32 KB=2, QACT groups 8, W=16, shift/drop, FP32 epilogue",
             "actual_isa_output_bit_equivalence":True,"core_independent":True,
             "fp32_primitive_independent":False,"results":results}
    canonical=json.dumps(summary,sort_keys=True,separators=(',',':')).encode()
    h=hashlib.sha256(canonical).hexdigest()
    (dest/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
    (dest/'summary.sha256').write_text(h+"\n")
    print(f"PASS_QUANTIZED_MXU_ISA fixtures={len(generated_cases())} activation_rows={len(results)} sha256={h}")
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    verify_and_generate(a.output)
