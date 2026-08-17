#!/usr/bin/env python3
"""List Figma webhooks while keeping passcodes and tokens out of the output."""

from __future__ import annotations

import sys

from figma_api import fail, load_dotenv, request, required_env


def main() -> int:
    load_dotenv()
    try:
        context = required_env("FIGMA_CONTEXT_TYPE").lower()
        if context not in {"file", "project", "team"}:
            raise ValueError("FIGMA_CONTEXT_TYPE deve ser file, project ou team")
        result = request(
            "GET",
            "/webhooks",
            params={"context": context, "context_id": required_env("FIGMA_CONTEXT_ID")},
        )
        webhooks = result.get("webhooks", [])
        if not webhooks:
            print("Nenhum webhook encontrado.")
            return 0
        for webhook in webhooks:
            print(
                "id={id} status={status} event={event} context={context}:{context_id} "
                "endpoint={endpoint} description={description}".format(
                    id=webhook.get("id", "<desconhecido>"),
                    status=webhook.get("status", "<desconhecido>"),
                    event=webhook.get("event_type", "<desconhecido>"),
                    context=webhook.get("context", "<desconhecido>"),
                    context_id=webhook.get("context_id", "<desconhecido>"),
                    endpoint=webhook.get("endpoint", "<desconhecido>"),
                    description=webhook.get("description", ""),
                )
            )
        return 0
    except (ValueError, RuntimeError) as error:
        return fail(str(error))


if __name__ == "__main__":
    sys.exit(main())
