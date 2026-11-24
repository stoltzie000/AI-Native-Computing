"""Independent 64-value FP32 QACT group-offset reference (not full QACT)."""
import argparse,hashlib,json,random
from pathlib import Path
N=64;G=8;MAX_D=31;SEED=20261124
def abs_ftz_word(word):
    if type(word) is not int or not 0<=word<=0xffffffff: raise ValueError('word must be uint32')
    positive=word&0x7fffffff
    return positive if positive&0x7f800000 else 0
def offsets(words):
    if len(words)!=N: raise ValueError('64 input FP32 words required')
    abswords=[abs_ftz_word(x) for x in words]
    maximum=max(abswords)
    result=[]
    for i in range(0,N,G):
        gmax=max(abswords[i:i+G])
        if not gmax: result.append(0)
        else:
            delta=(maximum>>23)-(gmax>>23)-int((gmax&0x7fffff)>(maximum&0x7fffff))
            result.append(max(0,min(MAX_D,delta)))
    return result
def cases():
    rng=random.Random(SEED);samples=[]
    samples.append([0]*N)
    samples.append([0x3f800000]*N)
    samples.append([0x3f800000,0xbf800000]*32)
    samples.append([0x7f7fffff]*8+[0x00800000]*(N-8))
    samples.append([0x00000001,0x80000001,0,0x80000000]*16)
    samples.append([0x7fc00000]*8+[0x7f800000]*8+[0x00800000]*48)
    samples.append([0x7f800000]*8+[0x00000000]*56)
    samples.append([0x7f7fffff]*8+[0x00800000,0xbf800000,0x00000001,0]*14)
    for _ in range(24): samples.append([rng.getrandbits(32) for _ in range(N)])
    if len(samples)!=32 or any(len(x)!=64 for x in samples): raise AssertionError('bad generated shape')
    return samples
def emit(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);manifest=[]
    for i,values in enumerate(cases()):
        d=offsets(values);directory=folder/f'case_{i:02d}';directory.mkdir(exist_ok=True)
        (directory/'x.hex').write_text(''.join(f'{v:08x}\n' for v in values))
        (directory/'d.hex').write_text(''.join(f'{v:02x}\n' for v in d))
        manifest.append({'name':directory.name,'offsets':d})
    encoded=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    sha=hashlib.sha256(encoded).hexdigest()
    (folder/'manifest.json').write_text(json.dumps({'sha256':sha,'cases':manifest},indent=2)+'\n')
    print(f'PASS_QACT_OFFSET_REFERENCE cases=32 groups=256 sha256={sha}')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    emit(parser.parse_args().output)
