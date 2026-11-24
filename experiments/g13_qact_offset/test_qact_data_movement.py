import unittest
from qact_data_movement import Scenario
class MovementTests(unittest.TestCase):
 def test_default_bytes_and_boundary(self):
  m=Scenario(1).account()
  self.assertEqual((m['useful_raw_bytes'],m['useful_quant_bytes']),(256,76))
  self.assertEqual((m['raw_burst_bytes'],m['quant_burst_bytes']),(256,128))
  self.assertEqual((m['repeated_raw_traffic'],m['quantized_total_traffic']),(256,512))
 def test_external_raw_break_even(self):
  self.assertEqual(Scenario(3).account()['saved_bytes'],0)
  self.assertEqual(Scenario(4).account()['saved_bytes'],128)
  self.assertEqual(Scenario(2).account()['saved_bytes'],-128)
 def test_onchip_producer(self):
  self.assertEqual(Scenario(1,external_raw_load=False).account()['saved_bytes'],0)
  self.assertEqual(Scenario(2,external_raw_load=False).account()['saved_bytes'],128)
 def test_5bit_metadata(self):
  m=Scenario(4,offset_bytes=5).account()
  self.assertEqual(m['useful_quant_bytes'],73)
  self.assertEqual(m['quant_burst_bytes'],128)
 def test_other_burst(self):
  m=Scenario(4,burst=32).account()
  self.assertEqual(m['quant_burst_bytes'],96)
  self.assertEqual(m['saved_bytes'],256*4-256-96*5)
 def test_invalid(self):
  for kw in (dict(n=0),dict(n=1.0),dict(n=1,burst=48),dict(n=1,offset_bytes=-1),dict(n=1,external_raw_load=1)):
   with self.assertRaises(ValueError):Scenario(**kw)
 def test_evidence_boundary(self):
  m=Scenario(4).account()
  self.assertFalse(m['hardware_latency_or_energy_known'])
  self.assertFalse(m['independent_model_accuracy_verified'])
if __name__=='__main__':unittest.main()
