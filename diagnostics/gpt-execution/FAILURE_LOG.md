# GPT execution failure log
| Incident | Timestamp UTC | Observed failure | Class | Evidence | Cause | Confidence | Recovery |
|---|---|---|---|---|---|---|---|
| F-001 | 2026-11-24T17:14:40Z | Six local TypeErrors parsing missing response.result | Diagnostic harness | JavaScript parsing exceptions; no HTTP status or server logs | Response handling failed; GitHub cause not established | HIGH for parser failure, LOW underlying | Isolated PR call succeeded; revised parser |
| F-002 | 2026-11-24T17:14:48Z | Two local SyntaxErrors parsing undefined content | Diagnostic harness | Six-call sequence; isolated fetch later returned valid JSON | Missing/alternate response envelope unverified | MEDIUM | Avoid interpreting as connector outage; inspect raw responses |
| F-003 | UNKNOWN | User reports intermittent “Message delivery timed out” in extended engineering | ChatGPT client/transport UNKNOWN | User's report; no HAR, server trace, session ID or frequency denominator | UNKNOWN | UNKNOWN | Preserve checkpoints, retrieve client telemetry when available |
