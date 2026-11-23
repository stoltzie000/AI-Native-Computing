import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from activation_probe import ActivationCollector, SENTENCES, SOURCES, file_sha256, make_prompt

class ProbeTests(unittest.TestCase):
    def test_linear_zero_count_and_logical_macs(self):
        m = torch.nn.Linear(4, 3, bias=False)
        probe = ActivationCollector().attach(m)
        with torch.no_grad():
            m(torch.tensor([[0., 2., -0., 1.], [3., 0., 0., 4.]]))
        probe.close()
        row = probe.report()["summary_by_operator"]["Linear"]
        self.assertEqual((row["elements"],row["exact_zeros"]),(8,4))
        self.assertEqual((row["logical_total_weight_macs"],row["logical_zero_weight_macs"]),(24,12))
    def test_nonfinite_rejected(self):
        m=torch.nn.Linear(2,3)
        probe=ActivationCollector().attach(m)
        with self.assertRaises(ValueError): m(torch.tensor([[float('nan'),0]]))
        probe.close()
    def test_conv_tracked_separately(self):
        m=torch.nn.Conv1d(2,3,1)
        probe=ActivationCollector().attach(m)
        with torch.no_grad():m(torch.zeros(1,2,4))
        probe.close()
        result=probe.report()
        self.assertIn('Conv1d',result['summary_by_operator'])
        self.assertNotIn('Linear',result['summary_by_operator'])
        self.assertEqual(result['summary_by_operator']['Conv1d']['exact_zeros'],8)
    def test_handles_closed(self):
        m=torch.nn.Linear(2,2)
        p=ActivationCollector().attach(m)
        p.close()
        with torch.no_grad():m(torch.ones(1,2))
        with self.assertRaises(ValueError):p.report()
    def test_hash_independent(self):
        import tempfile,hashlib
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.bin';p.write_bytes(b'abc')
            self.assertEqual(file_sha256(p),hashlib.sha256(b'abc').hexdigest())
    def test_fixed_prompts_and_sources(self):
        self.assertEqual(len(SENTENCES),8)
        self.assertEqual(set(SOURCES),{'mixer','transformer'})
        self.assertTrue(all(len(x['sha256'])==64 for x in SOURCES.values()))
    def test_all_128_prompts_are_unique(self):
        generated = [make_prompt(i)[0] for i in range(128)]
        self.assertEqual(len(set(generated)), 128)
        self.assertEqual({make_prompt(i)[1] for i in range(128)}, {16,32,48,64})
        with self.assertRaises(ValueError):make_prompt(256)

    def test_qualified_report(self):
        m=torch.nn.Sequential(torch.nn.Linear(3,4),torch.nn.ReLU(),torch.nn.Linear(4,3))
        p=ActivationCollector().attach(m)
        with torch.no_grad():m(torch.tensor([[-2.,-1.,0.]]))
        p.close()
        r=p.report()
        self.assertEqual(len(r['per_operator']),2)
        self.assertGreater(r['summary_by_operator']['Linear']['exact_zeros'],0)

if __name__=='__main__':unittest.main()
