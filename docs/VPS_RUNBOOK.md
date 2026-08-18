# Runbook da VPS

Esta é a única etapa que deve iniciar o n8n. O workflow e os scripts podem ser revisados
localmente, mas os segredos, o domínio e a URL pública pertencem à VPS.

## Ordem de configuração

1. Clone o repositório e crie `.env` a partir de `.env.example`.
3. Gere uma chave longa e estável para `N8N_ENCRYPTION_KEY`; não a troque depois de criar
   credenciais no n8n.
4. Preencha os tokens do Discord e do Figma e o `DISCORD_CHANNEL_ID`.
5. Defina `HANDS_ON_DOMAIN`, por exemplo `hands-on.seudominio.com`, e crie o registro DNS
   apontando para a VPS. Libere TCP `8081` e `8443` no firewall.
6. Coloque `certs/fullchain.pem` e `certs/privkey.pem` no servidor. O certificado deve
   ser válido para `HANDS_ON_DOMAIN`; a pasta é ignorada pelo Git.
7. Suba a stack independente com `make deploy-swarm`; não use `make up` nesta VPS.
8. Confirme `docker stack services hands-on` e abra `https://<domínio>:8443`.
9. Crie as credenciais Header Auth:
   - `Hands On — Discord Bot`: `Authorization` = `Bot <DISCORD_BOT_TOKEN>`.
   - `Hands On — Figma API Token`: `X-Figma-Token` = `<FIGMA_TOKEN>`.
10. Importe `n8n/workflows/figma-ready-for-dev.json`, selecione as duas credenciais e
   confirme que `FIGMA_WEBHOOK_PASSCODE` e `DISCORD_CHANNEL_ID` estão disponíveis para o
   workflow. Ative-o somente depois de testar o node do Discord.
11. Execute `make test-webhook`. O resultado esperado é HTTP 400 para passcode inválido,
    HTTP 200 para os demais seis casos e uma única mensagem no Discord.
12. Só depois registre o webhook real com `make register-webhook`.

## Operação

- `make logs` acompanha o n8n; o histórico de execuções deve ficar habilitado para
  diagnóstico e com retenção limitada.
- `make list-webhooks` confirma o webhook ativo sem revelar o passcode.
- `make remove-webhook ID=<id>` remove um cadastro incorreto; a remoção é irreversível.
- Faça backup do volume/banco do n8n e de `N8N_ENCRYPTION_KEY`.
- O Postgres não tem `ports` no Compose/Swarm e só é acessível pelo n8n.
- A stack não usa `rosarede`, Traefik ou volumes de outros projetos.

## Rollback

Pause o workflow no editor, remova o webhook pelo script e restaure o volume do n8n ou o
backup do Postgres. Não apague o volume como primeira ação: ele contém credenciais e o
estado operacional.
