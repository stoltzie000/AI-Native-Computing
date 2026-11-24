import unittest
from q8_reference import q8,vectors
class Tests(unittest.TestCase):
 def test_zero(self):
  for x in (0,0x80000000,1,0x80000001,0x007fffff,0x807fffff):self.assertEqual(q8(x),0)
 def test_rounding(self):
  for x,y in ((0x3f000000,0),(0xbf000000,0),(0x3fc00000,2),(0xbfc00000,-2),(0x40200000,2),(0xc0200000,-2)):self.assertEqual(q8(x),y)
 def test_saturation(self):
  for x,y in ((0x43000000,127),(0xc3000000,-127),(0x7f800000,127),(0xff800000,-127)):self.assertEqual(q8(x),y)
 def test_nan(self):
  for x in (0x7fc00000,0xffc00001,0x7f800001):self.assertEqual(q8(x),0)
 def test_invalid(self):
  for x in (-1,0x100000000,1.0,True):
   with self.assertRaises(ValueError):q8(x)
 def test_determinism(self):self.assertEqual(len(vectors()),2049);self.assertEqual(vectors(),vectors())
if __name__=='__main__':unittest.main()
