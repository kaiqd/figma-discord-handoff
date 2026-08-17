#!/usr/bin/env python3
"""Validate repository artifacts without requiring Docker, n8n, or network access."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = [
        ".env.example",
        ".gitignore",
        "infra/compose.yaml",
        "infra/stack.yaml",
        "n8n/workflows/figma-ready-for-dev.json",
        "scripts/register_figma_webhook.py",
        "scripts/list_figma_webhooks.py",
        "scripts/remove_figma_webhook.py",
        "scripts/test_webhook.sh",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    if missing:
        print(f"Arquivos ausentes: {', '.join(missing)}", file=sys.stderr)
        return 1

    workflow_path = ROOT / "n8n/workflows/figma-ready-for-dev.json"
    try:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"Workflow JSON inválido: {error}", file=sys.stderr)
        return 1

    node_names = {node.get("name") for node in workflow.get("nodes", [])}
    expected_nodes = {
        "Webhook — Figma events",
        "Validate passcode",
        "Route event",
        "Filter READY_FOR_DEV",
        "Deduplicate",
        "Build Discord message",
        "Send message to Discord",
        "Record result",
    }
    if not expected_nodes.issubset(node_names):
        print(f"Nodes ausentes no workflow: {sorted(expected_nodes - node_names)}", file=sys.stderr)
        return 1

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    forbidden = ["Bot ", "xoxb-", "ghp_", "sk-"]
    if any(marker in env_example for marker in forbidden):
        print("Possível segredo encontrado em .env.example", file=sys.stderr)
        return 1

    test_script = ROOT / "scripts/test_webhook.sh"
    if not (test_script.stat().st_mode & stat.S_IXUSR):
        print("scripts/test_webhook.sh não está executável", file=sys.stderr)
        return 1

    print(f"OK: {len(workflow['nodes'])} nodes no workflow; artefatos básicos válidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
