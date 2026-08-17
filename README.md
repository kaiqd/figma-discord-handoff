# Hands On — Figma para Discord

POC de handoff operacional: quando uma tela, seção ou componente for marcado como
**Ready for dev** no Figma, o n8n envia um embed para o canal `#ready-for-dev` no Discord.

O n8n será configurado por último e hospedado na VPS. Este repositório já contém os
artefatos versionáveis para essa etapa, mas nenhum container ou credencial é iniciado
localmente por padrão.

## Fluxo

```text
Figma Webhooks V2 → n8n → Discord REST API
```

O workflow aceita `PING`, mas não publica; publica somente `DEV_MODE_STATUS_UPDATE` com
`status=READY_FOR_DEV`. Também valida o passcode e usa uma chave idempotente para evitar
duplicidade em retries.

## Preparação local

1. Copie `.env.example` para `.env` e preencha os valores apenas no ambiente seguro.
2. Execute `make validate` para validar a estrutura e o JSON do workflow.
3. Não execute `make up` ainda: ele é a etapa final e deve ser executado na VPS.

Os scripts do Figma usam apenas a biblioteca padrão do Python:

```bash
make register-webhook
make list-webhooks
make remove-webhook ID=<webhook-id>
```

O token do Figma precisa da permissão `webhooks:write` para criar/remover e `webhooks:read`
para listar. Os scripts nunca exibem tokens ou passcodes.

## Configuração final na VPS

Consulte [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) para o passo a passo completo.
A sequência final é:

1. Instalar Docker e Docker Compose na VPS.
2. Criar `.env` na VPS e gerar uma `N8N_ENCRYPTION_KEY` estável.
3. Revisar `infra/compose.yaml` e iniciar com `make up`.
4. Criar no n8n a credencial **Header Auth** `Authorization: Bot <DISCORD_BOT_TOKEN>`.
5. Criar outra credencial **Header Auth** `X-Figma-Token: <FIGMA_TOKEN>` para a consulta
   opcional do nome do arquivo.
6. Importar `n8n/workflows/figma-ready-for-dev.json`.
7. Configurar a URL pública HTTPS, testar o Discord e executar `make test-webhook`.
8. Só então executar `make register-webhook` para cadastrar o endpoint no Figma.

Nunca versionar `.env`, tokens, credenciais exportadas ou o estado do n8n. Se um segredo
for exposto, revogue-o e gere outro.
