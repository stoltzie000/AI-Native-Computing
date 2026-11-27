import unittest
from queue_worker import plan
from controller import BRANCHES
class QueueTests(unittest.TestCase):
    def test_pause_and_dedup(self):
        head = "a"*40
        entry = {"branch":BRANCHES[0],"task":{"id":"one","revision":head,"operation":"inspect_state"}}
        q = {"version":1,"paused":True,"tasks":[entry]}
        self.assertEqual(plan(q,{BRANCHES[0]:head},set()),[])
        q["paused"] = False
        self.assertEqual(plan(q,{BRANCHES[0]:head},set()),[entry])
        self.assertEqual(plan(q,{BRANCHES[0]:head},{("one",head)}),[])
        q["tasks"].append(entry)
        with self.assertRaises(ValueError):
            plan(q,{BRANCHES[0]:head},set())
