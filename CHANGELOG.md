# Changelog

Todas as mudanças notáveis deste projeto serão documentadas aqui.

## [v0.1.0] - 2025-10-15

### Added
- Manifestação (Recepção de Evento v4.00):
  - Endpoint `/api/dfe/manifestar` agora retorna HTTP 2xx somente em sucesso (quando há `cStat`), inclui `saved_path` do XML de resposta salvo em `storage/<CNPJ>/`.
  - Em erro, retorna 400 (assinatura), 424 (4xx do serviço remoto) ou 502 (falha HTTP/parse), com metadados (`url`, `op`, `soap`, `status_code`) e trecho do `body` remoto.
- Cliente de eventos: ampliadas variações de endpoints para AN e SP (com e sem `/ws/`, capitalização alternativa). Prioriza SOAP 1.1 para SP; usa `cOrgao=91` no AN e UF na SEFAZ.

### Fixed
- Web (Vite): adicionada tipagem de `import.meta.env` via `web/src/env.d.ts`.

### Docs
- README: seção de TLS com `DFE_CA_BUNDLE` e passo a passo para gerar bundle ICP-Brasil no WSL.

[v0.1.0]: https://github.com/harlemsilvas/dfe-sync/releases/tag/v0.1.0
