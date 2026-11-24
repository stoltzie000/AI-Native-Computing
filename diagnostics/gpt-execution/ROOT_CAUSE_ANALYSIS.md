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
