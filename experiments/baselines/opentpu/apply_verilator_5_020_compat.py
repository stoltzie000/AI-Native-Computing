"""Narrow verification-only SystemVerilog parser compatibility patch.

Upstream commit and exact rtl/mxu/otpu_mxu.sv git blob are checked *before*
editing a temporary CI checkout. Only a simulation assertion is rewritten;
the synthesizable datapath and requested comparisons remain unchanged.
This does NOT mean unmodified upstream RTL compiled under Verilator 5.020.
"""
from __future__ import annotations
import argparse
import difflib
from pathlib import Path
import subprocess

UPSTREAM_SHA = "d84db55712aba0d40811d7762cb052f05d55b7e5"
SOURCE_BLOB = "bb74e8af7e10ece16e69e3a7468e8304abf3642f"
RELATIVE_FILE = "rtl/mxu/otpu_mxu.sv"
EXPRESSION = "bk_ad(rq_ad, rq_en)[b]"
ALIAS = "compat_rb_expected_from_bk_ad[b]"
DECLARATION = (
    "    logic [TLANES-1:0][31:0] compat_rb_expected_from_bk_ad;\n"
    "    assign compat_rb_expected_from_bk_ad = bk_ad(rq_ad, rq_en);\n"
)
ANCHOR = "    always @(posedge clk)\n      if (!rst && rst_seen) begin"


def rewrite(source: str) -> str:
    if source.count(EXPRESSION) != 2 or source.count(ANCHOR) != 1:
        raise ValueError("Unexpected upstream source; refusing compatibility patch")
    if "compat_rb_expected_from_bk_ad" in source:
        raise ValueError("Compatibility name already present")
    updated = source.replace(ANCHOR, DECLARATION + ANCHOR, 1)
    updated = updated.replace(EXPRESSION, ALIAS)
    if updated.count(ALIAS) != 2 or updated.count(DECLARATION) != 1:
        raise AssertionError("Incorrect compatibility rewrite")
    return updated


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def patch(repo: Path, diff_out: Path) -> None:
    if git(repo, "rev-parse", "HEAD") != UPSTREAM_SHA:
        raise ValueError("Unexpected upstream commit")
    source_file = repo / RELATIVE_FILE
    if git(repo, "hash-object", RELATIVE_FILE) != SOURCE_BLOB:
        raise ValueError("Unexpected upstream RTL source blob")
    version = subprocess.check_output(["verilator", "--version"], text=True).strip()
    if not version.startswith("Verilator 5.020 "):
        raise ValueError(f"Patch only approved for Verilator 5.020, got: {version}")
    original = source_file.read_text(encoding="utf-8")
    edited = rewrite(original)
    source_file.write_text(edited, encoding="utf-8")
    diff = "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        edited.splitlines(keepends=True),
        fromfile=f"upstream/{RELATIVE_FILE}",
        tofile=f"CI-verifier-only/{RELATIVE_FILE}",
    ))
    diff_out.parent.mkdir(parents=True, exist_ok=True)
    diff_out.write_text(diff, encoding="utf-8")
    if git(repo, "status", "--porcelain") != " M " + RELATIVE_FILE:
        raise ValueError("Unexpected working-tree changes after patch")
    print("VERILATOR_COMPAT_ASSERTION_ONLY " + version)
    print(diff)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("repo", type=Path)
    p.add_argument("--diff-out", required=True, type=Path)
    a = p.parse_args()
    patch(a.repo.resolve(), a.diff_out.resolve())
