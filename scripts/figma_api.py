"""Small, dependency-free helpers for the Figma Webhooks V2 API."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE = "https://api.figma.com/v2"


def load_dotenv() -> None:
    """Load a local .env without overriding variables supplied by the shell."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Variável obrigatória ausente: {name}")
    return value


def request(method: str, path: str, *, params: dict[str, str] | None = None,
            payload: dict[str, Any] | None = None) -> dict[str, Any]:
    token = required_env("FIGMA_TOKEN")
    query = f"?{urlencode(params)}" if params else ""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_obj = Request(
        f"{API_BASE}{path}{query}",
        data=body,
        method=method,
        headers={
            "X-Figma-Token": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "hands-on-figma-discord/1.0",
        },
    )

    try:
        with urlopen(request_obj, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body) if response_body else {}
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        messages = {
            400: "Parâmetros inválidos. Confira FIGMA_CONTEXT_TYPE, FIGMA_CONTEXT_ID e o endpoint.",
            403: "Token inválido/expirado ou sem a permissão Figma necessária.",
            404: "Contexto ou webhook não encontrado, ou sem permissão para acessá-lo.",
        }
        friendly = messages.get(error.code, "A API do Figma retornou um erro inesperado.")
        # O corpo da API pode conter detalhes úteis, mas nunca imprimimos headers ou tokens.
        detail = detail[:500] if detail else "sem detalhes adicionais"
        raise RuntimeError(f"HTTP {error.code}: {friendly} Detalhe: {detail}") from None
    except URLError as error:
        raise RuntimeError(f"Não foi possível conectar à API do Figma: {error.reason}") from None


def fail(message: str) -> int:
    print(f"Erro: {message}", file=sys.stderr)
    return 2
