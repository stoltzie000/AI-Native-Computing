import unittest
from manifest import eligible
class ManifestTests(unittest.TestCase):
    def test_eligibility(self):
        head = "a"*40
        task = {"id":"inspect-1","revision":head,"operation":"inspect_state"}
        self.assertTrue(eligible(task,head,set()))
        self.assertFalse(eligible(task,head,{("inspect-1",head)}))
        self.assertFalse(eligible(task,"b"*40,set()))
        self.assertFalse(eligible(dict(task,operation="shell"),head,set()))
        self.assertFalse(eligible(dict(task,command="echo"),head,set()))
        self.assertFalse(eligible(dict(task,operation=[]),head,set()))
