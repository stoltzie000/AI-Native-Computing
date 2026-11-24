"""Independent integer-domain FP32-to-Q8 reference. No float computations."""
import argparse,hashlib,json,random
from pathlib import Path
SEED=20261124
def q8(x):
 if type(x) is not int or not 0<=x<=0xffffffff: raise ValueError("uint32 required")
 sign=-1 if x>>31 else 1; exponent=(x>>23)&255;fraction=x&0x7fffff
 if exponent==255:return 0 if fraction else 127*sign
 if exponent==0:return 0
 mantissa=(1<<23)|fraction;shift=150-exponent
 if shift<=0:integer=128
 else:
  whole,remainder=divmod(mantissa,1<<shift);half=1<<(shift-1)
  integer=whole+int(remainder>half or (remainder==half and whole%2==1))
 return max(-127,min(127,sign*integer))
def vectors():
 boundary=[0,0x80000000,1,0x80000001,0x007fffff,0x807fffff,0x00800000,
 0x80800000,0x3f000000,0xbf000000,0x3f000001,0x3fc00000,0xbfc00000,
 0x40200000,0xc0200000,0x42fc0000,0xc2fc0000,0x42fe0000,0xc2fe0000,
 0x43000000,0xc3000000,0x7f800000,0xff800000,0x7fc00000,
 0xffc00001,0x7f7fffff,0xff7fffff,0x3e800000,0xbe800000,
 0x3f800000,0xbf800000,0x4b000000,0xcb000000]
 rng=random.Random(SEED)
 return boundary+[rng.getrandbits(32) for _ in range(2016)]
def emit(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);v=vectors();assert len(v)==2049
 (out/'x.hex').write_text(''.join(f'{x:08x}\n' for x in v))
 (out/'expected.hex').write_text(''.join(f'{q8(x)&255:02x}\n' for x in v))
 digest=hashlib.sha256(''.join(f'{x:08x}:{q8(x)&255:02x}\n' for x in v).encode()).hexdigest()
 (out/'manifest.json').write_text(json.dumps({'cases':len(v),'sha256':digest,'seed':SEED},indent=2)+'\n')
 print(f'PASS_Q8_ORACLE cases={len(v)} sha256={digest}')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
 emit(parser.parse_args().output)
