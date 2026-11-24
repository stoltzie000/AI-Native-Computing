# Controlled client-side investigation protocol — pending, NOT executed
Scope: ChatGPT Work message delivery and model response lifecycle, isolated from production G1 work.

## Required client-observable record
For each conversation run: anonymized session_id, model menu and effort, exact Work/Instant client mode, client platform/browser build, conversation classification (new/established), intended progress cadence, start/end timestamp with timezone, last server-sent and client-received message times, exact visible error, number of operations and successfully returned connector calls, tool invocation and response timestamps, final response present/absent, remaining authorized work, user intervention, and outcome success/timeout/other_error/unknown.
Do not collect conversation content, tokens, cookies, secrets, authenticated HAR, personal contact info or identifying thread URLs in the public GitHub repository. Redact private artifacts before sharing.

## T4 reporting frequency controlled design
- Four variants: substantive progress every ~30 seconds, ~60 seconds, ~120 seconds, or unconstrained. Implement 120s only inside an explicitly controlled diagnostic session, not production engineering where the <=60s progress directive remains in force.
- Match workload, tool budget, context length, client, model/effort and network as closely as possible. Randomize/counterbalance order; include at least five observed runs/variant initially (20 runs, exploratory and underpowered). Do not claim causality on five runs.
- Require actual client receipt timestamp, not assistant-authored timestamp or GitHub CI clock. Record missed/late messages and deliveries distinctly. If timing was not imposed or reception not observed, set condition UNTESTED/UNKNOWN, not success.
- Compute proportion observed timed-out among delivered/failed observations using analyze_delivery.py; keep unknown separate, report Wilson 95% intervals and observed exposure hours; compare confidence intervals and confounders, never assert a fixed cutoff from a single failure.

## T7 conversation lifecycle
- Counterbalanced paired fresh/established conversations, identical deterministic read-only workload, same client, model/effort and tool access. Record context length proxy (message count/file count), not personal content.
- Need separate ChatGPT client conversations and independent client outcome observation. This assistant cannot create or observe a new Work conversation from its current tools; UNTESTED pending available client-side execution.

## T6 tool-latency controls
- Use external monotonic client instrumentation for request start/end and response arrival. GitHub CI run timestamps measure external job duration only. Tool-side JS clock results of 0ms were invalid/unreliable; never compute connector latency from them.
- Correlate exact delivery timeout with overlapping connector calls only after obtaining both timelines. A connector failure and stream failure may occur independently.

## Stop mechanism interpretation
- A visible assistant 'final' turn with remaining work indicates assistant-visible response termination; it does not reveal internal policy selection or server-enforced cause.
- A client UI showing 'Message delivery timed out' without a valid final response is a different outcome, requiring transport/error logs to distinguish failure source.
- GitHub CI running after response end proves GitHub independence, not Work session continuity.
- Never treat work completion as timeout, or every model final as a platform failure.

## Acceptance
Document direct client errors and reproducible matched trials before attributing to platform; preserve all missing fields as UNKNOWN. Re-run tests with one variable changed at a time. This protocol does not itself collect client telemetry.
