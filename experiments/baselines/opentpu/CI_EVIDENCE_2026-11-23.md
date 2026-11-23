# Independent openTPU baseline reproduced — 2026-11-23

## Actual successful GitHub Actions evidence

- **GitHub Actions run:** [45282595649](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45282595649)
- **Job:** `138070641636`
- **Conclusion:** `success` (verified from completed GitHub Actions job)
- **Unmodified external source:** FeSens/openTPU commit `d84db55712aba0d40811d7762cb052f05d55b7e5`.
- **Toolchain:** Verilator **5.054**, built from pinned Verilator git release commit `bbb60a403932a9f695cb6ff001ceb73de6ad9234`. Source installed into ephemeral runner; version logged `Verilator 5.054 2026-11-01 rev vUNKNOWN-built20261123-bbb60a4`.
- **Third-party code:** Apache-2.0 upstream source temporarily checked out for validation, **no copied hardware code in this repository**.
- **Patch count:** **0** applied to upstream source in successful run. Prior rejected Verilator 5.020 compatibility approaches are retained separately.

## Executed test counts

| Gate | Executed | Passed | Skipped | Evidence |
|---|---:|---:|---:|---|
| Upstream ISA encoding, simulator semantics, DRAM weight layout, selected compiler/dataflow | 48 | **48** | 0 | `functional_junit.xml` from Actions artifact |
| Upstream **actual Verilator RTL vs ISA** MM replay (mcols=2, rows=8, seed=0) | 1 | **1** | 0 | `rtl_junit.xml`, 46.601s reported by JUnit |
| Project's local reproduction validator and source compatibility unit tests | 9 | **9** | 0 | Completed job logs |
| Project's existing v1.0 numerical reference tests | 7 | **7** | 0 | Completed job logs |
| Machine-readable strict JUnit gate | 2 JUnit reports | **PASSED** | 0 | `validate_reports.py`, reported `VALIDATED_OPENTPU_BASELINE` |

The RTL test builds upstream SystemVerilog with Verilator, executes `test_fuzz_mm_replay[2-8-0]`, and asserts **DRAM and TMEM state bit equality** against upstream `Machine` ISA simulator. This is substantially stronger than checking only Python control code or counting RTL source files. It is still a **single selected hardware-simulator test**, not exhaustive formal equivalence.

## Durable artifacts

The GitHub Actions [artifact](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45282595649/artifacts/14869578402) contains full two JUnit XML reports, `reproduction_summary.json`, exact upstream commit, exact Verilator version and Python dependency freeze. The JUnit files were inspected after download: **48 functional testcases and 1 RTL testcase, zero failures and zero skips**.

The JSON summary and dependency/commit/toolchain version text have been **committed as durable repository files** under `results/`, so the record is not limited to the 30-day CI artifact retention.

## Failed attempts retained

Runs 45281228948, 45281871189 and 45282130627 all passed the 48 external software tests but did NOT demonstrate valid RTL. First failed due Verilator 5.020 parsing a simulation-only function-result bit select, second failed a too-strict local guard, and third compiled past the first parser error only to reject an unrelated `otpu_se_tail.sv` construct. See [failure/compatibility log](FAILURE_AND_COMPATIBILITY_LOG.md). **Do not erase or count those runs as RTL passes.**

## Scientific conclusion and limitations

**ADOPT openTPU as a reproducible external functional ISA+RTL comparison/control.** Our project now has a verified third-party accelerator reference, with source and test provenance. This is a research infrastructure milestone, not new processor performance.

**Not measured:** physical FPGA card, achieved device clock, DRAM bandwidth, energy, complete AI model inference/quality, numeric equivalence of our v1.0 RTL with openTPU, or matched current NVIDIA/AMD GPUs.

**Next test must normalize arithmetic and resources.** Upstream `test_mm_matches_integer_math` includes activation quantization, scale/shift and FP32 reconstruction; our v1.0 is modular signed INT8×INT8→INT32. Raw RTL cycle counts are not comparable until one shared operator/precision contract is implemented in both. See [comparability gaps](COMPARABILITY_GAPS.md).

**Notification control:** the CI workflow uses push restricted to this branch and the workflow YAML path only; no `pull_request` trigger. Research/document commits and PR changes do not launch duplicate tests.
