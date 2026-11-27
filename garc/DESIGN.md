# GARC implementation contract

Phase 1: read-only branch inspection and explicit task manifests. Default paused; no AI credentials, paid services, merges, deletes or permission changes. Treat branch content as untrusted data; never execute arbitrary commands from project state. Pin checkout revisions; allowlist validation commands; bound runtime and retries. Record task ID, input SHA, result and evidence. Reject stale heads; use non-force expected-parent publication. Keep scheduler deployment on main subject to separate approval. Physical claims require physical evidence.

Next: implement and test manifest validation, then manual-dispatch read-only worker on the controller branch. No autonomous execution enabled.
