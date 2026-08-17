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

payload=$(cat <<JSON
{
  "event_type": "DEV_MODE_STATUS_UPDATE",
  "file_key": "test-file",
  "file_name": "Hands On Test",
  "node_id": "43:2",
  "status": "READY_FOR_DEV",
  "change_message": "Checkout flow is ready",
  "passcode": "$passcode",
  "timestamp": "2026-08-17T20:00:00Z",
  "triggered_by": {
    "id": "designer-test",
    "handle": "Designer Test"
  },
  "webhook_id": "local-test"
}
JSON
)

printf '%s\n' 'Enviando o evento controlado (1/2)...'
curl --fail-with-body --silent --show-error \
  --request POST "$webhook_url" \
  --header 'Content-Type: application/json' \
  --data "$payload"
printf '\n%s\n' 'Enviando o mesmo evento novamente (2/2); deve ser deduplicado...'
curl --fail-with-body --silent --show-error \
  --request POST "$webhook_url" \
  --header 'Content-Type: application/json' \
  --data "$payload"
printf '\n%s\n' 'Teste enviado. Confirme uma única mensagem no Discord e duas execuções no n8n.'
