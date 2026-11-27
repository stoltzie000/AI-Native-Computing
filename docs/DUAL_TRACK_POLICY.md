# Dual-track research and continuity policy

**Purpose.** Advance the AI-native computer through two independent, evidence-gated paths while preserving the separate investigation into ChatGPT execution and delivery failures. The continuity procedure protects project progress; it cannot alter ChatGPT's hosted runtime.

## Track A — engineering evidence
**Working branch:** `research/g13-qact-offset`

Build and validate concrete RTL, memory interfaces, and FPGA-ready designs. Preserve exact numerical behavior and failed runs. Separate RTL simulation, synthesis estimates, routed timing, board measurements, and workload benchmarks. Never represent proxy results as physical performance.

**Current verified signal (2026-11-27):** At commit `440aa834fe80898a6f4571d54fc8815272cad77b`, GitHub Actions run `45641131479` passed numerical/memory and 6.25 MHz bring-up checks, but the 100 MHz full-rate route failed at an estimated 19.232 MHz. This is a material timing miss, not a ChatGPT or GitHub transport failure. The next engineering step is to inspect the preserved timing reports, isolate the QACT scaling/rounding path, and run a bit-equivalent experiment against the existing paired control. Do not merge.

## Track B — breakthrough architecture research
**Working branch:** `research/architectural-breakthrough`

Test alternatives beyond conventional GPU assumptions, including new data representations, memory placement, execution order, processor, and whole-system topology. Each proposal must state:
1. A falsifiable hypothesis and a named independent control.
2. Required workload, quality, data, and physical boundaries.
3. A measurable pass threshold and a rejection rule.
4. The evidence artifact and exact commit that support the result.

Start with the prioritized roadmap already in `research/prior_art_2026_11_23/EXPERIMENTAL_ROADMAP_AND_RISK_REGISTER.md`. Its P0 G1 activation audit is the next high-information experiment. It must measure real trained-model activations before activation-gated RTL receives more optimization. Keep dense negative controls and synthetic sparse positive controls separate from real-model evidence. Preserve negative outcomes.

## Separate diagnostic track — ChatGPT continuity
**Working branch:** `research/gpt-execution-diagnostics-20261124`

Keep client delivery, assistant response termination, connector/tool failures, and repository/CI outcomes as separate event classes. Existing tests establish that arithmetic and GitHub workflows can succeed and that some supplied test responses ended early; they do not identify the hidden cause of a ChatGPT delivery timeout. No client HAR, server trace, request ID, or controlled fresh-versus-established conversation receipt record is present in the repo.

OpenAI's current troubleshooting guidance says that when a ChatGPT issue persists across browsers, devices, and networks, collect a sanitized HAR and browser console errors with timestamps, note the model and conversation identifier, and contact Support. Keep these private artifacts out of the public repo. An alternative durable application can use the Agents API's persisted sessions and retrieve saved items after a disconnected stream; this is a separate API application, not a repair to ChatGPT Work. API usage is billed separately from ChatGPT, so do not create or run API-billed work without explicit approval.

References:
- https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages
- https://help.openai.com/en/articles/6614161-how-can-i-contact-support
- https://developers.openai.com/api/docs/guides/agents-api/sessions
- https://developers.openai.com/api/docs/guides/agents-api/sessions/events
- https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform

## Shared execution and continuity rules
- On resume, read this policy and the branch's `PROJECT_STATE.md`; independently verify the remote branch head before work.
- Execute the next bounded action when it is safe and authorized. Do not stop at a status-only report while a safe action is available.
- Before a write, capture the intended parent and exact paths. Use a non-force expected-parent ref update. If a write response is ambiguous, inspect the branch and content before retrying.
- After an experiment, save the command, inputs, tool versions, outcome, limitations, and next action in the same track's state or evidence record.
- If one track needs user-only evidence, record the specific missing item and continue independent work on another track.
- Never merge unfinished research, overwrite prior evidence, expose credentials, change repository visibility, or claim that scheduled checks guarantee uninterrupted execution.
- No assistant prompt task number is assigned by this policy. Existing task-number continuity remains unresolved.

## Current gate
**ChatGPT platform cause: OPEN / UNKNOWN.** The project can provide a reproducer and private evidence for OpenAI Support; only OpenAI can inspect private service-side traces. The engineering and breakthrough tracks continue independently.
