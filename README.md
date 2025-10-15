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
AN_DIST_URL_HOMOLOG=https://hom.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx
DFE_USE_WSDL=false

# Recepção de Evento v4.00 – Ambiente Nacional (fallback)
EV_URL_PRODUCAO=https://www.nfe.fazenda.gov.br/ws/recepcaoevento/recepcaoevento4.asmx
EV_URL_HOMOLOG=https://hom.nfe.fazenda.gov.br/ws/recepcaoevento/recepcaoevento4.asmx

# Certificados – PFX e bundle de CAs (ICP-Brasil)
PFX_PATH=/path/para/certificado.pfx
PFX_PASSWORD=senha
# Bundle de CAs personalizado (quando necessário):
DFE_CA_BUNDLE=/path/para/icp_brasil_chain.pem

# Debug detalhado (logs SOAP, endpoints tentados)
DFE_DEBUG=true
```

Observações:

- Se seu ambiente usa proxy corporativo com inspeção SSL, configure `DFE_CA_BUNDLE` apontando para o CA corporativo (PEM).
- Caso o endpoint estadual (ex.: SEFAZ-SP) falhe por TLS (`CERTIFICATE_VERIFY_FAILED`), usar `DFE_CA_BUNDLE` com a cadeia do servidor resolve.

## TLS (DFE_CA_BUNDLE) – Como obter a cadeia em WSL

Exemplo: extrair a cadeia de certificados do host da SEFAZ-SP e salvar em `/tmp/sefaz_sp_chain.pem`:

```bash
# WSL
echo | openssl s_client -servername nfe.fazenda.sp.gov.br \
  -connect nfe.fazenda.sp.gov.br:443 -showcerts 2>/dev/null \
  | awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/ { print }' \
  > /tmp/sefaz_sp_chain.pem
```

Aponte no `.env`:

```
DFE_CA_BUNDLE=/tmp/sefaz_sp_chain.pem
```

Reinicie o servidor e teste novamente a manifestação.

## UI – Página `/ui`

- Lista de documentos com paginação (50 por página) e busca local (por nome/chave/CNPJ/número/data)
- Manifestação em lote: seleciona itens e clica em “manifestar e importar XMLs”
- Seção “Visualizar XML por chave”: permite consultar/exibir/baixar XML por chave diretamente

Dicas:

- Se a lista mostrar “cStat=?” e nada mais, ative `DFE_DEBUG=true` e observe a mensagem detalhada (erro/status_code/url/op/soap).
- Para Distribuição DF-e, respeite o cStat=656 (Consumo Indevido): aguarde ~1h e use o `ultNSU` informado nas próximas chamadas.

## Boas práticas de orquestração

- distDFe (pull):
  - Quando `ultNSU == maxNSU`, agende o próximo ciclo em ~1h (ambiente ocioso)
  - Quando `cStat == 656`, interrompa o ciclo e reagende para ~1h usando o `ultNSU` retornado
- Manifestação:
  - Preferir SOAP 1.1 para alguns UFs (ex.: SP), e usar `cOrgao` conforme o endpoint: 91 (AN) ou `UF` da chave
  - Se um endpoint estadual falhar (TLS, 404), cair para o AN automaticamente

## Sugestão de retorno HTTP no endpoint de manifestação

Para simplificar o frontend, recomendamos que o endpoint `POST /api/dfe/manifestar` retorne:

- HTTP 200 apenas quando houver sucesso (com `cStat`/`xMotivo`)
- HTTP 4xx/5xx quando houver erro na chamada ao serviço (ex.: TLS, 404, parse), incluindo no corpo JSON os campos `url`, `op`, `soap`, `status_code`, `detail`

Assim o UI pode exibir mensagens consistentes sem inferir “sucesso” pelo status 200 em respostas de erro.

## Troubleshooting rápido

- “CERTIFICATE_VERIFY_FAILED” em SEFAZ estadual:
  - Configure `DFE_CA_BUNDLE` com a cadeia do servidor (ou CA corporativo)
  - Teste o fallback para o Ambiente Nacional (já implementado)
- “SOAP 404 The resource cannot be found”:
  - Verifique a versão SOAP e a operação (1.1 com `SOAPAction` ajuda em alguns UFs)
  - Use os endpoints sugeridos acima (minúsculos no AN são comuns)
- “cStat=656 Rejeição: Consumo Indevido”:
  - Pausar por ~1h e retomar com o `ultNSU` informado; o cliente já sinaliza `wait_sec=3600`

---

Se precisar, posso adicionar um script utilitário (ex.: `scripts/fetch_chain.sh`) para baixar cadeias de certificados específicas e atualizar o `.env` automaticamente.

## dfe-sync

Ferramenta/serviço FastAPI para sincronização de Distribuição DF-e (NFeDistribuicaoDFe) por NSU.

### Ambiente

Requisitos principais:

1. Python 3.11+ (em WSL) e virtualenv ativado.
2. PostgreSQL acessível (porta configurada em `.env`).
3. Certificado A1 em formato PFX + senha.

### Variáveis de ambiente chave

`NFE_AMBIENTE` = HOMOLOG ou PRODUCAO  
`DFE_DEBUG` = true/false habilita logs detalhados do cliente DF-e (tempo, cStat, xMotivo, SOAP bruto em caso de erro).  
`DFE_CA_BUNDLE` = caminho para bundle PEM da cadeia ICP-Brasil (opcional; se não definido usa truststore padrão `certifi`).

WSDL do Ambiente Nacional (endereços remotos + fallback local):

`AN_WSDL_HOMOLOG` = URL completa do WSDL de homologação (atenção ao sufixo "/ws/")
`AN_WSDL_PRODUCAO` = URL completa do WSDL de produção (atenção ao sufixo "/ws/")
`AN_WSDL_LOCAL_PATH` = caminho para arquivo WSDL local (opcional, usado como fallback se o remoto falhar)

Compatibilidade temporária: se `NFE_AMBIENTE` não estiver definido mas existir `DFE_AMBIENTE`, o código pode (se implementado) assumir o valor antigo e emitir um log de aviso. Recomenda-se migrar para `NFE_AMBIENTE`.

Exemplo export:

```bash
export NFE_AMBIENTE=PRODUCAO
export DFE_DEBUG=true
export DFE_CA_BUNDLE=storage/ca/icp-brasil-bundle.pem
export AN_WSDL_PRODUCAO="https://www.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?WSDL"
export AN_WSDL_HOMOLOG="https://hom.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?WSDL"
# Fallback local (opcional)
export AN_WSDL_LOCAL_PATH="$(pwd)/wsdl/NFeDistribuicaoDFe.wsdl"
```

### Geração de CA Bundle ICP-Brasil

Use o script `generate-ca-bundle.sh` para extrair a cadeia de certificados do seu PFX e montar um bundle PEM:

```bash
bash generate-ca-bundle.sh storage/certs/1.pfx 123456 storage/ca/icp-brasil-bundle.pem
export DFE_CA_BUNDLE=storage/ca/icp-brasil-bundle.pem
```

Observações:

- O OpenSSL 3.x exige flag `-legacy` para PFXs que usam RC2.
- Se o bundle tiver apenas 1 certificado, confirme se faltam intermediárias (pode ser necessário baixar cadeia da AC emissora e concatenar manualmente).

### Validação do Certificado A1

Script: `validate-cert.sh`

```bash
bash validate-cert.sh storage/certs/1.pfx SENHA
```

Saída esperada: subject, issuer, validade, fingerprint e HTTP code (404/200 são aceitáveis para teste TLS).

### Diagnóstico rápido de Distribuição

Endpoint único: `/api/dfe/diagnose?empresa_id=1`
Retorna estrutura contendo `cStat`, `xMotivo`, `ultNSU`, `maxNSU`. Use para validar conectividade antes de loops longos.

Exemplo curl:

```bash
curl -s http://localhost:8000/api/dfe/diagnose?empresa_id=1 | jq
```

### Sincronização por NSU

Iniciar pull:

```bash
curl -X POST http://localhost:8000/api/dfe/sync?empresa_id=1
```

Monitorar cursor:

```bash
curl -s http://localhost:8000/api/dfe/cursor?empresa_id=1 | jq
```

Listar documentos persistidos:

```bash
curl -s http://localhost:8000/api/dfe/documentos?empresa_id=1 | jq
```

### Possíveis códigos de status (cStat) relevantes

- 138: Documento localizado (há retorno)
- 137: Nenhum documento localizado
- 656: Consumo indevido (aplique backoff, aguarde antes de nova tentativa)
- 109/110: Erros de serviço (reinicie mais tarde)

### Checklist de Problemas Comuns

1. Certificado expirado ou senha incorreta -> revise `validate-cert.sh`.
2. Cadeia incompleta -> gere bundle e defina `DFE_CA_BUNDLE`.
3. cStat 656 frequente -> reduzir ritmo (intervalo > 1 min) e manter estado NSU.
4. Sempre cStat 137 e maxNSU = ultNSU = 0 -> verifique se CNPJ é destinatário de notas e possui autorização para distribuição.
5. Timeouts sem resposta -> checar rede (curl com bundle) e ativar `DFE_DEBUG` para logs.
6. Erro 404/indisponibilidade do WSDL remoto -> colocar o arquivo em `wsdl/NFeDistribuicaoDFe.wsdl` e definir `AN_WSDL_LOCAL_PATH`.

### Logs e Debug

Com `DFE_DEBUG=true`, o cliente registra tempo da chamada, tamanho da resposta, códigos e erros. Redirecione logs para arquivo se necessário:

```bash
DFE_DEBUG=true uvicorn src.main:app --reload 2>&1 | tee logs/dfe-debug.log
```

### Segurança

- Nunca commitar PFX ou bundle contendo certificados privados em repositórios públicos.
- Considere criptografar a senha do PFX em repouso (futuro: armazenamento seguro em variáveis secretas).

### Próximos Passos

- Ajustar `.env` com WSDLs corretos (com "/ws/").
- Confirmar diagnose vs script SOAP manual.
- Agendar sync por hora quando `ultNSU == maxNSU`.
-

### Teste SOAP Manual (curl)

Script utilitário: `soap-dfe.sh` permite realizar chamada direta ao serviço sem depender da biblioteca SOAP.

Uso:

```bash
bash soap-dfe.sh <CNPJ> <ULT_NSU> <AMBIENTE> <PFX> <SENHA>
# Exemplo:
bash soap-dfe.sh 51309435000153 000000000000000 PRODUCAO storage/certs/1.pfx 513094
```

Saída inclui HTTP e dicionário com `cStat`, `xMotivo`, `ultNSU`, `maxNSU` e quantidade de `docZip`.

Interpretação rápida:

- HTTP!=200: problema de transporte/TLS ou bloqueio.
- cStat 137: nenhum documento para o NSU informado (normal se início de histórico).
- cStat 138: documentos retornados em `docZip`.
- cStat 656: consumo indevido (reduzir frequência / aplicar backoff).
- cStat nulo: possível falha de parsing (ver conteúdo em `resp.xml`).

Se o script manual funcionar e a aplicação não, revisar diferença de envelopes (Zeep) ou timeout.

Validação cruzada (Diagnose vs SOAP):

1. Configure `.env` com os WSDLs e NFE_AMBIENTE corretos (ver `.env.example`). Em caso de erro 404 no WSDL remoto, baixe o arquivo e aponte `AN_WSDL_LOCAL_PATH` para `wsdl/NFeDistribuicaoDFe.wsdl`.
2. Rode o diagnose:

- GET /api/dfe/diagnose?empresa_id=1&ult_nsu=000000000000000

3. Rode o script SOAP manual com os mesmos parâmetros (CNPJ, ultNSU, ambiente):

- bash soap-dfe.sh <CNPJ> 000000000000000 PRODUCAO <PFX> <SENHA>

4. Compare: `cStat`, `ultNSU` e `maxNSU` devem coincidir; a quantidade de `docZip` deve ser similar.
5. Se divergir:

- verifique WSDL remoto vs fallback local, `DFE_CA_BUNDLE` e diferenças em `tpAmb`/`cUFAutor`.

- Implementar armazenamento cifrado da senha do PFX.
- Adicionar testes automatizados para parsing e persistência de documentos.
- Suporte a refresh agendado com APScheduler configurável por empresa.

### Consulta Pública NF-e SP

Endpoint experimental para resumo de NF-e via portal público da SEFAZ/SP.

Rota:

`GET /api/nfe/sp/publica/{chave}`

Resposta (exemplo):

```json
{
  "status": "ok",
  "chave": "35140112345678000123550010001234567890123456",
  "emitente": {
    "cnpj": "12345678000123",
    "ie": "123.456.789.112",
    "municipio": "SAO PAULO",
    "uf": "SP"
  },
  "destinatario": {
    "cnpj": "22345678000198",
    "ie": "ISENTO",
    "municipio": "CAMPINAS",
    "uf": "SP"
  },
  "produtos": [
    {
      "numero_item": 1,
      "codigo": "001",
      "descricao": "PRODUTO A",
      "ncm": "12345678",
      "cfop": "5102",
      "quantidade": 10.0,
      "unidade": "UN",
      "valor_unitario": 5.0,
      "valor_total": 50.0
    }
  ],
  "eventos": [{ "descricao": "Autorizado o uso da NF-e" }],
  "raw_html_hash": "sha256:...",
  "fetched_at": "2025-10-14T12:34:56Z"
}
```

Status possíveis:

- `ok`: parse básico concluído.
- `captcha_required`: portal pediu captcha (sem automação inclusa).
- `not_found`: chave não reconhecida ou página sem dados.
- `error`: falha de rede ou exceção (campo `detail`).

Limitações e avisos:

- Layout do portal pode mudar a qualquer momento (parser heurístico).
- Possível desafio de captcha se volume/ frequência alta.
- Uso deve respeitar termos de serviço e limites legais (apenas chaves às quais você já tem direito de acesso / finalidade legítima).
- Produtos e eventos: parser inicial pode retornar lista vazia ou campos nulos se estrutura divergente.

### Planejamento UI Web (Futuro)

Objetivo: Interface simples para consultar chave, visualizar resumo, produtos e eventos.

Stack proposta: React + Vite + TypeScript.

Estrutura inicial (pasta `web/`):

```
web/
	src/
		components/
			NFeSearchForm.tsx
			ProductsTable.tsx
			EventsTimeline.tsx
		pages/
			Home.tsx
		api/
			client.ts (fetch wrapper)
		App.tsx
		main.tsx
	index.html
	package.json
```

Fluxo:

1. Usuário digita chave (validação 44 dígitos).
2. Chamada `GET /api/nfe/sp/publica/{chave}`.
3. Exibe status; se `ok`, renderiza bloco Emitente/Destinatário, tabela Produtos, seção Eventos.
4. Estados de erro/captcha apresentados com mensagens claras e possivelmente dica de aguardar/reduzir frequência.

Melhorias futuras:

- Cache local (IndexedDB) de últimas consultas.
- Dark mode.
- Download de JSON.
- Comparação lado-a-lado de chaves.
