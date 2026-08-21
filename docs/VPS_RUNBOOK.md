# Runbook da VPS

Esta é a única etapa que deve iniciar o n8n. O workflow e os scripts podem ser revisados
localmente, mas os segredos, o domínio e a URL pública pertencem à VPS.

## Ordem de configuração

1. No Coolify (ou na VPS), configure as variáveis de ambiente baseadas em `.env.example`.
2. Gere uma chave longa e estável para `N8N_ENCRYPTION_KEY`; não a troque depois de criar
   credenciais no n8n.
3. Preencha os tokens do Discord e do Figma e o `DISCORD_CHANNEL_ID`.
4. Defina o domínio do n8n no Coolify (ex: `https://n8n.seudominio.com`). O Coolify cuidará
   automaticamente do roteamento e dos certificados SSL/TLS.
5. Realize o deploy pelo Coolify apontando para `infra/compose.yaml` (ou execute `make up`
   se estiver operando diretamente via Docker Compose).
6. Abra `https://<domínio>` e acesse o n8n.
7. Crie as credenciais Header Auth:
   - `Hands On — Discord Bot`: `Authorization` = `Bot <DISCORD_BOT_TOKEN>`.
   - `Hands On — Figma API Token`: `X-Figma-Token` = `<FIGMA_TOKEN>`.
8. Importe `n8n/workflows/figma-ready-for-dev.json`, selecione as duas credenciais e
   confirme que `FIGMA_WEBHOOK_PASSCODE` e `DISCORD_CHANNEL_ID` estão configurados nas variáveis
   de ambiente. Ative o workflow somente depois de testar o node do Discord.
9. Execute `./scripts/test_webhook.sh` (ou `make test-webhook`). O resultado esperado é HTTP 400 para passcode inválido,
   HTTP 200 para os demais casos e uma única mensagem no Discord.
10. Só depois registre o webhook real com `make register-webhook`.

## Operação

- `make logs` acompanha o n8n; o histórico de execuções deve ficar habilitado para
  diagnóstico e com retenção limitada.
- `make list-webhooks` confirma o webhook ativo sem revelar o passcode. Para investigar o
  limite do plano inteiro, preencha temporariamente `FIGMA_PLAN_API_ID` com `team-<id>` ou
  `organization-<id>` e execute o mesmo comando; remova somente webhooks confirmadamente
  antigos com `make remove-webhook ID=<id>`.
- `make remove-webhook ID=<id>` remove um cadastro incorreto; a remoção é irreversível.
- Faça backup do volume/banco do n8n e de `N8N_ENCRYPTION_KEY`.
- O Postgres não expõe portas externas e só é acessível internamente pelo n8n.

## Rollback

Pause o workflow no editor, remova o webhook pelo script e restaure o volume do n8n ou o
backup do Postgres. Não apague o volume como primeira ação: ele contém credenciais e o
estado operacional.
