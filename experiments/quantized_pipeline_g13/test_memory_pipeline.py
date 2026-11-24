"""Verify actual bytes at the output address against pinned upstream ISA."""
import json
import struct
import unittest
import random
from pathlib import Path
from memory_pipeline import transfer, execute
from memory_model import Request
from adapter import actual_upstream, generated_cases
import numpy as np

class MemoryPipelineTests(unittest.TestCase):
    def test_random_masked_transfers(self):
        rng=random.Random(20261124)
        for _ in range(300):
            mem=bytearray(rng.randbytes(1024))
            before=bytes(mem)
            start=rng.randrange(0,800); length=rng.randrange(1,200)
            data=rng.randbytes(length)
            width=rng.choice((16,32,64,128)); depth=rng.choice((1,2,4,8))
            _,wr=transfer(mem,[(Request(start,length,True),data)],width,depth,8,range(8,20))
            self.assertEqual(mem,before[:start]+data+before[start+length:])
            bufs,rd=transfer(mem,[(Request(start,length),None)],width,depth)
            self.assertEqual(bytes(bufs[0]),data)
            self.assertEqual(rd["useful"],length)
            self.assertEqual(wr["transferred"],rd["transferred"])
    def test_ordered_write_read(self):
        mem=bytearray(256)
        b,stats=transfer(mem,[(Request(31,66,True),bytes(range(66))),
                              (Request(31,66),None)],depth=8)
        self.assertEqual(b[1],bytes(range(66)))
    def test_invalid(self):
        for req,p in [(Request(-1,1),None),(Request(255,2),None),
                      (Request(0,4,True),b'x'),(Request(0,4),b'x')]:
            with self.assertRaises(ValueError): transfer(bytearray(256),[(req,p)])
    def test_end_to_end(self):
        report=[]
        for name,x,w,sw,dw in generated_cases():
            got,*_=actual_upstream(x,w,sw,dw)
            initial=bytearray([165])*8192
            initial[:768]=x.astype("<f4").tobytes()
            initial[1024:1344]=w.tobytes()
            for j in range(5):
                struct.pack_into("<f",initial,2048+8*j,float(sw[j]))
                initial[2052+8*j:2054+8*j]=bytes(dw[j])
            for depth in (1,2,4,8):
                for width in (32,64):
                    for stalls in ((),range(8,30)):
                        mem=bytearray(initial)
                        s=execute(mem,width,depth,8,stalls)
                        self.assertEqual(mem[4096:4156],got.astype("<f4").tobytes(),name)
                        self.assertEqual(mem[:4096],initial[:4096])
                        self.assertEqual(mem[4156:],initial[4156:])
                        self.assertEqual(s["compute_start"],s["read"]["end"])
                        self.assertEqual(s["write_start"],s["compute_start"]+120)
                        self.assertEqual(s["useful"],1188)
                        self.assertLessEqual(max(s["read"]["peak"],s["write"]["peak"]),depth)
                        report.append(dict(case=name,depth=depth,width=width,stalled=bool(stalls),**s))
        self.assertEqual(len(report),128)
        Path("g13-memory-pipeline.json").write_text(json.dumps(report,indent=2)+"\n")
        print("PASS_DATA_PIPELINE executions=128 scalar_outputs=1920")
if __name__=="__main__":unittest.main()
