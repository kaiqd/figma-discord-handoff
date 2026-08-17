#!/usr/bin/env python3
"""Register the Hands On Figma webhook without exposing secrets in output."""

from __future__ import annotations

import sys
from urllib.parse import urlparse

from figma_api import fail, load_dotenv, request, required_env


def main() -> int:
    load_dotenv()
    try:
        context = required_env("FIGMA_CONTEXT_TYPE").lower()
        if context not in {"file", "project", "team"}:
            raise ValueError("FIGMA_CONTEXT_TYPE deve ser file, project ou team")
        context_id = required_env("FIGMA_CONTEXT_ID")
        passcode = required_env("FIGMA_WEBHOOK_PASSCODE")
        endpoint = required_env("FIGMA_WEBHOOK_ENDPOINT")
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise ValueError("FIGMA_WEBHOOK_ENDPOINT deve usar HTTPS fora de localhost")
        if len(passcode) > 100:
            raise ValueError("FIGMA_WEBHOOK_PASSCODE deve ter no máximo 100 caracteres")
        if len(endpoint) > 2048:
            raise ValueError("FIGMA_WEBHOOK_ENDPOINT deve ter no máximo 2048 caracteres")

        result = request(
            "POST",
            "/webhooks",
            payload={
                "event_type": "DEV_MODE_STATUS_UPDATE",
                "context": context,
                "context_id": context_id,
                "endpoint": endpoint,
                "passcode": passcode,
                "status": "ACTIVE",
                "description": "Hands On — Ready for dev notifications",
            },
        )
        print(f"Webhook criado: id={result.get('id', '<não informado>')} status={result.get('status', '<não informado>')}")
        print("O Figma enviará um PING inicial; ele deve ser aceito sem publicar no Discord.")
        return 0
    except (ValueError, RuntimeError) as error:
        return fail(str(error))


if __name__ == "__main__":
    sys.exit(main())
