"""Generate real upstream pinned MM output fixtures plus arithmetic edge vectors.

No generated results are assumed until independently checked in GitHub Actions.
All ISA comparisons are exact binary32 bit-pattern equality.
"""
import argparse
import json
import random
import struct
import sys
from pathlib import Path
import numpy as np

G13=Path(__file__).resolve().parents[1]/"quantized_pipeline_g13"
G12=Path(__file__).resolve().parents[1]/"quantized_mxu_g12"
sys.path[:0]=[str(G13),str(G12)]
from adapter import generated_cases, actual_upstream, hexwrite
from exact_core import grouped_acc
import fp32_ref as f


def generate(fixtures: Path, output: Path):
    fixtures.mkdir(parents=True,exist_ok=True)
    output.mkdir(parents=True,exist_ok=True)
    rows=0
    for name,x,w,sw,dw in generated_cases():
        got,q,sa,da,_=actual_upstream(x,w,sw,dw)
        swbits=sw.view(np.uint32).tolist()
        for row in range(3):
            place=fixtures/f"{name}_activation_{row}"
            if not (place/"expected.hex").exists():
                raise FileNotFoundError("G1.2 generated integer fixture missing: "+str(place))
            core=grouped_acc(q[row].tolist(),w.tolist(),
                             da[row].tolist(),dw.tolist())
            expected=[f.mul(f.mul(f.word(a),int(b)),
                            f.mul(int(sa[row].view(np.uint32)),f.word(2**-16)))
                      for a,b in zip(core.accumulators,swbits)]
            actual=got[row].view(np.uint32).tolist()
            if expected!=actual:
                raise AssertionError(f"{name}/row{row} epilogue oracle diverged from actual pinned ISA")
            hexwrite(place/"ascale.hex",[int(sa[row].view(np.uint32))],32)
            hexwrite(place/"wscale.hex",swbits,32)
            hexwrite(place/"expected_fp32.hex",actual,32)
            rows+=1

    rng=random.Random(20261124)
    corners=[0,0x80000000,0x00000001,0x80000001,0x00800000,
             0x80800000,0x7f7fffff,0xff7fffff,0x7f800000,
             0xff800000,0x7fc12345,0xffc12345,0x3f800000,
             0xbf800000,0x00000002,0x007fffff,0x3f000000,
             0x37800000]
    pairs=[(a,b) for a,b in zip(corners,corners[::-1])]
    pairs+= [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(2048-len(pairs))]
    values=[0,-1,1,-(1<<47),(1<<47)-1,(1<<24)+1,
            (1<<24)+3,-((1<<24)+3)]
    values+=[rng.randrange(-(1<<47),1<<47) for _ in range(2048-len(values))]
    hexwrite(output/"mul_a.hex",[a for a,b in pairs],32)
    hexwrite(output/"mul_b.hex",[b for a,b in pairs],32)
    hexwrite(output/"mul_expected.hex",[f.mul(a,b) for a,b in pairs],32)
    hexwrite(output/"int48_in.hex",values,48)
    hexwrite(output/"int48_expected.hex",[f.word(v) for v in values],32)
    summary=dict(upstream="FeSens/openTPU@d84db55712aba0d40811d7762cb052f05d55b7e5",
                 exact_isa_rows=rows,fp32_outputs=rows*5,
                 multiply_finite_nan_inf_ftz_vectors=len(pairs),
                 int48_rne_vectors=len(values),isa_outputs_bit_exact=True)
    (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("PASS_EPILOGUE_REFERENCE",json.dumps(summary,sort_keys=True))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--fixtures",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    opts=ap.parse_args()
    generate(opts.fixtures,opts.output)
