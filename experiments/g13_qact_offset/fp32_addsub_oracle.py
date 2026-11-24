"""Strict independent scalar binary32 oracle, cross-check pinned openTPU vector arithmetic."""
import argparse,hashlib,json,random,sys
from pathlib import Path
import numpy as np
def generate(folder,upstream):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quantized_pipeline_g13'))
 import fp32_ref as independent
 import importlib.util
 spec=importlib.util.spec_from_file_location('pinned_fp32',Path(upstream)/'opentpu'/'fp32.py')
 F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
 corners=[0,0x80000000,1,0x80000001,0x007fffff,0x807fffff,
  0x00800000,0x80800000,0x3f800000,0xbf800000,0x3f000000,
  0xbf000000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,
  0x7fc00000,0xffc00001,0x3f800001,0x3f7fffff,0x00000000,
  0x40000000,0xc0000000,0x7f800001,0x00400000]
 rng=random.Random(20261124)
 basic=[(a,b) for a in corners for b in corners]
 pairs=(basic+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(4096-len(basic))])
 if len(pairs)!=4096:raise AssertionError('pair count')
 words=[]
 for op in (0,1):
  for a,b in pairs:
   words.append((a,b,op,independent.sub(a,b) if op else independent.add(a,b)))
 a=np.array([w[0] for w in words],dtype=np.uint32)
 b=np.array([w[1] for w in words],dtype=np.uint32)
 actual=np.empty(len(words),dtype=np.uint32)
 for op in (0,1):
  segment=slice(4096*op,4096*(op+1))
  fn=F.sub if op else F.add
  actual[segment]=fn(F.from_bits(a[segment]),F.from_bits(b[segment])).view(np.uint32)
 disagreements=[(i,hex(words[i][3]),hex(int(actual[i]))) for i in range(len(words)) if words[i][3]!=int(actual[i])]
 if disagreements:raise AssertionError(f'independent reference disagreement count={len(disagreements)} first={disagreements[:3]}')
 out=Path(folder);out.mkdir(parents=True,exist_ok=True)
 for name,index,width in (('a.hex',0,8),('b.hex',1,8),('op.hex',2,1),('expected.hex',3,8)):
  (out/name).write_text(''.join(f'{row[index]:0{width}x}\n' for row in words))
 digest=hashlib.sha256(''.join(f'{a:08x}:{b:08x}:{op}:{v:08x}\n' for a,b,op,v in words).encode()).hexdigest()
 (out/'manifest.json').write_text(json.dumps(dict(vectors=len(words),sha256=digest,pinned_upstream='d84db55712aba0d40811d7762cb052f05d55b7e5'),indent=2)+'\n')
 print(f'PASS_FP32_ADDSUB_ORACLE vectors={len(words)} sha256={digest}')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--upstream',required=True)
 a=ap.parse_args();generate(a.out,a.upstream)
