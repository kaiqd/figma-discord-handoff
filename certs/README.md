# Certificado TLS

Antes do deploy da stack, coloque nesta pasta um certificado válido para
`HANDS_ON_DOMAIN`:

- `fullchain.pem`
- `privkey.pem`

Os arquivos são ignorados pelo Git e viram secrets do Docker Swarm. Nunca faça commit
deles.

O Projeto por padrão usa HTTP `8081` e HTTPS
`8443`. O DNS deve apontar `HANDS_ON_DOMAIN` para a VPS e o firewall deve liberar TCP
8081 e 8443. O endpoint final do Figma será:

```text
https://HANDS_ON_DOMAIN:8443/webhook/figma-ready-for-dev
```
