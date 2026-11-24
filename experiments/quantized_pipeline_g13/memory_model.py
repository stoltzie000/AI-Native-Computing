"""Bounded, ordered, synthetic burst scheduler. Not a DRAM timing model."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Request:
    address:int
    size:int
    write:bool=False

def bursts(req, width):
    if width<=0 or req.address<0 or req.size<=0:
        raise ValueError("invalid request")
    end=req.address+req.size
    return [(a,min(end,a+width)-max(a,req.address),req.write)
            for a in range(req.address//width*width,end,width)]

def simulate(requests,width=64,depth=2,latency=8,stall=()):
    if depth<1 or latency<1: raise ValueError("invalid controller")
    pending=[b for r in requests for b in bursts(r,width)]
    inflight=[]; completed=[]; index=0; cycle=0; peak=0; blocked=0
    stall=set(stall)
    while index<len(pending) or inflight:
        if inflight and inflight[0][0]<=cycle and cycle not in stall:
            _,b=inflight.pop(0); completed.append(b)
        if index<len(pending):
            if len(inflight)<depth:
                inflight.append((cycle+latency,pending[index]))
                index+=1; peak=max(peak,len(inflight))
            else: blocked+=1
        cycle+=1
    assert completed==pending
    return dict(cycles=cycle,bursts=len(completed),peak=peak,blocked=blocked,
                useful=sum(b[1] for b in completed),
                transferred=len(completed)*width,
                reads=sum(not b[2] for b in completed),
                writes=sum(b[2] for b in completed))

def workload():
    return [Request(0,3*64*4),Request(1024,5*64),
            Request(2048,5*8),Request(4096,3*5*4,True)]

if __name__=="__main__":
    import json
    print(json.dumps({str(d):simulate(workload(),depth=d) for d in (1,2,4,8)},indent=2))
