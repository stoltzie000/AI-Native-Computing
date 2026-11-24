"""Independent scalar binary32 arithmetic and high-byte QACT reference."""
import struct
import math

def word(x):
    try: return struct.unpack('>I',struct.pack('>f',x))[0]
    except OverflowError: return 0xff800000 if x<0 else 0x7f800000

def value(x): return struct.unpack('>f',struct.pack('>I',x))[0]
def ftz(x): return x & 0x80000000 if x & 0x7f800000 == 0 else x

def op(a,b,kind):
    a,b=value(ftz(a)),value(ftz(b))
    c=a*b if kind=='mul' else a+b if kind=='add' else a-b
    return 0x7fc00000 if math.isnan(c) else ftz(word(c))
def mul(a,b): return op(a,b,'mul')
def add(a,b): return op(a,b,'add')
def sub(a,b): return op(a,b,'sub')
ONE=word(1); TWO=word(2); QMAX=word(127)

def recip(x):
    x=ftz(x); magnitude=x & 0x7fffffff; sign=x & 0x80000000
    if not magnitude: return 0
    if magnitude>=0x7e800000: return sign
    a=0x3f800000 | (magnitude & 0x7fffff)
    y=0x7ef311c3-a
    for _ in range(2): y=mul(y,sub(TWO,mul(a,y)))
    y=add(y,mul(y,sub(ONE,mul(a,y))))
    return ((y+((127-(magnitude>>23))<<23)) & 0xffffffff)|sign

def q8(x):
    x=value(ftz(x))
    if math.isnan(x): return 0
    if x>=127: return 127
    if x<=-127: return -127
    return round(x)

def quantize_row(words,group=8):
    if not words or group<1 or len(words)%group: raise ValueError('invalid row/group')
    words=[ftz(x) for x in words]; mags=[x&0x7fffffff for x in words]
    top=max(mags); scale=mul(top,word(1/127)); inv=mul(QMAX,recip(top))
    codes=[]; offsets=[]
    for i in range(0,len(words),group):
        m=max(mags[i:i+group])
        d=0 if not m else max(0,min(31,(top>>23)-(m>>23)-int((m&0x7fffff)>(top&0x7fffff))))
        offsets.append(d); factor=mul(inv,word(2**d))
        codes.extend(q8(mul(x,factor)) for x in words[i:i+group])
    return codes,scale,offsets
