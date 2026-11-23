"""Fail closed on missing/skipped upstream RTL differential execution.

Parses JUnit XML emitted by real pytest runs. Validates *test execution only*,
not numerical throughput, clock frequency, GPU superiority or energy.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

UPSTREAM_COMMIT = "d84db55712aba0d40811d7762cb052f05d55b7e5"


def summarize(path: Path, minimum: int) -> dict:
    if not path.is_file():
        raise ValueError(f"JUnit report missing: {path}")
    root = ET.parse(path).getroot()
    if root.tag not in ("testsuite", "testsuites"):
        raise ValueError(f"Invalid JUnit root: {root.tag}")
    cases = root.findall(".//testcase")
    errors = sum(any(c.find(t) is not None for t in ("error", "failure")) for c in cases)
    skipped = sum(c.find("skipped") is not None for c in cases)
    if len(cases) < minimum or errors or skipped:
        raise ValueError(
            f"{path}: cases={len(cases)} minimum={minimum} "
            f"errors_or_failures={errors} skipped={skipped}"
        )
    return {"cases": len(cases), "errors_or_failures": 0, "skipped": 0}


def validate(functional: Path, rtl: Path) -> dict:
    return {
        "upstream_project": "FeSens/openTPU",
        "pinned_commit": UPSTREAM_COMMIT,
        "evidence_level": "Upstream software ISA tests and actual Verilator-vs-ISA RTL differential on GitHub runner",
        "functional": summarize(functional, minimum=20),
        "rtl_differential": summarize(rtl, minimum=1),
        "rtl_parser_compatibility": "Verilator 5.020: two simulator-only assertion expressions rewritten via pinned verified patch; computation RTL unchanged",
        "unmodified_upstream_rtl_compiled": False,
        "physical_fpga_executed": False,
        "matched_GPU_benchmark_performed": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("functional", type=Path)
    p.add_argument("rtl", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = validate(args.functional, args.rtl)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("VALIDATED_OPENTPU_BASELINE " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
