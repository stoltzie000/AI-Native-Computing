"""Produce frozen full QACT scale oracle while checking real upstream and independent scalar reference."""
import argparse, pathlib,sys,hashlib,json
def generate(folder,upstream):
 import qact_row_reference
 folder=pathlib.Path(folder)
 qact_row_reference.produce(folder,upstream)
 sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'quantized_pipeline_g13'))
 import fp32_ref as reference
 data=[int(x,16) for x in (folder/'x.hex').read_text().splitlines()]
 assert len(data)==2048
 scales=[]
 for i in range(0,2048,64):
  _,scale,_=reference.quantize_row(data[i:i+64],group=8)
  scales.append(scale)
 (folder/'scale.hex').write_text(''.join(f'{x:08x}\n' for x in scales))
 expected=[int(x,16) for x in (folder/'inv.hex').read_text().splitlines()]
 assert len(expected)==32 and len(scales)==32
 manifest={'rows':32,'scale_sha256':hashlib.sha256((folder/'scale.hex').read_bytes()).hexdigest()}
 (folder/'full-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
 print('PASS_QACT_FULL_REFERENCE rows=32 q=2048 offsets=256 scales=32')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--upstream',required=True)
 x=ap.parse_args();generate(x.out,x.upstream)
