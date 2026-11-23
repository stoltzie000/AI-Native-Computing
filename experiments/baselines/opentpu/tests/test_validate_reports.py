"""Deterministic local JUnit gate tests; do not require openTPU."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_reports import summarize, validate


class ReportTests(unittest.TestCase):
    def write(self, parent, cases):
        path = parent / "junit.xml"
        path.write_text(f'<testsuite tests="{len(cases)}">' + "".join(cases) + "</testsuite>")
        return path

    def test_valid_report(self):
        with tempfile.TemporaryDirectory() as t:
            p = self.write(Path(t), ['<testcase name="x"/>', '<testcase name="y"/>'])
            self.assertEqual(summarize(p, 2)["cases"], 2)

    def test_missing_report(self):
        with self.assertRaises(ValueError):
            summarize(Path("/a/nonexistent/report.xml"), 1)

    def test_reject_skipped_rtl(self):
        with tempfile.TemporaryDirectory() as t:
            p = self.write(Path(t), ['<testcase name="rtl"><skipped/></testcase>'])
            with self.assertRaises(ValueError):
                summarize(p, 1)

    def test_reject_failure_and_error(self):
        for tag in ("failure", "error"):
            with self.subTest(tag=tag), tempfile.TemporaryDirectory() as t:
                p = self.write(Path(t), [f'<testcase name="rtl"><{tag}/></testcase>'])
                with self.assertRaises(ValueError):
                    summarize(p, 1)

    def test_reject_zero_tests(self):
        with tempfile.TemporaryDirectory() as t:
            p = self.write(Path(t), [])
            with self.assertRaises(ValueError):
                summarize(p, 1)

    def test_invalid_root(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "junit.xml"
            p.write_text("<wrong><testcase/></wrong>")
            with self.assertRaises(ValueError):
                summarize(p, 1)


if __name__ == "__main__":
    unittest.main()
