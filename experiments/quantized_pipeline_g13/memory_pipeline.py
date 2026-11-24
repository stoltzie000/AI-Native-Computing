"""Data-bearing ordered burst simulation with read/compute/write barriers.

Fixed G1.3 geometry. Timing is synthetic; software arithmetic is not RTL.
"""
import struct
import sys
from pathlib import Path
from memory_model import Request
import fp32_ref as f
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quantized_mxu_g12"))
from exact_core import grouped_acc

def transfer(memory,requests,width=64,depth=2,latency=8,stalls=(),start=0):
    if min(width,depth,latency)<1: raise ValueError("invalid configuration")
    pending=[]; buffers=[]
    for req,payload in requests:
        if req.address<0 or req.size<=0 or req.address+req.size>len(memory):
            raise ValueError("request outside memory")
        if req.write and (payload is None or len(payload)!=req.size):
            raise ValueError("invalid write payload")
        if not req.write and payload is not None: raise ValueError("read payload")
        buf=bytearray(payload if req.write else bytes(req.size))
        buffers.append(buf)
        for a in range(req.address//width*width,req.address+req.size,width):
            lo=max(a,req.address); hi=min(a+width,req.address+req.size)
            pending.append((req,buf,lo,hi))
    q=[]; i=0; cycle=start; peak=0; blocked=0; complete=0; stalls=set(stalls)
    while i<len(pending) or q:
        if q and q[0][0]<=cycle and cycle not in stalls:
            _,(req,buf,lo,hi)=q.pop(0)
            off=lo-req.address
            if req.write: memory[lo:hi]=buf[off:off+hi-lo]
            else: buf[off:off+hi-lo]=memory[lo:hi]
            complete+=1
        if i<len(pending):
            if len(q)<depth:
                q.append((cycle+latency,pending[i])); i+=1
                peak=max(peak,len(q))
            else: blocked+=1
        cycle+=1
    assert complete==len(pending)
    return buffers,dict(end=cycle,cycles=cycle-start,bursts=complete,peak=peak,
                        blocked=blocked,useful=sum(r.size for r,_ in requests),
                        transferred=complete*width)

def execute(memory,width=64,depth=2,latency=8,stalls=()):
    """Only memory bytes enter arithmetic; outputs committed through write queue."""
    cfg=dict(width=width,depth=depth,latency=latency,stalls=stalls)
    buffers,rd=transfer(memory,[(Request(0,768),None),(Request(1024,320),None),
                                (Request(2048,40),None)],**cfg)
    x=list(struct.unpack("<192I",buffers[0]))
    w=list(struct.unpack("<320b",buffers[1]))
    w=[w[i:i+64] for i in range(0,320,64)]
    sw=[]; dw=[]
    for i in range(5):
        sw.append(struct.unpack_from("<I",buffers[2],i*8)[0])
        dw.append(list(buffers[2][i*8+4:i*8+6]))
    output=[]
    for j in range(3):
        q,sa,da=f.quantize_row(x[j*64:(j+1)*64])
        acc=grouped_acc(q,w,da,dw).accumulators
        output.extend(f.mul(f.mul(f.word(a),b),f.mul(sa,f.word(2**-16)))
                      for a,b in zip(acc,sw))
    # 120 group-dot cycles is a G1.2 core-only scheduling assumption.
    # QACT and epilogue are untimed software, so this is NOT full latency.
    compute_start=rd["end"]; write_start=compute_start+120
    _,wr=transfer(memory,[(Request(4096,60,True),struct.pack("<15I",*output))],
                  start=write_start,**cfg)
    return dict(read=rd,write=wr,compute_start=compute_start,write_start=write_start,
                modeled_cycles=wr["end"],useful=rd["useful"]+wr["useful"],
                transferred=rd["transferred"]+wr["transferred"])
