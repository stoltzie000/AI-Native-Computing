# OpenTPU reproducibility — retained negative-run evidence (2026-11-23)

This is not an accusation of upstream algorithmic incorrectness. The original pinned openTPU repository and its CPU-based ISA/dataflow/compiler tests are the reference. Negative runs must not be erased.

| Run | Upstream software tests | Local tests | Actual RTL differential | Reason |
|---|---:|---:|---|---|
| [45281228948](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45281228948) | **48 passed** | **6 report-gate + 7 v1.0 passed** | **FAILED at compile** | Ubuntu Verilator **5.020** rejected bit select of function return in simulation-only assertion `otpu_mxu.sv:2778` |
| [45281871189](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45281871189) | **48 passed** | **9 report/patch + 7 v1.0 passed** | **NOT EXECUTED** | First compatibility patch script rejected unrelated working-tree entries; overly strict guard; script corrected after failure |
| [45282130627](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45282130627) | **48 passed** | **9 report/patch + 7 v1.0 passed** | **FAILED at compile** | After narrowly rewriting the first simulation assertion in ephemeral checkout, Verilator 5.020 rejected a second upstream construct in `rtl/vpu/otpu_se_tail.sv:457` (`Non-interface used as an interface`) |

The first source compatibility patch did **not** modify the synthesizable datapath, but run #3 showed that repeatedly rewriting upstream code is not a reliable independent reference. Patch script and exact source-guard logic are retained as a research record, NOT an accepted downstream fix.

## New plan

Use upstream openTPU at unchanged pinned commit `d84db55712aba0d40811d7762cb052f05d55b7e5`. Build **unmodified Verilator v5.054** at pinned release commit `bbb60a403932a9f695cb6ff001ceb73de6ad9234` in the CI runner, then run the same selected external tests. Confirm the upstream working tree has no tracked changes before and after external testing. Reproduce on an immutable runner with JUnit result parsing, including strict no-skips policy. If full RTL still fails, log concrete compiler error, do not call it a passing RTL baseline.

No chip/FPGA, clock, physical memory traffic, power, quality-matched GPU results, or superiority are verified here.
