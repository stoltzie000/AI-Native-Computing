import unittest
from qact_offset_reference import offsets,cases,abs_ftz_word
class QACTOffsetTests(unittest.TestCase):
 def test_zero(self): self.assertEqual(offsets([0]*64),[0]*8)
 def test_equal_magnitude(self): self.assertEqual(offsets([0xbf800000]*64),[0]*8)
 def test_denormal_ftz(self):
  self.assertEqual(abs_ftz_word(0x80000001),0)
  self.assertEqual(offsets([0x00000001]*64),[0]*8)
 def test_saturation(self):
  self.assertEqual(offsets([0x7f7fffff]*8+[0x00800000]*56),[0]+[31]*7)
 def test_frozen_shape(self):
  self.assertEqual(len(cases()),32)
  self.assertTrue(all(len(x)==64 for x in cases()))
 def test_reject_bad(self):
  with self.assertRaises(ValueError): offsets([0]*63)
  with self.assertRaises(ValueError): offsets([0]*63+[-1])
  with self.assertRaises(ValueError): offsets([0]*63+[0x100000000])
if __name__=='__main__': unittest.main()
