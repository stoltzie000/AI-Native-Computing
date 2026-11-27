import unittest
from unittest.mock import patch
import controller

class Tests(unittest.TestCase):
    def test_reject_unknown(self):
        with self.assertRaises(ValueError):
            controller.inspect("main")
    @patch("controller.git")
    def test_stale(self, git):
        sha = "a" * 40
        git.side_effect = ["", sha, "b"*40, "5", "state", "c"*40+" ref"]
        self.assertEqual(controller.inspect(controller.BRANCHES[0])["status"], "stale")
    @patch("controller.git")
    def test_valid(self, git):
        sha = "a"*40
        git.side_effect = ["", sha, "b"*40, "5", "state", sha+" ref"]
        result = controller.inspect(controller.BRANCHES[0])
        self.assertEqual(result["status"], "inspected")
        self.assertFalse(result["engineering_write"])
    @patch("controller.git")
    def test_size_limit(self, git):
        git.side_effect = ["", "a"*40, "b"*40, "1000001"]
        with self.assertRaises(ValueError):
            controller.inspect(controller.BRANCHES[0])
