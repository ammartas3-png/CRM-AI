#!/usr/bin/env python3
"""Extract / inject the jsCode of an n8n Code node so it can be edited as a plain file.

    python3 scripts/node_code.py extract "Memory Match" /tmp/memory_match.js
    python3 scripts/node_code.py inject  "Memory Match" /tmp/memory_match.js

Editing the JS inside the workflow JSON directly is error prone (escaping, huge single
line), so rule work happens on the extracted file and is written back with `inject`.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / "n8n-import" / "05-V2-smart-upgraded.workflow.json"


def find(wf, name):
    for node in wf["nodes"]:
        if node["name"] == name:
            return node
    raise SystemExit(f"node not found: {name}")


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    action, name, target = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    wf = json.loads(WORKFLOW.read_text())
    node = find(wf, name)

    if action == "extract":
        target.write_text(node["parameters"]["jsCode"])
        print(f"extracted {name} -> {target} ({len(node['parameters']['jsCode'])} chars)")
    elif action == "inject":
        node["parameters"]["jsCode"] = target.read_text()
        WORKFLOW.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n")
        print(f"injected {target} -> {name}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
