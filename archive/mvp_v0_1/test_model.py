import unittest
from model import Config,evaluate
class ModelTests(unittest.TestCase):
 def test_weights(self):
  self.assertAlmostEqual(evaluate(Config(metadata_fraction=0))['weights_gb'],15)
 def test_bandwidth(self):
  r=evaluate(Config(metadata_fraction=0,bandwidth_gbs=1500,bandwidth_utilization=1,compute_tops=10000))
  self.assertAlmostEqual(r['estimated_decode_tps'],100)
 def test_compute(self):
  r=evaluate(Config(metadata_fraction=0,bandwidth_gbs=10000,compute_tops=6,compute_utilization=1))
  self.assertAlmostEqual(r['estimated_decode_tps'],100)
 def test_energy(self):
  r=evaluate(Config())
  self.assertAlmostEqual(r['estimated_tokens_per_joule'],r['estimated_decode_tps']/350)
if __name__=='__main__':unittest.main()
