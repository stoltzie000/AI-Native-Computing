# FP32 epilogue generic synthesis — verified 2026-11-24
- Tool: Yosys 0.33 (git 2584903a060), ubuntu-24.04.
- Exact source: fp32_mul_ftz.v, int48_to_fp32_rne.v, mxu_integer_epilogue.v under experiments/g13_fp32_epilogue/rtl on commit b9764f7eafd155c6c11adee92c892b507f998fb1.
- GitHub Actions run 45448043366, attempt 1, job 138637128400, SUCCESS. Actual job log PASS_G13_FP32_EPILOGUE_GENERIC_SYNTH and hierarchy stat Number of cells: 75373. Artifact 14945854625, raw ZIP not independently downloaded/rehashed.
- EVIDENCE CLASS SYNTHESIS_ESTIMATE (technology-independent, no timing/area/power physical measurement), not an FPGA resource utilization result. Do not combine with prior 16320 integer+tagged controller hierarchy as an equal configuration or infer a timing/performance ratio.
- Decision: TEST serial/shared FP32 epilogue with controlled identical five-output 24 pinned ISA fixture results; compare area/time/resource after same Yosys setup and arithmetic correctness. No serial version yet implemented or measured. No claims of physical throughput improvement.
- G1 remains OPEN.
