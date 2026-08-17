#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
project_dir="$(CDPATH= cd -- "$script_dir/.." && pwd)"

if [[ -f "$project_dir/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "$project_dir/.env"
  set +a
fi

webhook_url="${FIGMA_WEBHOOK_ENDPOINT:-${WEBHOOK_URL:-http://localhost:5678/}webhook/figma-ready-for-dev}"
passcode="${FIGMA_WEBHOOK_PASSCODE:-replace-with-local-passcode}"

make_payload() {
  python3 - "$1" "$2" "$3" <<'PY'
import json
import sys

event_type, status, passcode = sys.argv[1:]
payload = {
    "event_type": event_type,
    "file_key": "test-file",
    "node_id": "43:2",
    "status": status,
    "change_message": "Checkout flow is ready",
    "passcode": passcode,
    "timestamp": "2026-08-17T20:00:00Z",
    "triggered_by": {"id": "designer-test", "handle": "Designer Test"},
    "webhook_id": "local-test",
}
print(json.dumps(payload))
PY
}

post_expect() {
  local label="$1"
  local expected_status="$2"
  local payload="$3"
  local response_file
  local actual_status
  response_file=$(mktemp)
  actual_status=$(curl --silent --show-error --output "$response_file" --write-out '%{http_code}' \
    --request POST "$webhook_url" \
    --header 'Content-Type: application/json' \
    --data "$payload")
  if [[ "$actual_status" != "$expected_status" ]]; then
    printf 'Falha em %s: esperado HTTP %s, recebido HTTP %s\n' "$label" "$expected_status" "$actual_status" >&2
    cat "$response_file" >&2
    rm -f "$response_file"
    exit 1
  fi
  rm -f "$response_file"
  printf 'OK: %s (HTTP %s)\n' "$label" "$actual_status"
}

post_expect 'passcode inválido' '400' "$(make_payload DEV_MODE_STATUS_UPDATE READY_FOR_DEV wrong-passcode)"
post_expect 'PING sem publicação' '200' "$(make_payload PING NONE "$passcode")"
post_expect 'COMPLETED sem publicação' '200' "$(make_payload DEV_MODE_STATUS_UPDATE COMPLETED "$passcode")"
post_expect 'NONE sem publicação' '200' "$(make_payload DEV_MODE_STATUS_UPDATE NONE "$passcode")"
post_expect 'evento desconhecido sem publicação' '200' "$(make_payload UNKNOWN NONE "$passcode")"
post_expect 'READY_FOR_DEV primeira entrega' '200' "$(make_payload DEV_MODE_STATUS_UPDATE READY_FOR_DEV "$passcode")"
post_expect 'READY_FOR_DEV retry deduplicado' '200' "$(make_payload DEV_MODE_STATUS_UPDATE READY_FOR_DEV "$passcode")"

printf '%s\n' 'Teste enviado. Confirme uma única mensagem no Discord e sete execuções no n8n.'
