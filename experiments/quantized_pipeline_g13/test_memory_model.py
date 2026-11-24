import unittest
import random
from memory_model import Request,bursts,simulate,workload

class MemoryTests(unittest.TestCase):
    def test_workload(self):
        x=simulate(workload())
        self.assertEqual(x["useful"],1188)
        self.assertEqual(x["bursts"],19)
        self.assertEqual(x["transferred"],1216)
        self.assertEqual(x["writes"],1)
        self.assertEqual(x["reads"],18)
    def test_unaligned(self):
        self.assertEqual(bursts(Request(63,66),64),[(0,1,False),(64,64,False),(128,1,False)])
    def test_serial_closed_form(self):
        for n in range(1,20):
            self.assertEqual(simulate([Request(0,64*n)],depth=1,latency=8)["cycles"],8*n+1)
    def test_stall(self):
        a=simulate(workload(),depth=2)
        b=simulate(workload(),depth=2,stall=range(8,30))
        self.assertGreater(b["cycles"],a["cycles"])
        for k in ("useful","transferred","bursts","reads","writes"): self.assertEqual(a[k],b[k])
    def test_bounds(self):
        for d in (1,2,4,8):
            self.assertLessEqual(simulate(workload(),depth=d)["peak"],d)
    def test_random(self):
        rng=random.Random(20261124)
        for _ in range(500):
            width=rng.choice((16,32,64,128))
            rs=[Request(rng.randrange(500),rng.randrange(1,250),bool(i%2)) for i in range(rng.randrange(1,12))]
            d=rng.randrange(1,9)
            x=simulate(rs,width,d,rng.randrange(1,20),range(3,9))
            count=sum(len({a//width for a in range(r.address,r.address+r.size)}) for r in rs)
            self.assertEqual(x["bursts"],count)
            self.assertEqual(x["useful"],sum(r.size for r in rs))
            self.assertEqual(x["transferred"],count*width)
            self.assertLessEqual(x["peak"],d)
    def test_invalid(self):
        for r in (Request(-1,1),Request(0,0)):
            with self.assertRaises(ValueError): simulate([r])
        with self.assertRaises(ValueError): simulate(workload(),depth=0)
if __name__=="__main__": unittest.main()
