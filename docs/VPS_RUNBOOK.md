# Runbook da VPS

Esta é a única etapa que deve iniciar o n8n. O workflow e os scripts podem ser revisados
localmente, mas os segredos, o domínio e a URL pública pertencem à VPS.

## Ordem de configuração

1. Instale Docker Engine, Docker Compose e Caddy (ou outro proxy HTTPS) na VPS.
2. Clone o repositório e crie `.env` a partir de `.env.example`.
3. Gere uma chave longa e estável para `N8N_ENCRYPTION_KEY`; não a troque depois de criar
   credenciais no n8n.
4. Preencha os tokens do Discord e do Figma e o `DISCORD_CHANNEL_ID`.
5. Defina `N8N_HOST`, `N8N_PROTOCOL=https`, `WEBHOOK_URL=https://<domínio>/` e
   `N8N_PROXY_HOPS=1`.
6. Configure o proxy para encaminhar o domínio para `127.0.0.1:5678` e confirme TLS.
7. Suba os serviços com `make up` e abra o editor apenas pelo domínio protegido.
8. Crie as credenciais Header Auth:
   - `Hands On — Discord Bot`: `Authorization` = `Bot <DISCORD_BOT_TOKEN>`.
   - `Hands On — Figma API Token`: `X-Figma-Token` = `<FIGMA_TOKEN>`.
9. Importe `n8n/workflows/figma-ready-for-dev.json`, selecione as duas credenciais e
   confirme que `FIGMA_WEBHOOK_PASSCODE` e `DISCORD_CHANNEL_ID` estão disponíveis para o
   workflow. Ative-o somente depois de testar o node do Discord.
10. Execute `make test-webhook`. O resultado esperado é HTTP 400 para passcode inválido,
    HTTP 200 para os demais seis casos e uma única mensagem no Discord.
11. Só depois registre o webhook real com `make register-webhook`.

## Operação

- `make logs` acompanha o n8n; o histórico de execuções deve ficar habilitado para
  diagnóstico e com retenção limitada.
- `make list-webhooks` confirma o webhook ativo sem revelar o passcode.
- `make remove-webhook ID=<id>` remove um cadastro incorreto; a remoção é irreversível.
- Faça backup do volume/banco do n8n e de `N8N_ENCRYPTION_KEY`.
- O Postgres não tem `ports` no Compose e só é acessível pelo n8n.

## Rollback

Pause o workflow no editor, remova o webhook pelo script e restaure o volume do n8n ou o
backup do Postgres. Não apague o volume como primeira ação: ele contém credenciais e o
estado operacional.
