# G1.1 completed experimental evidence — 2026-11-23

## Verified external GitHub Actions execution

- [GitHub Actions run **45290172189**](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45290172189), job **138096581156**: **completed, SUCCESS**, not an unexecuted workflow.
- The workflow checked out unmodified FeSens/openTPU at commit `d84db55712aba0d40811d7762cb052f05d55b7e5` and built pinned Verilator **5.054** from commit `bbb60a403932a9f695cb6ff001ceb73de6ad9234`.
- Frozen SHA-256 for common 11-case signed INT8 64×4 inputs, all 64 expected outputs each, and 33 reproducibly generated input files: `6cacaf38065f50773531c84408572d930988a0c51d01608212db152cde474d38`. CI `sha256sum -c` **PASSED**.
- Existing project `prototype_v1_0/rtl/column_buffered_pe.v` was **not modified**.

## Executed, independently checked

| Gate | Pass | Evidence |
|---|---:|---|
| New deterministic fixture generator and constraints unit tests | **7/7** | CI log and fixture generator's frozen SHA |
| Existing v1.0 Python reference regression | **7/7** | CI log |
| Real pinned openTPU ISA executes all identical inputs | **11/11** | `openTPU_ISA.json` and CI log `PASS_SHARED_OPENTPU_ISA 11` |
| Our real Icarus Verilog v1.0 RTL, 2 lanes | **11/11** | `rtl/lane_2.log` 11 distinct fixture passes |
| Our real Icarus Verilog v1.0 RTL, 4 lanes | **11/11** | `rtl/lane_4.log` 11 distinct fixture passes |
| Real openTPU RTL via Verilator for dense/half-zero/all-zero controls | **3/3** | `openTPU_RTL.json` and CI log `PASS_SHARED_OPENTPU_RTL 3` |

**36 cross-implementation fixture executions passed.** Both existing and new Python suites had 7 tests each. This is a fixed-workload *arithmetic proof by test*, not a universal formal proof.

## Direct observations for our RTL

With 64 rows, exactly four active columns, and a synthetic in-order column-memory response:
- **LANES=2**: active MAC compute cycles = **128**.
- **LANES=4**: active MAC compute cycles = **64**.
- Two active columns: 64 versus 32 compute cycles respectively; zero active columns: zero MAC cycles. These are **not full-controller cycles, operating frequency, time, watts, bandwidth or latency**.

## Independently retrieved evidence

Downloaded artifact [**14874521670**](https://github.com/stoltzie000/AI-Native-Computing/actions/runs/45290172189/artifacts/14874521670) and inspected its contents in the analysis environment. It contains **42 entries**, including the exact generated `fixtures.json`, `manifest.json`, 33 named hex images, both openTPU JSON results, both RTL execution logs, upstream commit and tool/dependency identities. The fixture SHA-256 in both data and manifest matches the recorded frozen value; each local RTL lane log has **11 PASS** lines, openTPU ISA JSON has 11 and RTL JSON has 3 passes.

## Crucial scientific boundary

The openTPU test executes **FP32 VOP multiply/reduce**, intentionally chosen because four INT8 products can sum exactly as FP32 in this fixed small workload. It **does not exercise openTPU's quantized MXU/MM datapath**. Our PE executes signed INT8 operations and emulates a 64-byte column fetch using a testbench. Even though the exact mathematical outputs match, **arithmetic units, precision formats, weight layouts and memory movement are different**. No fair cycle, throughput, energy, DRAM efficiency, model quality or GPU superiority conclusion can be drawn. There was no FPGA or physical system deployment.

**Decision:** ADOPT this shared synthetic mathematical workload as the first proven cross-architecture correctness control. Do **not** accept it as a normalized throughput benchmark. Next gate is implementation of an *identical actual quantized operator and memory-transfer contract* in both architectures and a full-system/physical baseline.

The workflow is scoped to `research/matched-matvec-v1-1` plus its own YAML path only, with **no duplicate PR trigger**. Do not erase negative or earlier results.
