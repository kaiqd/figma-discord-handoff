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
  webhooks.
- Um arquivo Figma contendo as telas do produto e acessível aos membros da team. O projeto
  usa um webhook de team, que pode receber eventos dos arquivos elegíveis dessa team.
- Uma aplicação/bot do Discord com permissão para enviar mensagens no canal escolhido.
- Uma VPS com Docker Compose ou Coolify configurado e um domínio apontando para a aplicação.
- Python 3 para os scripts de administração do Figma.

No plano Professional, o Figma permite até 3 webhooks por arquivo, 5 por pasta, 20 por
team e 150 webhooks de arquivos no plano. Para este projeto, usamos um único webhook de
team. O número de páginas, telas ou eventos recebidos não consome novos cadastros de
webhook.

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
3. Na área de arquivos do Figma, copie o ID da team na URL. Em uma URL como
   `https://www.figma.com/files/team/123456789/`, o ID da team é `123456789`.
4. Crie um Personal Access Token com permissão para ler arquivos e administrar webhooks.
5. Gere um passcode exclusivo para validar os eventos recebidos pelo n8n.

O passcode é uma senha do webhook. Ele não é o ID da conta, da team ou do arquivo.

O workflow usa a credencial Header Auth abaixo para consultar metadados do arquivo:

```text
Nome: Hands On — Figma API Token
Header: X-Figma-Token
Valor: <FIGMA_TOKEN>
```

## Configuração do Ambiente e Deploy no Coolify

### 1. Variáveis de Ambiente

No Coolify (ou na VPS no arquivo `.env` gerado a partir de `.env.example`), configure:

```dotenv
DISCORD_APPLICATION_ID=<application-id>
DISCORD_CHANNEL_ID=<channel-id>
DISCORD_BOT_TOKEN=<bot-token>

FIGMA_TOKEN=<personal-access-token>
FIGMA_CONTEXT_TYPE=team
FIGMA_CONTEXT_ID=<team-id>
FIGMA_WEBHOOK_PASSCODE=<passcode>

N8N_HOST=n8n.seudominio.com
N8N_PROTOCOL=https
N8N_PORT=5678
N8N_ENCRYPTION_KEY=<chave-estavel-e-longa>
WEBHOOK_URL=https://n8n.seudominio.com/
FIGMA_WEBHOOK_ENDPOINT=https://n8n.seudominio.com/webhook/figma-ready-for-dev
N8N_PROXY_HOPS=1

POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=<senha-forte>
```

Gere uma chave estável para o n8n, por exemplo:

```bash
openssl rand -hex 32
```

### 2. Deploy no Coolify

1. No Coolify, crie um novo recurso escolhendo **Docker Compose** apontando para o repositório.
2. Defina o caminho do arquivo compose para `infra/compose.yaml`.
3. Insira as variáveis de ambiente acima.
4. O Coolify gerencia automaticamente o proxy reverso e os certificados SSL/TLS via Let's Encrypt para o seu domínio.
5. Clique em **Deploy**.

Acesse o editor do n8n em:

```text
https://n8n.seudominio.com
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

Liste os webhooks existentes na team:

```bash
make list-webhooks
```

Depois registre o webhook:

```bash
make register-webhook
```

O Figma enviará um `PING` inicial. O workflow deve aceitá-lo sem publicar no Discord.

Como o webhook é de team, os arquivos precisam estar acessíveis aos membros da team. Um
arquivo restrito a convidados pode não enviar eventos para esse tipo de webhook.

Para usar um webhook limitado a um único arquivo, configure `FIGMA_CONTEXT_TYPE=file` e
`FIGMA_CONTEXT_ID=<file-key>` antes de executar os comandos acima.

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
