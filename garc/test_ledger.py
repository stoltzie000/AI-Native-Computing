import tempfile
import unittest
from pathlib import Path
from ledger import load, append, completed
class LedgerTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/"evidence.jsonl"
            self.assertEqual(load(p), [])
            append(p, {"id":"one","sha":"a"*40,"status":"inspected"})
            append(p, {"id":"two","sha":"b"*40,"status":"blocked"})
            self.assertEqual(completed(load(p)), {("one","a"*40)})
