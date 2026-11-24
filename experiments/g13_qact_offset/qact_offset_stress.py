"""512 deterministic offset stress fixtures from audited reference."""
import argparse,random,hashlib,json
from pathlib import Path
from qact_offset_reference import cases,offsets
def emit(path):
 rng=random.Random(20261125)
 data=cases()+[[rng.getrandbits(32) for _ in range(64)] for _ in range(480)]
 assert len(data)==512
 root=Path(path);root.mkdir(parents=True,exist_ok=True)
 words=''.join(f'{v:08x}\n' for row in data for v in row)
 ds=''.join(f'{d:02x}\n' for row in data for d in offsets(row))
 (root/'x.hex').write_text(words);(root/'d.hex').write_text(ds)
 digest=hashlib.sha256((words+ds).encode()).hexdigest()
 (root/'manifest.json').write_text(json.dumps({'cases':512,'offsets':4096,'sha256':digest},indent=2)+'\n')
 print(f'PASS_OFFSET_STRESS_REFERENCE cases=512 offsets=4096 sha256={digest}')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);emit(ap.parse_args().out)
