"""Validate persistent queue; read-only until explicit worker deployment."""
import json
from pathlib import Path
from controller import BRANCHES
from manifest import eligible

def plan(queue, heads, completed):
    if not isinstance(queue, dict) or set(queue) != {"version","paused","tasks"}:
        raise ValueError("Invalid queue")
    if queue["version"] != 1 or type(queue["paused"]) is not bool or not isinstance(queue["tasks"], list):
        raise ValueError("Invalid queue schema")
    if len(queue["tasks"]) > 100:
        raise ValueError("Queue exceeds budget")
    seen = set()
    ready = []
    for entry in queue["tasks"]:
        if not isinstance(entry, dict) or set(entry) != {"branch","task"}:
            raise ValueError("Invalid entry")
        branch, task = entry["branch"], entry["task"]
        if branch not in BRANCHES or not isinstance(task, dict):
            raise ValueError("Invalid branch or task")
        ident = task.get("id")
        if not isinstance(ident, str) or ident in seen:
            raise ValueError("Invalid or duplicate task ID")
        seen.add(ident)
        if eligible(task, heads.get(branch), completed):
            ready.append(entry)
    return [] if queue["paused"] else ready

if __name__ == "__main__":
    queue = json.loads(Path(__file__).with_name("queue.json").read_text())
    plan(queue, {}, set())
    print("Queue schema validated; no engineering writes enabled")
