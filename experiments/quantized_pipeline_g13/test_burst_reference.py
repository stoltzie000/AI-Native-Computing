import random
import os
from pathlib import Path
import unittest
from burst_reference import bursts, simulate, place_response, ProtocolError


class BurstReferenceTests(unittest.TestCase):
    def test_exact_G13_operand_payload_and_width_sweep(self):
        source=bytes((i * 17 + (i >> 2)) % 256 for i in range(2048))
        for width in (1, 8, 16, 32, 64, 128):
            for depth in (1,2,4,8):
                data, stats=simulate(source,128,402,width=width,depth=depth)
                self.assertEqual(data,source[128:530])
                self.assertEqual(stats['useful'],402)
                self.assertEqual(stats['requests'],stats['responses'])
                self.assertLessEqual(stats['peak'],depth)
                self.assertEqual(stats['padding'],stats['transferred']-402)

    def test_random_unaligned_no_other_memory_modified(self):
        rng=random.Random(20261124)
        for i in range(300):
            width=rng.choice((1,2,4,8,16,32,64,128))
            memory=rng.randbytes(4096)
            base=rng.randrange(0,3000)
            length=rng.randrange(1,400)
            depth=rng.choice((1,2,4,8))
            out,s=simulate(memory,base,length,width=width,depth=depth,
                           jitter=13,seed=i+1,req_stall_every=3,
                           rsp_stall_every=5)
            self.assertEqual(out,memory[base:base+length])
            self.assertEqual(s['requests'],len(bursts(base,length,width)))
            self.assertLessEqual(s['peak'],depth)

    def test_duplicate_tag_payload_does_not_silently_corrupt(self):
        request=bursts(9,11,16)[0]
        target=bytearray(11)
        written=bytearray(11)
        place_response(target,written,9,request,bytes(range(16)))
        with self.assertRaises(ProtocolError):
            place_response(target,written,9,request,bytes(range(16)))
        self.assertEqual(bytes(target),bytes(range(9,16))+bytes(4))

    def test_invalid_inputs_and_uncovered_aligned_bus(self):
        for args in ((-1,10,16),(0,0,16),(0,10,3)):
            with self.assertRaises(ValueError): bursts(*args)
        for depth in (0,-1):
            with self.assertRaises(ValueError):
                simulate(bytes(256),0,32,depth=depth)
        with self.assertRaises(ValueError):
            simulate(bytes(32),0,32,width=64)

    def test_synthetic_comparator_identical_service_assumptions(self):
        memory=bytes((i*73) % 256 for i in range(1024))
        ref=memory[:402]
        modes={}
        for name,width,depth in [('serialized_byte',1,1),('one_burst',64,1),
                                 ('four_bursts',64,4)]:
            got,s=simulate(memory,0,402,width=width,depth=depth,latency=8,
                           jitter=0,req_stall_every=0,rsp_stall_every=0)
            self.assertEqual(got,ref)
            modes[name]=s
        self.assertEqual(modes['serialized_byte']['requests'],402)
        self.assertEqual(modes['one_burst']['requests'],7)
        self.assertEqual(modes['four_bursts']['requests'],7)
        self.assertLess(modes['four_bursts']['cycles'],modes['one_burst']['cycles'])
        self.assertLess(modes['one_burst']['cycles'],modes['serialized_byte']['cycles'])
        print('PASS_SYNTHETIC_COMPARATOR',[(k,v['cycles']) for k,v in modes.items()])

    def test_pinned_upstream_quantized_fixture_payloads(self):
        root = os.environ.get('G13_FIXTURE_ROOT')
        if not root:
            self.skipTest('G13_FIXTURE_ROOT not supplied outside CI')
        folders = sorted(Path(root).glob('case_*_activation_*'))
        self.assertEqual(len(folders),24)
        for folder in folders:
            payload = bytes(int(code,16) for name in ('q.hex','w.hex','da.hex','dw.hex')
                            for code in (folder/name).read_text().splitlines())
            self.assertEqual(len(payload),402)
            memory = payload + bytes(64)
            for width,depth in ((1,1),(16,2),(64,1),(64,4)):
                data,stat = simulate(memory,0,402,width=width,depth=depth,
                                     seed=20261124 + len(folder.name))
                self.assertEqual(data,payload,folder.name)
                self.assertEqual(stat['useful'],402)
                self.assertLessEqual(stat['peak'],depth)

if __name__=='__main__': unittest.main()
