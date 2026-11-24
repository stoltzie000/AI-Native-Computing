import unittest
from validate_rubin_pareto import load,constrained_points
class ParetoTests(unittest.TestCase):
 def test_exact_ten_points(self):
  a=load()
  self.assertEqual([int(x['concurrency']) for x in a],[16,24,32,64,128,256,512,1024,2048,3072])
 def test_official_max(self):
  z=load()[-1]
  self.assertEqual(float(z['system_tps']),103537.)
  self.assertEqual(float(z['ttft_p90_ms']),7085.1)
  self.assertEqual(float(z['interactivity_tps_per_user']),33.7)
 def test_low_concurrency(self):
  z=load()[0]
  self.assertEqual(float(z['system_tps']),3741.6)
  self.assertEqual(float(z['ttft_p90_ms']),112.8)
 def test_illustrative_threshold(self):
  points=constrained_points(200)
  self.assertEqual(len(points),6)
  self.assertEqual(max(float(x['system_tps']) for x in points),33555.1)
 def test_not_wall_power(self):
  for row in load():
   self.assertNotEqual(row['power_kind'],'WALL_MEASURED')
   self.assertEqual(row['accuracy_score'],'UNKNOWN')
 def test_bad_threshold(self):
  for v in (-1,0,True):
   with self.assertRaises(ValueError):constrained_points(v)
if __name__=='__main__':unittest.main()
