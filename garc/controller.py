"""Read-only, bounded branch inspection. No commands from branch content."""
import json, os, re, subprocess
from ledger import append

BRANCHES = ("research/g13-qact-offset", "research/architectural-breakthrough",
            "research/quantized-pipeline-g13", "research/g1-hbm4-controller-envelope",
            "research/gpt-execution-diagnostics-20261124")

def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True,
                          text=True, timeout=60).stdout

def inspect(branch):
    if branch not in BRANCHES:
        raise ValueError("Branch not allowed")
    ref = "refs/heads/" + branch
    git("fetch", "--no-tags", "--depth=1", "origin", ref)
    sha = git("rev-parse", "FETCH_HEAD").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid revision")
    blob = git("rev-parse", sha + ":PROJECT_STATE.md").strip()
    size = int(git("cat-file", "-s", blob))
    if size > 1000000:
        raise ValueError("State exceeds size budget")
    state = git("show", sha + ":PROJECT_STATE.md")
    current = git("ls-remote", "--exit-code", "origin", ref).split()[0]
    return {"branch": branch, "sha": sha, "state_blob": blob,
            "state_bytes": size, "state_present": bool(state.strip()),
            "status": "inspected" if current == sha else "stale",
            "engineering_write": False}

def main():
    if os.environ.get("GARC_ENABLED") != "true":
        print(json.dumps({"status": "paused"}))
        return
    results = []
    for branch in BRANCHES:
        try:
            results.append(inspect(branch))
        except (ValueError, subprocess.SubprocessError, IndexError) as exc:
            results.append({"branch": branch, "status": "blocked",
                            "error_type": type(exc).__name__})
    for result in results:
        append('garc-evidence.jsonl', dict(result, id='inspect-' + result['branch'].replace('/', '-')))
    print(json.dumps(results, indent=2))
    if any(x["status"] != "inspected" for x in results):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
