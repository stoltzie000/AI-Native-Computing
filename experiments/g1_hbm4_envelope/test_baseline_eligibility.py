import json,unittest
from pathlib import Path
from baseline_eligibility import load,validate_record,comparison_status
FILE=Path(__file__).with_name('mlperf_endpoints_official_sample.json')
class BaselineEligibilityTests(unittest.TestCase):
 def setUp(self):
  self.data=load(FILE);self.row=dict(self.data['records'][0])
 def test_three_unique_official(self):
  self.assertEqual(len(self.data['records']),3)
  self.assertEqual({x['publication_status'] for x in self.data['records']},{'Official'})
  self.assertEqual(sorted(x['gpu_count'] for x in self.data['records']),[4,4,8])
 def test_exact_model_mismatch_blocks(self):
  self.assertEqual(comparison_status(self.row,self.data['model'],'Qwen2.5-32B'),
                   'BLOCK_MODEL_MISMATCH')
 def test_quality_unverified_blocks(self):
  self.assertEqual(comparison_status(self.row,self.data['model'],self.data['model']),
                   'BLOCK_QUALITY_UNVERIFIED')
 def test_provisional_blocks(self):
  self.row['publication_status']='Provisional'
  self.assertEqual(comparison_status(self.row,'deepseek-v4_1-flash','deepseek-v4_1-flash',True),
                   'BLOCK_PROVISIONAL')
 def test_not_wall_metered(self):
  self.assertEqual(comparison_status(self.row,self.data['model'],self.data['model'],True,True),
                   'BLOCK_WALL_POWER_UNMEASURED')
  self.row['actual_wall_power_kw']=9.73
  with self.assertRaises(ValueError):validate_record(self.row)
 def test_invalid_gpu_and_throughput(self):
  for value in (0,-1,2.0,True):
   self.row['gpu_count']=value
   with self.assertRaises(ValueError):validate_record(self.row)
  self.row['gpu_count']=8;self.row['task_throughput']=1000000
  with self.assertRaises(ValueError):validate_record(self.row)
 def test_missing_fields(self):
  del self.row['result_id']
  with self.assertRaises(ValueError):validate_record(self.row)
if __name__=='__main__':unittest.main()
