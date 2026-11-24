"""G1.3 bitwise differential verification of independent QACT and epilogue."""
import json
import sys
from pathlib import Path
import numpy as np
import fp32_ref as f
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quantized_mxu_g12"))
from adapter import actual_upstream, generated_cases
from exact_core import grouped_acc
from opentpu import fp32 as F

def check():
    rng=np.random.default_rng(20261124)
    count=0
    for i in range(512):
        x=rng.integers(0,2**32,64,dtype=np.uint32)
        # restrict to finite inputs; includes subnormals and signed zero controls
        x[(x & 0x7f800000)==0x7f800000]=0
        if i%16==0: x[:8]=0
        q,s,d=f.quantize_row(x.tolist())
        uq,us,ud=F.quantize_mx(x.view(np.float32)[None,:],8)
        assert q==uq[0].tolist(), ("codes",i)
        assert s==int(us.view(np.uint32)[0]), ("scale",i)
        assert d==ud[0].tolist(), ("offset",i)
        count+=1
    rows=outputs=0
    for name,x,w,sw,dw in generated_cases():
        got,q,sa,da,_=actual_upstream(x,w,sw,dw)
        for j,row in enumerate(x):
            codes,scale,offset=f.quantize_row(row.view(np.uint32).tolist())
            assert codes==q[j].tolist(), name
            assert scale==int(sa[j].view(np.uint32)), name
            assert offset==da[j].tolist(), name
            core=grouped_acc(codes,w.tolist(),offset,dw.tolist())
            bits=[f.mul(f.mul(f.word(a),int(b)),f.mul(scale,f.word(2**-16)))
                  for a,b in zip(core.accumulators,sw.view(np.uint32))]
            assert bits==got[j].view(np.uint32).tolist(), (name,j,bits,got[j])
            rows+=1
            outputs+=len(bits)
    report={"quantizer_rows":count,"quantizer_values":count*64,"actual_isa_rows":rows,
            "actual_isa_scalar_outputs":outputs,"independent_fp32":True,
            "memory_controller_validated":False,"physical_performance_validated":False}
    print(json.dumps(report,indent=2))
    Path("g13-results.json").write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__": check()
