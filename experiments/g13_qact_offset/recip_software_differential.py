"""Independent scalar reciprocal vs pinned actual upstream vectorized binary32 FTZ Newton."""
import argparse,importlib.util,random,pathlib,sys,hashlib,json
import numpy as np
def main(upstream,out):
 sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'quantized_pipeline_g13'))
 import fp32_ref as independent
 spec=importlib.util.spec_from_file_location('pinned_fp32',pathlib.Path(upstream)/'opentpu'/'fp32.py')
 F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
 rng=random.Random(20261124)
 edge=[0,0x80000000,1,0x80000001,0x007fffff,0x807fffff,0x00800000,
  0x80800000,0x3f800000,0xbf800000,0x3f000000,0x3fc00000,
  0x7e7fffff,0xfe7fffff,0x7e800000,0xfe800000,0x7f800000,
  0xff800000,0x7fc00001,0xffc00001,0x7f7fffff,0xff7fffff]
 words=edge+[rng.getrandbits(32) for _ in range(2048-len(edge))]
 actual=F.recip(F.from_bits(np.asarray(words,dtype=np.uint32))).view(np.uint32)
 expected=[independent.recip(x) for x in words]
 failures=[(i,words[i],expected[i],int(actual[i])) for i in range(len(words)) if expected[i]!=int(actual[i])]
 folder=pathlib.Path(out);folder.mkdir(parents=True,exist_ok=True)
 records=''.join(f'{w:08x}:{e:08x}\n' for w,e in zip(words,expected))
 digest=hashlib.sha256(records.encode()).hexdigest()
 (folder/'recip-input.hex').write_text(''.join(f'{w:08x}\n' for w in words))
 (folder/'recip-expected.hex').write_text(''.join(f'{e:08x}\n' for e in expected))
 (folder/'recip-manifest.json').write_text(json.dumps({'vectors':len(words),'sha256':digest,'failures':len(failures),'upstream':'d84db55712aba0d40811d7762cb052f05d55b7e5'},indent=2)+'\n')
 if failures:
  i,w,e,a=failures[0]
  raise AssertionError(f'recip mismatch i={i} x={w:08x} expected={e:08x} actual={a:08x} count={len(failures)}')
 print(f'PASS_RECIP_SOFTWARE_DIFFERENTIAL vectors={len(words)} sha256={digest}')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--upstream',required=True);ap.add_argument('--out',required=True)
 v=ap.parse_args();main(v.upstream,v.out)
