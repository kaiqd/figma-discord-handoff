# Hands On — Figma para Discord

Integração que envia uma mensagem formatada para o Discord quando uma tela, seção ou
componente do Figma é marcado como **Ready for dev**.

```text
Figma Webhooks V2 → n8n → Discord REST API
```

O workflow valida o passcode, aceita o `PING` inicial do Figma, ignora eventos que não
representam um handoff e publica somente eventos `DEV_MODE_STATUS_UPDATE` com
`status=READY_FOR_DEV`. A deduplicação evita mensagens repetidas em retries.

## Pré-requisitos

- Uma team Figma Professional, Organization ou Enterprise com permissão para criar
  webhooks no arquivo.
- Um arquivo Figma contendo as telas do produto. Um único webhook no arquivo atende todas
  as telas e nodes desse arquivo.
- Uma aplicação/bot do Discord com permissão para enviar mensagens no canal escolhido.
- Uma VPS com Docker Swarm, um domínio ou subdomínio apontando para a VPS e um certificado
  TLS válido.
- Python 3 para os scripts de administração do Figma.

No plano Professional, o Figma permite até 3 webhooks por arquivo, 5 por pasta, 20 por
team e 150 webhooks de arquivos no plano. Para este projeto, use um webhook por arquivo.
O número de telas ou eventos recebidos não consome novos cadastros de webhook.

## Clonar o projeto

```bash
git clone https://github.com/kaiqd/figma-discord-handoff.git
cd figma-discord-handoff
```

Valide os artefatos antes de configurar a VPS:

```bash
make validate
```

## Configurar o Discord

1. Crie uma aplicação no [Discord Developer Portal](https://discord.com/developers/applications).
2. Crie um bot para a aplicação e copie o token.
3. Convide o bot para o servidor com permissão para enviar mensagens e inserir links.
4. Copie o ID do canal que receberá as notificações.

O workflow usa a credencial Header Auth abaixo:

```text
Nome: Hands On — Discord Bot
Header: Authorization
Valor: Bot <DISCORD_BOT_TOKEN>
```

## Configurar o Figma

1. Abra o arquivo Figma que contém as telas do projeto.
2. Copie o file key da URL. Em uma URL como
   `https://www.figma.com/design/ABC123/Nome`, o file key é `ABC123`.
3. Crie um Personal Access Token com permissão para ler arquivos e administrar webhooks.
4. Gere um passcode exclusivo para validar os eventos recebidos pelo n8n.

O workflow usa a credencial Header Auth abaixo para consultar metadados do arquivo:

```text
Nome: Hands On — Figma API Token
Header: X-Figma-Token
Valor: <FIGMA_TOKEN>
```

## Configurar a VPS

Na VPS, copie o arquivo de ambiente e preencha os valores. Nunca versionar este arquivo.

```bash
cp .env.example .env
```

Variáveis principais:

```dotenv
HANDS_ON_DOMAIN=hands-on.seudominio.com
HANDS_ON_HTTP_PORT=8081
HANDS_ON_HTTPS_PORT=8443

DISCORD_APPLICATION_ID=<application-id>
DISCORD_CHANNEL_ID=<channel-id>
DISCORD_BOT_TOKEN=<bot-token>

FIGMA_TOKEN=<personal-access-token>
FIGMA_CONTEXT_TYPE=file
FIGMA_CONTEXT_ID=<file-key>
FIGMA_WEBHOOK_PASSCODE=<passcode>

N8N_ENCRYPTION_KEY=<chave-estavel-e-longa>
WEBHOOK_URL=https://hands-on.seudominio.com:8443/
FIGMA_WEBHOOK_ENDPOINT=https://hands-on.seudominio.com:8443/webhook/figma-ready-for-dev

POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=<senha-forte>
```

Gere uma chave estável para o n8n, por exemplo:

```bash
openssl rand -hex 32
```

Coloque o certificado do domínio nestes arquivos:

```text
certs/fullchain.pem
certs/privkey.pem
```

Suba a stack independente do projeto:

```bash
make deploy-swarm
docker stack services hands-on
```

Acesse o editor em:

```text
https://hands-on.seudominio.com:8443
```

## Importar e ativar o workflow

No n8n:

1. Importe `n8n/workflows/figma-ready-for-dev.json`.
2. No node **Fetch Figma file metadata**, selecione `Hands On — Figma API Token`.
3. No node **Send message to Discord**, selecione `Hands On — Discord Bot`.
4. Salve e ative o workflow.

## Testar antes do Figma

Na VPS:

```bash
make test-webhook
```

O resultado esperado é:

- passcode inválido: HTTP 400;
- eventos não publicáveis: HTTP 200 sem mensagem;
- primeiro `READY_FOR_DEV`: HTTP 200 com uma mensagem no Discord;
- retry do mesmo evento: HTTP 200 sem uma segunda mensagem.

## Registrar o webhook no Figma

Liste os webhooks existentes no arquivo:

```bash
make list-webhooks
```

Depois registre o webhook:

```bash
make register-webhook
```

O Figma enviará um `PING` inicial. O workflow deve aceitá-lo sem publicar no Discord.

Para listar todos os webhooks do plano, defina temporariamente o identificador do plano:

```bash
FIGMA_PLAN_API_ID=team-<team-id> make list-webhooks
```

Use `organization-<organization-id>` em contas Organization ou Enterprise.

## Operação

```bash
make logs
make list-webhooks
make remove-webhook ID=<webhook-id>
```

Faça backups periódicos do volume do n8n, do banco PostgreSQL e da
`N8N_ENCRYPTION_KEY`. Esses itens são necessários para recuperar credenciais e o estado
operacional da instalação.

## Segurança

- Nunca envie tokens, passcodes ou arquivos de credenciais para o Git.
- Mantenha `.env` fora do versionamento.
- Use um passcode exclusivo para cada endpoint.
- Restrinja no Discord as permissões do bot ao canal de destino.
- Se um segredo for exposto, revogue-o e gere outro imediatamente.

Para o procedimento detalhado da VPS, consulte [docs/VPS_RUNBOOK.md](docs/VPS_RUNBOOK.md).
