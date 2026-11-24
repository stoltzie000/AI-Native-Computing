"""Direct differential against pinned upstream FP32 mul + Q8; not a full QACT."""
import argparse,importlib.util,random,pathlib,json,hashlib
import numpy as np
def generate(folder,upstream):
 spec=importlib.util.spec_from_file_location('pinned_fp32',pathlib.Path(upstream)/'opentpu'/'fp32.py')
 F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
 rng=random.Random(20261124)
 edge=[0,0x80000000,0x7f800000,0xff800000,0x7fc00000,0xffc00001,
       0x3f800000,0xbf800000,0x3f000000,0x3fc00000,0x42fe0000,0x00800000,0x00000001]
 pairs=[(x,y) for x in edge for y in edge]
 pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(512-len(pairs))]
 assert len(pairs)==512
 a=np.array([x for x,_ in pairs],dtype=np.uint32)
 b=np.array([y for _,y in pairs],dtype=np.uint32)
 prod=F.mul(F.from_bits(a),F.from_bits(b));quant=F.q8(prod)
 pw=prod.view(np.uint32);qw=quant.view(np.uint8)
 out=pathlib.Path(folder);out.mkdir(parents=True,exist_ok=True)
 for name,vals in [('x.hex',a),('inv.hex',b),('product.hex',pw),('q.hex',qw)]:
  width=2 if name=='q.hex' else 8
  (out/name).write_text(''.join(f'{int(v):0{width}x}\n' for v in vals))
 digest=hashlib.sha256(''.join(f'{int(a[i]):08x}:{int(b[i]):08x}:{int(pw[i]):08x}:{int(qw[i]):02x}\n' for i in range(len(a))).encode()).hexdigest()
 (out/'manifest.json').write_text(json.dumps({'pairs':512,'sha256':digest,'upstream':'d84db55712aba0d40811d7762cb052f05d55b7e5'},indent=2)+'\n')
 print(f'PASS_SCALED_Q8_REFERENCE pairs=512 sha256={digest}')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--upstream',required=True)
 q=ap.parse_args();generate(q.output,q.upstream)
