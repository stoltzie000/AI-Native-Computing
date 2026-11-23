"""Proof that the parser patch changes the required text only."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apply_verilator_5_020_compat import rewrite, DECLARATION, ANCHOR, EXPRESSION, ALIAS

class PatchTests(unittest.TestCase):
    def test_exact_two_assertion_expressions(self):
        src = (
            "module m;\n"
            + "`ifndef SYNTHESIS\n"
            + ANCHOR + "\n"
            + "  if (rb_v[b] && rb_a[b] != " + EXPRESSION + ") begin\n"
            + '    $display("%0d", ' + EXPRESSION + ");\n"
            + "  end\n"
            + "`endif\n"
            + "endmodule\n"
        )
        out = rewrite(src)
        self.assertEqual(out.count(DECLARATION), 1)
        self.assertEqual(out.count(ALIAS), 2)
        self.assertEqual(out.count(EXPRESSION), 0)
        self.assertIn("if (rb_v[b]", out)

    def test_reject_changed_upstream_source(self):
        with self.assertRaises(ValueError):
            rewrite("module m; endmodule")

    def test_reject_already_modified_source(self):
        src = ANCHOR + "\n" + EXPRESSION*2 + "compat_rb_expected_from_bk_ad"
        with self.assertRaises(ValueError):
            rewrite(src)

if __name__ == "__main__":
    unittest.main()
