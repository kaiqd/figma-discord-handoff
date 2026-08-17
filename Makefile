.PHONY: help validate up deploy-swarm down logs test-webhook register-webhook list-webhooks remove-webhook export-workflows import-workflows

SHELL := /bin/sh
COMPOSE := docker compose -f infra/compose.yaml
PYTHON ?= python3

help:
	@printf '%s\n' \
		'make validate          valida os artefatos versionados' \
		'make up                sobe o n8n na VPS (etapa final)' \
		'make deploy-swarm      sobe a stack hands-on no Docker Swarm' \
		'make down              encerra o ambiente n8n' \
		'make logs              acompanha os logs do n8n' \
		'make test-webhook      envia o payload controlado duas vezes' \
		'make register-webhook  registra o webhook no Figma' \
		'make list-webhooks     lista webhooks do contexto Figma' \
		'make remove-webhook ID remove um webhook pelo ID' \
		'make export-workflows  exporta workflows do n8n para n8n/workflows' \
		'make import-workflows  importa o workflow versionado no n8n'

validate:
	$(PYTHON) scripts/validate_project.py

# O n8n é deliberadamente a última etapa operacional. Execute estes alvos apenas na VPS.
up:
	$(COMPOSE) up -d

deploy-swarm:
	@test -f .env || (printf '%s\n' 'Crie o arquivo .env antes do deploy.' >&2; exit 2)
	@set -a; . ./.env; set +a; docker stack deploy -c infra/stack.yaml hands-on

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f n8n

test-webhook:
	./scripts/test_webhook.sh

register-webhook:
	$(PYTHON) scripts/register_figma_webhook.py

list-webhooks:
	$(PYTHON) scripts/list_figma_webhooks.py

remove-webhook:
	@test -n "$(ID)" || (printf '%s\n' 'Uso: make remove-webhook ID=<webhook-id>' >&2; exit 2)
	$(PYTHON) scripts/remove_figma_webhook.py "$(ID)"

export-workflows:
	@printf '%s\n' 'Exportação deve ser executada na VPS após configurar o n8n.'
	@printf '%s\n' 'Use: docker compose -f infra/compose.yaml exec n8n n8n export:workflow --all --output=/files/workflows.json'

import-workflows:
	@printf '%s\n' 'Importação deve ser executada na VPS após revisar credenciais.'
	@printf '%s\n' 'Use: docker compose -f infra/compose.yaml exec n8n n8n import:workflow --input=/files/figma-ready-for-dev.json'
