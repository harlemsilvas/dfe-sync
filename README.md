# DF-e Sync / Manifestação – Guia Rápido

Este projeto implementa:

- Distribuição DF-e (AN – NFeDistribuicaoDFe) para consulta por NSU e por chave
- Visualização/Download de XML por chave no UI estático (`/ui`)
- Manifestação do destinatário (Recepção de Evento v4.00)

## Variáveis de ambiente (.env)

Defina as variáveis conforme seu ambiente. Exemplos:

```
# Ambiente: PRODUCAO ou HOMOLOGACAO
NFE_AMBIENTE=PRODUCAO

# Distribuição DF-e (AN) – endpoints (opcional; caso não defina, usamos candidatos conhecidos)
AN_DIST_URL_PRODUCAO=https://www.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx
# dfe-sync

Serviço FastAPI para sincronização de DF-e (Distribuição de Documentos Fiscais Eletrônicos) e Manifestação do Destinatário, com UI estática para consulta e download por chave.

• Backend: FastAPI, SQLAlchemy, Alembic, APScheduler, requests + lxml.
• SOAP: envelopes 1.1/1.2 compatíveis (NFeDistribuicaoDFe e Recepção de Evento v4.00).
• Certificados: PFX→PEM, suporte a DFE_CA_BUNDLE (ICP-Brasil/corporativo).
• UI: `web/index.html` com listagem, paginação, busca local, manifestação em lote e “Visualizar XML por chave”.

## Quick Start

1) Requisitos
- Python 3.11+ (WSL recomendado)
- PostgreSQL acessível (configure `DB_URL` no `.env`)
- Certificado A1 (PFX) válido e senha

2) Configuração
- Copie `.env` de exemplo e ajuste valores. Campos principais:

```

NFE_AMBIENTE=PRODUCAO # ou HOMOLOG
DFE_DEBUG=true # logs detalhados
DFE_CA_BUNDLE=/mnt/c/openai-xml/dfe-sync/certs/combined_ca.pem
AN_DIST_URL_PRODUCAO=https://www.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx
AN_DIST_URL_HOMOLOG=https://hom.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx

````

- Gere/aponte um bundle PEM confiável (veja seção TLS abaixo).

3) Executar
- Ative seu venv e instale dependências (requirements.txt).
- Rode migrações Alembic e inicie a API na porta 8001.

4) Usar
- UI: acesse `http://localhost:8001/ui`
- Diagnose: `GET /api/dfe/diagnose?empresa_id=1`
- Download por chave: `GET /api/dfe/conschave/download?empresa_id=1&chNFe=<44dígitos>&prefer=procNFe&save=true`

## Variáveis de ambiente (.env)

Principais chaves suportadas (ver `src/settings.py`):

- `NFE_AMBIENTE`: PRODUCAO | HOMOLOG
- `AN_DIST_URL_PRODUCAO`/`AN_DIST_URL_HOMOLOG`: endpoints diretos (sem ?WSDL)
- `DFE_USE_WSDL`: false por padrão (WSDL remoto pode retornar 404)
- `EV_URL_PRODUCAO`/`EV_URL_HOMOLOG`: Recepção de Evento v4.00 (fallback AN em minúsculas)
- `DFE_CA_BUNDLE`: caminho para bundle PEM confiável
- `DFE_DEBUG`: logs detalhados do cliente DF-e

## TLS (DFE_CA_BUNDLE)

Se o erro `CERTIFICATE_VERIFY_FAILED` ocorrer, gere um bundle com a cadeia ICP-Brasil (ou CA corporativo) e aponte `DFE_CA_BUNDLE`.

Exemplo WSL para AN + SP (gera `certs/combined_ca.pem`):

```bash
mkdir -p certs
> certs/dfe_ca_bundle.pem
for h in www.nfe.fazenda.gov.br www1.nfe.fazenda.gov.br nfe.fazenda.sp.gov.br; do
  echo "# $h" >> certs/dfe_ca_bundle.pem
  echo | openssl s_client -showcerts -servername $h -connect $h:443 2>/dev/null \
    | awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/ {print}' >> certs/dfe_ca_bundle.pem
  echo >> certs/dfe_ca_bundle.pem
done
cat certs/dfe_ca_bundle.pem /etc/ssl/certs/ca-certificates.crt > certs/combined_ca.pem
````

Atualize `.env` e reinicie a API.

## Rotas principais

- `GET /api/dfe/diagnose?empresa_id=1` – uma chamada única para validar acesso (cStat/ultNSU/maxNSU)
- `POST /api/dfe/sync?empresa_id=1` – orquestração de distribuição até ociosidade ou 656
- `GET /api/dfe/conschave?empresa_id=1&chNFe=...` – consChNFe (metadados)
- `GET /api/dfe/conschave/download?...&prefer=procNFe&save=true` – retorna XML e salva em storage
- `POST /api/dfe/manifestar?...` – Recepção de Evento v4.00

## Regras de orquestração e errors

- `cStat=656`: pare e reagende (~1h) usando ultNSU retornado.
- `ultNSU==maxNSU`: ambiente ocioso; reagende em ~1h.
- Manifestação: tente SOAP 1.1/1.2; ajuste `cOrgao` (91 AN, ou UF da chave para SEFAZ).

Sugestão de API: retornar 2xx apenas com `cStat`/`xMotivo`; caso contrário, 4xx/5xx com `{ url, op, soap, status_code, detail }`.

## Troubleshooting

- TLS: use `DFE_CA_BUNDLE` e combine com truststore do sistema.
- 404 (SOAP): tente operação 1.1 (com SOAPAction), verifique path minúsculo no AN.
- Sem documentos: valide CNPJ-base do PFX (H04) e permissão de distribuição.

## Licença

Sugerida: MIT. Se desejar, adiciono `LICENSE` com o texto padrão.

1. Python 3.11+ (em WSL) e virtualenv ativado.
