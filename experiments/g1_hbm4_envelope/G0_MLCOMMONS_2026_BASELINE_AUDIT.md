# G0 current published GPU baseline audit — 2026-11-24
EVIDENCE: Published official benchmark and rules; not measured or reproduced by this project. G0 OPEN.

## Verified primary sources
- MLCommons results index https://results.mlcommons.org/ : Endpoints v1.0 was released Nov 23, 2026 with 28 submissions reported.
- Official Endpoints Pareto explorer https://results.mlcommons.org/endpoints : agentic multi-step task results report system throughput versus E2E average user interactivity across concurrency, with Official vs Provisional publication status.
- Submission method https://docs.mlcommons.org/endpoints-submission-docs/understand/what-is-mlperf-endpoints/ and requirements https://docs.mlcommons.org/endpoints-submission-docs/rules/requirements/ . Authoritative policies https://github.com/mlcommons/endpoints_policies ; documentation includes still-evolving requirements.
- Older inference benchmark round v6.1, announced Sep 2026 https://mlcommons.org/2026/09/mlperf-inference-v6-1-results/ , source https://github.com/mlcommons/inference .

## Some officially verified, publicly disclosed Endpoints examples
Standardized model deepseek-v4_1-flash, Available category:
- Krai HPE Cray XD670 8×H200 (vLLM), Official 2026-11-18, 9.73 kW *MLC Estimated* provisioned system power; result ID 1.0.0.deepseek-v4_1-flash.agentic_combined.1.
- NVIDIA Vera Rubin NVL72 **4-GPU system under test**, Official 2026-11-18, provisioned power 12.61 kW; result ID 1.0.0.deepseek-v4_1-flash.mlperf_agentic_inference_dataset.3.
- NVIDIA GB300 NVL72 **4-GPU system under test**, Official 2026-11-04, provisioned power 7.5 kW; result ID 1.0.0.deepseek-v4_1-flash.mlperf_agentic_inference_dataset.1.
- Other MI300X, H200 and Rubin result records in the explorer are *Provisional* and must not silently be represented as Official. These entries are published configurations, NOT measured by this project.

## Key comparability integrity boundaries
1. Endpoints power-normalized throughput uses **provisioned/rated power** for Standardized submissions, not the measured AC wall power. The model may estimate omitted components and flag MLC Estimated Power. Do not label throughput/provisioned-kW as wall-metered performance/watt or energy/task.
2. Endpoints agentic reports whole-task E2E average user interactivity and system TPS, not raw kernel or per-chip cycle speed. Different GPU counts, context lengths, software stacks, load shapes, quality thresholds and tokenization confound direct comparisons.
3. MLPerf Inference v6.1 references Llama2-70B, Llama3.1-8B, DeepSeek-R1 etc.; Endpoints v1.0 references multi-step agentic models. Neither currently matches our assumed Qwen2.5-32B 4-bit / 32K-context analytical service-time proxy. No derived synthetic token/s to MLPerf score comparison is valid.
4. Standardized division requires accuracy/quality gates across tested frontier points, software disclosure and independent reproducibility. Exact policies are version-sensitive and subject to checks.
5. No original AI-native processor physical measurement, matched GPU trace, measured system energy or reproduced baseline has been established here.

## Engineering decision and falsifiable next gate
ADOPT official MLCommons methodology and verifiable system results as G0 published controls. TEST specific Official model/accuracy matched results with exact submission/run IDs, hardware GPU count and version, optimization/runtime, concurrency/TTFT and throughput quality frontier, dataset and tokenizer revision. Measure actual prototype on same task with repeated runs, fixed quality, and independent physical wall-power limits. Record separate power kinds: PROVISIONED_ESTIMATE, WALL_MEASURED, UNKNOWN. Preserve rejected comparisons without backfilling missing values. G0 remains OPEN until a reproducible optimized GPU workload matches our candidate task quality and measurement boundaries.

NEXT_ACTION: Build machine-readable citation-linked official-submission ledger, preserving status and power-kind metadata; independently validate its schema and eligibility, then use only comparable, matched points for future system-level physical benchmark.
