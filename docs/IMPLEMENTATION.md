# Hands On — Guia de implementação

## 1. Objetivo

O **Hands On** transforma o handoff do Figma em uma notificação operacional no Discord.
Quando uma tela, seção ou componente for marcado como **Ready for dev**, o Figma enviará
um webhook ao n8n. O workflow validará o evento, enriquecerá os dados quando necessário e
publicará a notificação no canal da equipe usando a identidade do bot **Hands On**.

```text
Designer marca “Ready for dev”
               |
               v
Figma Webhooks V2
               |
               v
n8n self-hosted
  - valida o passcode
  - filtra READY_FOR_DEV
  - evita duplicidade
  - formata a mensagem
               |
               v
Discord API
               |
               v
#ready-for-dev
```

## 2. Escopo da POC

A primeira versão deverá:

- Monitorar um arquivo ou projeto do Figma.
- Receber o evento `DEV_MODE_STATUS_UPDATE`.
- Publicar somente quando `status` for `READY_FOR_DEV`.
- Ignorar `PING`, `COMPLETED`, `NONE` e outros eventos.
- Validar o `passcode` enviado pelo Figma.
- Publicar nome do arquivo, responsável, descrição e link do Figma no Discord.
- Evitar notificações duplicadas causadas por retries do webhook.
- Registrar execuções e falhas no n8n.

Não fazem parte da POC inicial:

- Ler mensagens do Discord.
- Slash commands.
- Botões como “Assumir” ou “Concluir”.
- Atualizar o status no Figma a partir do Discord.
- Sincronizar automaticamente código e design.

Essas funcionalidades poderão ser adicionadas em `apps/discord-bot` após a validação do
fluxo unidirecional.

## 3. Estrutura do repositório

```text
figma-discord-handoff/
├── apps/
│   └── discord-bot/          # Futuro serviço interativo do Discord
├── docs/
│   └── IMPLEMENTATION.md     # Este guia
├── infra/
│   ├── compose.yaml          # n8n, PostgreSQL e proxy/túnel
│   └── caddy/                # Proxy HTTPS, quando utilizado
├── n8n/
│   └── workflows/
│       └── figma-ready-for-dev.json
├── scripts/
│   ├── register_figma_webhook.py
│   ├── list_figma_webhooks.py
│   ├── remove_figma_webhook.py
│   └── test_webhook.sh
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```

### Responsabilidades

- `infra/`: ambiente reproduzível e configuração de deployment.
- `n8n/workflows/`: workflows exportados e versionados como JSON.
- `scripts/`: cadastro, inspeção e remoção dos webhooks do Figma.
- `apps/discord-bot/`: reservado para interações bidirecionais futuras.
- `docs/`: arquitetura, decisões e operação do projeto.

Na POC, não é necessário executar um processo permanente para o bot. O n8n chamará a API
REST do Discord com o bot token; as mensagens continuarão sendo publicadas pelo **Hands On**.

## 4. Pré-requisitos

- Docker e Docker Compose.
- Aplicação **Hands On** criada no Discord.
- Bot instalado no servidor com as permissões:
  - View Channels
  - Send Messages
  - Embed Links
- ID do canal de destino.
- Token do bot do Discord.
- Token do Figma com `webhooks:write`.
- `file_content:read` no token do Figma caso o workflow consulte nomes e metadados dos nodes.
- URL HTTPS pública para o endpoint do n8n.

## 5. Variáveis e segredos

O `.env.example` deverá documentar apenas nomes e valores não sensíveis:

```dotenv
# Discord
DISCORD_APPLICATION_ID=
DISCORD_CHANNEL_ID=
DISCORD_BOT_TOKEN=

# Figma
FIGMA_TOKEN=
FIGMA_CONTEXT_TYPE=file
FIGMA_CONTEXT_ID=
FIGMA_WEBHOOK_PASSCODE=

# n8n
N8N_HOST=localhost
N8N_PROTOCOL=http
N8N_PORT=5678
N8N_ENCRYPTION_KEY=
WEBHOOK_URL=http://localhost:5678/

# PostgreSQL
POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=
```

Regras:

- `.env` nunca entra no Git.
- O bot token deve ser armazenado em uma credencial criptografada do n8n.
- `N8N_ENCRYPTION_KEY` deve ser estável e armazenado no gerenciador de segredos do ambiente.
- Tokens de produção não devem ser usados em testes locais compartilhados.
- Qualquer token exposto deve ser revogado e substituído.

## 6. Fases de implementação

### Fase 1 — Infraestrutura local

Criar `infra/compose.yaml` com:

- `n8n`, fixando uma versão da imagem em vez de usar `latest`.
- `postgres`, com health check e volume persistente.
- Volume persistente para os dados do n8n.
- Rede interna entre n8n e PostgreSQL.

Resultado esperado:

```text
http://localhost:5678
```

O n8n deve reiniciar sem perder workflows ou credenciais.

### Fase 2 — Credencial do Discord

No n8n, criar uma credencial do tipo **Header Auth**:

```text
Name: Authorization
Value: Bot <DISCORD_BOT_TOKEN>
```

Executar um node HTTP Request isolado:

```text
POST https://discord.com/api/v10/channels/<DISCORD_CHANNEL_ID>/messages
```

Body de teste:

```json
{
  "content": "🛠️ **Hands On is online!**\nFrom handoff to hands-on."
}
```

Essa fase termina quando a mensagem aparecer no canal enviada pelo bot.

### Fase 3 — Workflow do n8n

Criar o workflow `Figma — Ready for dev` com os nodes:

1. **Webhook — Figma events**
   - Método: `POST`
   - Path: `figma-ready-for-dev`
   - Resposta: imediatamente com HTTP `200`
2. **Validate passcode**
   - Comparar `body.passcode` com o segredo configurado.
   - Encerrar a execução caso seja inválido.
3. **Route event**
   - `PING`: aceitar sem publicar.
   - `DEV_MODE_STATUS_UPDATE`: continuar.
   - Demais eventos: ignorar.
4. **Filter READY_FOR_DEV**
   - Continuar somente se `body.status == "READY_FOR_DEV"`.
5. **Deduplicate**
   - Gerar uma chave idempotente com os campos do evento.
   - Não publicar uma chave já processada.
6. **Build Discord message**
   - Normalizar dados e construir o payload.
7. **Send message to Discord**
   - Chamar a API do Discord com a credencial do bot.
8. **Record result**
   - Registrar sucesso ou erro para diagnóstico.

### Fase 4 — Teste do webhook sem Figma

Com o workflow ativo, testar primeiro com um payload controlado:

```bash
curl --fail-with-body \
  --request POST \
  "http://localhost:5678/webhook/figma-ready-for-dev" \
  --header "Content-Type: application/json" \
  --data '{
    "event_type": "DEV_MODE_STATUS_UPDATE",
    "file_key": "test-file",
    "file_name": "Hands On Test",
    "node_id": "43:2",
    "status": "READY_FOR_DEV",
    "change_message": "Checkout flow is ready",
    "passcode": "replace-with-local-passcode",
    "timestamp": "2026-08-17T20:00:00Z",
    "triggered_by": {
      "id": "designer-test",
      "handle": "Designer Test"
    },
    "webhook_id": "local-test"
  }'
```

Executar o mesmo comando duas vezes. A primeira execução deve publicar uma mensagem; a
segunda deve ser identificada como duplicada.

### Fase 5 — Endpoint HTTPS público

O Figma precisa alcançar o n8n por uma URL HTTPS pública.

Para desenvolvimento, utilizar um túnel temporário. Para ambiente persistente, utilizar
domínio próprio e proxy reverso, como Caddy ou Traefik.

Configurações importantes do n8n em produção:

```dotenv
N8N_HOST=automation.example.com
N8N_PROTOCOL=https
WEBHOOK_URL=https://automation.example.com/
N8N_PROXY_HOPS=1
```

O editor do n8n não deve ficar publicamente acessível sem autenticação e TLS.

### Fase 6 — Registro do webhook no Figma

Implementar `scripts/register_figma_webhook.py` para chamar:

```text
POST https://api.figma.com/v2/webhooks
```

Payload:

```json
{
  "event_type": "DEV_MODE_STATUS_UPDATE",
  "context": "file",
  "context_id": "<FIGMA_CONTEXT_ID>",
  "endpoint": "https://automation.example.com/webhook/figma-ready-for-dev",
  "passcode": "<FIGMA_WEBHOOK_PASSCODE>",
  "status": "ACTIVE",
  "description": "Hands On — Ready for dev notifications"
}
```

O script deve:

- Ler configurações do ambiente.
- Nunca imprimir tokens.
- Validar parâmetros obrigatórios.
- Tratar respostas `400`, `403` e `404` com mensagens úteis.
- Exibir apenas o ID e o status do webhook criado.

Ao cadastrar o webhook, o Figma enviará um `PING`. A execução precisa retornar `200`, sem
publicar mensagem no Discord.

### Fase 7 — Teste de ponta a ponta

1. Abrir o arquivo configurado no Figma.
2. Marcar uma tela ou seção como **Ready for dev**.
3. Confirmar o recebimento no histórico de execuções do n8n.
4. Confirmar a notificação no canal do Discord.
5. Conferir responsável, descrição e link.
6. Repetir a alteração e verificar a política de duplicidade.

## 7. Contrato do evento recebido

Campos principais utilizados:

| Campo | Uso |
| --- | --- |
| `event_type` | Seleciona o fluxo do evento. |
| `status` | Publica apenas `READY_FOR_DEV`. |
| `file_key` | Identifica o arquivo e auxilia na criação do link. |
| `file_name` | Nome exibido na mensagem, quando presente. |
| `node_id` | Identifica a tela, seção ou componente. |
| `change_message` | Contexto escrito pelo designer. |
| `triggered_by.handle` | Responsável pelo handoff. |
| `timestamp` | Auditoria e deduplicação. |
| `webhook_id` | Auditoria e deduplicação. |
| `passcode` | Validação básica da origem. |

Caso o payload não traga o nome do node, o workflow poderá consultar a API de nodes do
Figma usando `file_key` e `node_id` antes de montar a mensagem.

## 8. Formato da mensagem no Discord

Preferir embed em vez de texto solto:

```json
{
  "embeds": [
    {
      "title": "Ready for development",
      "description": "Checkout flow is ready",
      "color": 5763719,
      "fields": [
        {
          "name": "File",
          "value": "E-commerce App",
          "inline": true
        },
        {
          "name": "Handed off by",
          "value": "Designer Name",
          "inline": true
        }
      ],
      "footer": {
        "text": "Hands On · From handoff to hands-on"
      }
    }
  ],
  "allowed_mentions": {
    "parse": []
  }
}
```

`allowed_mentions.parse` vazio evita menções inesperadas vindas de textos do Figma.

## 9. Idempotência e retries

O Figma pode reenviar um webhook quando não recebe uma resposta válida. A aplicação deverá
considerar o processamento idempotente.

Chave sugerida:

```text
webhook_id:event_type:file_key:node_id:status:timestamp
```

Para a POC, a chave pode ser armazenada em uma Data Table do n8n ou no PostgreSQL. Em uma
versão posterior, registrar também o ID da mensagem criada no Discord permite atualizar a
mensagem existente em vez de criar outra.

## 10. Segurança mínima

- Responder rapidamente ao webhook e executar o restante do fluxo de forma desacoplada.
- Rejeitar ou encerrar silenciosamente eventos com `passcode` inválido.
- Não registrar bot token, Figma token ou passcode nos logs.
- Usar HTTPS no endpoint público.
- Fixar versões das imagens Docker.
- Manter PostgreSQL apenas na rede interna do Compose.
- Conceder ao bot somente permissões necessárias no canal.
- Configurar retenção limitada para dados de execução do n8n.
- Fazer backup do banco e da `N8N_ENCRYPTION_KEY` em ambientes persistentes.

## 11. Makefile sugerido

Alvos esperados:

```text
make up                 # sobe o ambiente
make down               # encerra o ambiente
make logs               # acompanha logs do n8n
make test-webhook       # envia o evento local de teste
make register-webhook   # registra o webhook no Figma
make list-webhooks      # lista webhooks do contexto
make export-workflows   # exporta workflows para n8n/workflows
make import-workflows   # importa workflows versionados
```

## 12. Critérios de aceite

A POC estará concluída quando todos os itens abaixo forem verdadeiros:

- [ ] O ambiente sobe com um único comando.
- [ ] O n8n persiste dados após reinicialização.
- [ ] O endpoint público responde HTTP `200` ao `PING` do Figma.
- [ ] Passcode inválido não produz mensagem.
- [ ] `READY_FOR_DEV` produz exatamente uma mensagem no canal correto.
- [ ] `COMPLETED`, `NONE` e eventos desconhecidos não produzem mensagem.
- [ ] Retry do mesmo evento não duplica a notificação.
- [ ] A mensagem apresenta contexto suficiente e link para o Figma.
- [ ] Nenhum segredo está versionado no Git.
- [ ] O workflow exportado está em `n8n/workflows/`.
- [ ] O procedimento de setup está documentado no `README.md`.

## 13. Evoluções após a POC

- Criar thread por tela entregue.
- Adicionar botão “Claim task”.
- Associar desenvolvedor responsável ao handoff.
- Publicar alterações feitas depois do handoff.
- Tratar o status `COMPLETED` e atualizar a mensagem original.
- Adicionar slash commands para consultar designs pendentes.
- Integrar GitHub, Linear ou Jira por meio de `related_links`.
- Adicionar métricas de tempo entre `READY_FOR_DEV` e `COMPLETED`.
- Executar um serviço dedicado em `apps/discord-bot` quando forem necessárias interações
  recebidas do Discord.

## 14. Referências

- [Figma — Webhooks V2](https://developers.figma.com/docs/rest-api/webhooks/)
- [Figma — Webhook events](https://developers.figma.com/docs/rest-api/webhooks-events/)
- [Figma — Webhook endpoints](https://developers.figma.com/docs/rest-api/webhooks-endpoints/)
- [Discord — Bots](https://docs.discord.com/developers/bots/overview)
- [Discord — Webhook and message resources](https://docs.discord.com/developers/resources/webhook)
- [n8n — Documentation](https://docs.n8n.io/)
