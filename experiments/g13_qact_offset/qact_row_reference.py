"""Independently verify externally supplied inverse QACT against pinned upstream."""
import argparse,importlib.util,random,sys,hashlib,json
from pathlib import Path
import numpy as np
def produce(root,upstream):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quantized_pipeline_g13'))
 import fp32_ref as independent
 spec=importlib.util.spec_from_file_location('pinned_fp32',Path(upstream)/'opentpu'/'fp32.py')
 F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
 rng=random.Random(20261124)
 rows=[[0.]*64,[1.,-1.]*32,[0.]*63+[2.**-125],[1e20]+[1e-20]*63]
 rows += [[rng.uniform(-5,5) for _ in range(64)] for _ in range(28)]
 x=np.asarray(rows,dtype=np.float32)
 q,scale,d=F.quantize_mx(x,g=8)
 words=x.view(np.uint32)
 for i in range(32):
  qref,sref,dref=independent.quantize_row([int(z) for z in words[i]],8)
  if qref!=[int(v) for v in q[i]] or dref!=[int(v) for v in d[i]] or sref!=int(scale[i].view(np.uint32)):
   raise AssertionError(f'independent QACT oracle disagrees at row {i}')
 amax=F.from_bits(np.max(F.bits(F.fabs(x)),axis=1))
 inverse=F.mul(np.float32(127),F.recip(amax)).view(np.uint32)
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 fields=[('x.hex',[int(v) for row in words for v in row],8),
         ('inv.hex',[int(v) for v in inverse],8),
         ('q.hex',[int(v)&255 for row in q for v in row],2),
         ('d.hex',[int(v) for row in d for v in row],2)]
 combined=''
 for name,data,width in fields:
  t=''.join(f'{v:0{width}x}\n' for v in data)
  (root/name).write_text(t);combined+=name+':'+t
 digest=hashlib.sha256(combined.encode()).hexdigest()
 (root/'manifest.json').write_text(json.dumps({'rows':32,'elements':2048,'offsets':256,'sha256':digest,'upstream':'d84db55712aba0d40811d7762cb052f05d55b7e5'},indent=2)+'\n')
 print(f'PASS_QACT_ROW_REFERENCE rows=32 q=2048 offsets=256 sha256={digest}')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--upstream',required=True);ap.add_argument('--out',required=True)
 a=ap.parse_args();produce(a.out,a.upstream)
