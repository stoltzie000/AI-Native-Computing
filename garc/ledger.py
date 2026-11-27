"""Append-only local evidence; durable publication is a separate operation."""
import json
from pathlib import Path
def load(path):
    p = Path(path)
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []
def append(path, record):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
def completed(records):
    return {(r["id"], r["sha"]) for r in records if r["status"] == "inspected"}
