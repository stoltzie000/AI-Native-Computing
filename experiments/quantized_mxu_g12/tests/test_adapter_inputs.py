import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adapter import generated_cases

class InputTests(unittest.TestCase):
    def test_count_shapes(self):
        c=generated_cases()
        self.assertEqual(len(c),8)
        for name,x,w,sw,dw in c:
            self.assertEqual(x.shape,(3,64))
            self.assertEqual(w.shape,(5,64))
            self.assertEqual(sw.shape,(5,))
            self.assertEqual(dw.shape,(5,2))
    def test_reproducible(self):
        a,b=generated_cases(),generated_cases()
        self.assertEqual([t[0] for t in a],[t[0] for t in b])
        for x,y in zip(a,b):
            for i in range(1,5):self.assertTrue((x[i]==y[i]).all())
    def test_negative_control(self):
        c=generated_cases()
        self.assertTrue((c[0][1]==0).all())
        self.assertTrue((c[1][1]!=0).all())
        self.assertTrue((c[2][1]!=0).all())
if __name__=='__main__':unittest.main()
