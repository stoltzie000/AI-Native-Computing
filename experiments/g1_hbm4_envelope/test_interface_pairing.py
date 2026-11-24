import unittest,math
from interface_pairing import Pair
class Tests(unittest.TestCase):
 def test_controller_limited(self):
  p=Pair(8,2048,10,11,True).evaluate()
  self.assertAlmostEqual(p['conditional_joint_limit_tb_s'],20.48)
  self.assertEqual(p['bottleneck'],'controller')
  self.assertEqual(p['physical_gate'],'OPEN')
 def test_memory_limited(self):
  p=Pair(8,2048,16,10,True).evaluate()
  self.assertAlmostEqual(p['conditional_joint_limit_tb_s'],20.48)
  self.assertAlmostEqual(p['controller_only_tb_s'],32.768)
  self.assertEqual(p['bottleneck'],'memory')
 def test_no_proven_compatibility(self):
  p=Pair(8,2048,16,16,None).evaluate()
  self.assertIsNone(p['conditional_joint_limit_tb_s'])
  self.assertIn('BLOCK',p['status'])
 def test_incompatible(self):
  p=Pair(8,2048,16,16,False).evaluate()
  self.assertIsNone(p['conditional_joint_limit_tb_s'])
  self.assertEqual(p['status'],'REJECT_INCOMPATIBLE')
 def test_validation(self):
  for kwargs in ({'stacks':0},{'data_pins':0},{'memory_gbps':math.inf},{'controller_gbps':0},{'compatible':1}):
   config=dict(stacks=8,data_pins=2048,controller_gbps=10)
   config.update(kwargs)
   with self.assertRaises(ValueError):Pair(**config)
if __name__=='__main__':unittest.main()
