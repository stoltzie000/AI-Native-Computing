# Root cause analysis — provisional, 2026-11-24
## Evidence hierarchy
1. **Confirmed:** assistant previously ended responses with remaining user-authorized work; an assistant termination was visibly generated. Whether model policy, product runtime, output-budget, host lifecycle or external termination caused a particular response boundary is NOT observable.
2. **Confirmed:** GitHub CI has completed independently after assistant responses; GitHub result continuity alone does not prove ChatGPT message delivery or absence of platform issues.
3. **Confirmed this session:** 12 deterministic arithmetic operations completed; diagnostic connector call adaptation had local parsing exceptions; isolated GitHub queries succeeded; branch creation succeeded.
4. **Unknown:** transport delivery/acknowledgement, client error codes, OpenAI request/stream lifecycle, token/time ceilings, inactivity threshold, timestamp and exact prevalence of delivery timeouts. The proposed 180 second threshold is UNVERIFIED.
## Competing falsifiable hypotheses
H1 Model elected response termination with outstanding tasks; test multiple checkpoints in same execution and record whether a final response is produced while work remains. Cannot infer hidden model decision mechanism from visible final alone.
H2 Host-enforced time/output limit; test repeated sessions with client-side time stamps and timeout reason; require matching service/error evidence.
H3 Tool/connector latency correlated with stop; measure via an independent monotonic clock *outside* restricted JS timing (e.g. GitHub CI with recorded timestamps or local wrapper) and correlate with client-side event.
H4 Delivery/stream timeout independent of GitHub; obtain redacted client network diagnostics and status incident ID, compare with same GitHub operations through direct CI.
H5 Conversation context load contributes; run controlled identical task in fresh and established conversations and record client delivered/failed status.
## Experimental safeguards
Change one variable, repeat conditions, denominator of sessions and exposure time, classify unknown delivery separately. Do not block 120 seconds just to simulate a heartbeat without transport capture. Current session only one observation, statistical before/after UNKNOWN. GitHub commits are evidence checkpoints not notification heartbeat.
## Workflow correction candidate
Small idempotent operations; expected-head fast-forward GitHub update; record start/intent BEFORE blocking calls; after ambiguous outcome inspect remote state rather than retry; avoid long tool calls; substantive user updates; fresh session resumes canonical PROJECT_STATE.md. This mitigates loss/duplication but does not establish delivery protection.
## Final questions (status)
Why/when/trigger/how? UNKNOWN for message delivery; parser errors identified. Reproducible? Parser behavior not yet reliably replicated under controlled isolated calls. Voluntary vs external? No proof of platform-forced termination; earlier assistant voluntarily emitted final replies with outstanding work. Workaround? Checkpointing/reconciliation tested; delivery impact unproven. OpenAI intervention? Required to diagnose internal transport if client logs demonstrate server failure; not yet established.

## Update following checkpoint B
The second observed multi-call wrapper problem strengthens the **harness issue** hypothesis but cannot distinguish connector dispatch from response adaptation; a standalone read succeeded. Separate the results into transport delivery, tool response, parsing and engineering oracle outcomes. The deterministic burst-reference 1000/1000 result validates only software byte accounting, not ChatGPT runtime continuity. This session has not terminated as of this checkpoint. T4 and T7 require client observation or separate controlled conversations. No pre/post interruption-rate inference justified.

## Corrected interpretation C
Earlier local parser errors do not justify request-level GitHub failure counts. Third three-call loop succeeded. A 40-second GitHub CI job is an external job duration, not a connector latency measurement. Test T4/T7 require external client receipt telemetry and separate comparable sessions. No measured platform timeout mechanism.

## Checkpoint D — separation of evidence
- **GitHub external execution:** 10/10 independent process test runs passed on actual GitHub runner, 2,515,920 bytes checked. This supports independent engineering continuity but does not exercise ChatGPT conversation lifecycle.
- **OpenAI public status:** Current aggregate page reports operational. A resolved 2026-11-05 Work incident exists, but no evidence aligns it with this user's observed errors. No published 180-second idle cutoff verified. No causal attribution.
- **Session-level analysis:** analytics script calculates Wilson 95% confidence interval for observed timeout proportions; unknown outcomes excluded rather than imputed. Empty template yields no denominator; no before/after claim.
- **Test 4 design:** counterbalance 30s, 60s, 120s and normal conditions across comparable tasks and clients; require actual message send and receive timestamps, durations, explicit error strings, and at least repeated sessions per group. 120s progress updates may violate user's <=60s mitigation directive: test only in a controlled diagnostic session if knowingly authorized, never inside production G1 work.
- **Test 7 design:** exact same workload/configuration in established and fresh conversation. This execution cannot start and observe a fresh ChatGPT client thread; marked NOT RUN, not evidence of failure.

## Causal separation checkpoint — 2026-11-24
OBSERVED RESPONSE TERMINATION: Earlier assistant replies in this conversation explicitly announced their own end and produced a final response while engineering tasks remained; a model-generated end-of-response decision is observable. Hidden causes behind selecting that decision (instruction conflict, host pressure, model preference) are NOT. This is not the same as the user's observed UI string “Message delivery timed out.”
OBSERVED DELIVERY TIMEOUT: user report only. No matching request ID/client HAR/server trace or independently observed timestamp; underlying cause UNKNOWN.
GITHUB: validated external CI 45446985000 proves independent job continuity across 10 independent processes. It cannot implicate the message transport.
OFFICIAL STATUS: https://status.openai.com/ indicated currently operational when searched; resolved incidents including https://status.openai.com/incidents/01M6P50GPP1V98EF8MJ9SH393R confirm historical Work failures, not a cause for this session.
WORKFLOW MITIGATION: avoid unnecessary final messages while work remains, persist results at explicit checkpoints, prefer bounded tool calls, verify ambiguous external operations before retry. These reduce interruption cost; cannot override client/server termination and don't measure prevention success.

## Updated falsification boundary G
Observed active execution persisted approximately seven minutes with external CI and repeated GitHub checkpoint operations. A universal forced 180-second **total-turn** timeout is inconsistent with this single session. A **180-second inactivity** timeout remains UNTESTED because messages/calls occurred during the period and client reception was not instrumented. Prior GPT-6 status incident is not proof of a causal link. Deliberate assistant final replies and client delivery errors must not be conflated.
