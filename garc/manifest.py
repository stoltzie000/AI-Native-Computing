"""Strict declarative task eligibility; never executes manifest content."""
import re
ALLOWED = {"inspect_state"}
def eligible(task, head, completed):
    if not isinstance(task, dict) or set(task) != {"id", "revision", "operation"}:
        return False
    return (isinstance(task["id"], str)
            and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", task["id"]) is not None
            and isinstance(head, str) and re.fullmatch(r"[0-9a-f]{40}", head) is not None
            and task["revision"] == head
            and isinstance(task["operation"], str)
            and task["operation"] in ALLOWED
            and (task["id"], head) not in completed)
