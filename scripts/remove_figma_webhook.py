#!/usr/bin/env python3
"""Delete one Figma webhook by ID."""

from __future__ import annotations

import sys

from figma_api import fail, load_dotenv, request


def main() -> int:
    load_dotenv()
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        return fail("Uso: python3 scripts/remove_figma_webhook.py <webhook-id>")
    webhook_id = sys.argv[1].strip()
    try:
        result = request("DELETE", f"/webhooks/{webhook_id}")
        print(f"Webhook removido: id={result.get('id', webhook_id)} status={result.get('status', 'deleted')}")
        return 0
    except (ValueError, RuntimeError) as error:
        return fail(str(error))


if __name__ == "__main__":
    sys.exit(main())
