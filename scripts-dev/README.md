# Scripts de Desenvolvimento e Testes

Scripts auxiliares para desenvolvimento, testes e diagnóstico do sistema.

⚠️ **Estes scripts NÃO devem ser usados em produção.**

---

## 🧪 Scripts de Teste

### test-api.sh
Testes básicos da API.

**Uso:**
```bash
./scripts-dev/test-api.sh
```

Testa:
- Criação de empresa
- Health check
- Endpoints básicos

---

### test-dfe-api.sh
Testes específicos dos endpoints DFe.

**Uso:**
```bash
./scripts-dev/test-dfe-api.sh
```

Testa endpoints de sincronização e consulta de documentos fiscais.

---

### test-complete-workflow.sh
Teste completo do fluxo de sincronização.

**Uso:**
```bash
./scripts-dev/test-complete-workflow.sh
```

Executa:
1. Verifica API
2. Consulta cursor inicial
3. Inicia sincronização em background
4. Monitora progresso durante 60s
5. Exibe resultado final

---

### test-prod-quick.sh
Teste rápido em ambiente de produção (com timeout).

**Uso:**
```bash
./scripts-dev/test-prod-quick.sh
```

Executa sincronização com timeout de 60s para validação rápida.

---

## 🔍 Scripts de Diagnóstico

### diagnose.sh
Diagnóstico rápido do sistema.

**Uso:**
```bash
./scripts-dev/diagnose.sh
```

Verifica:
- Ambiente configurado (.env)
- Empresa no banco
- Certificado cadastrado
- Teste de sincronização rápido (5s)

---

### monitor-sync.sh
Monitoramento em tempo real da sincronização.

**Uso:**
```bash
./scripts-dev/monitor-sync.sh
```

Exibe a cada 5 segundos:
- Cursor atual (ultimo_nsu/max_nsu)
- Documentos baixados (últimos 5)
- Arquivos XML salvos

**Parar:** Ctrl+C

---

## 🔐 Scripts de Certificado

### validate-cert.sh
Valida certificado digital A1.

**Uso:**
```bash
./scripts-dev/validate-cert.sh [PFX_PATH] [SENHA]
```

**Exemplos:**
```bash
# Usando valores padrão
./scripts-dev/validate-cert.sh

# Especificando certificado
./scripts-dev/validate-cert.sh storage/certs/1.pfx minha_senha
```

Verifica:
- Extração do certificado
- Informações (subject, issuer, validade)
- Conexão HTTPS com NF-e
- Serial, fingerprint

---

### generate-ca-bundle.sh
Gera bundle de certificados CA a partir do PFX.

**Uso:**
```bash
./scripts-dev/generate-ca-bundle.sh [PFX_PATH] [SENHA] [OUTPUT_PATH]
```

**Exemplos:**
```bash
# Usando valores padrão
./scripts-dev/generate-ca-bundle.sh

# Especificando caminhos
./scripts-dev/generate-ca-bundle.sh storage/certs/1.pfx senha123 storage/ca/bundle.pem
```

Gera arquivo PEM com a cadeia completa de certificados ICP-Brasil.

---

## 🛠️ Scripts de Setup

### setup-dfe-environment.sh
Setup completo do ambiente (desenvolvimento).

**Uso:**
```bash
./scripts-dev/setup-dfe-environment.sh
```

Executa:
1. Instala/configura PostgreSQL
2. Cria usuário e banco de dados
3. Cria virtualenv
4. Instala dependências
5. Aplica migrations
6. Exibe instruções finais

⚠️ **Atenção:** Instala PostgreSQL localmente. Em produção, use Docker ou servidor dedicado.

---

## 🧰 Scripts Utilitários

### soap-dfe.sh
Cliente SOAP direto para teste de comunicação com SEFAZ.

**Uso:**
```bash
./scripts-dev/soap-dfe.sh [CNPJ] [ULT_NSU] [AMBIENTE] [PFX] [SENHA]
```

**Exemplos:**
```bash
# Usando valores padrão
./scripts-dev/soap-dfe.sh

# Especificando parâmetros
./scripts-dev/soap-dfe.sh 51309435000153 000000000000000 PRODUCAO storage/certs/1.pfx senha123
```

**Parâmetros:**
- CNPJ: CNPJ sem formatação
- ULT_NSU: Último NSU conhecido (15 dígitos)
- AMBIENTE: PRODUCAO ou HOMOLOG
- PFX: Caminho do certificado
- SENHA: Senha do certificado

Útil para:
- Testar comunicação direta com SEFAZ
- Debug de problemas de certificado
- Validar resposta XML do serviço

---

## 📋 Fluxo de Desenvolvimento

### 1. Setup Inicial
```bash
# Executar setup automático
./scripts-dev/setup-dfe-environment.sh

# Ou manual:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
alembic upgrade head
```

### 2. Iniciar Desenvolvimento
```bash
# Terminal 1: Iniciar API
cd dfe-sync
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8001

# Terminal 2: Monitorar
./scripts-dev/monitor-sync.sh
```

### 3. Testes
```bash
# Testes básicos
./scripts-dev/test-api.sh

# Teste completo
./scripts-dev/test-complete-workflow.sh

# Diagnóstico
./scripts-dev/diagnose.sh
```

### 4. Debug de Certificado
```bash
# Validar certificado
./scripts-dev/validate-cert.sh storage/certs/1.pfx senha

# Gerar bundle CA
./scripts-dev/generate-ca-bundle.sh

# Testar SOAP direto
./scripts-dev/soap-dfe.sh
```

---

## 🔧 Dependências Adicionais

Alguns scripts requerem ferramentas extras:

```bash
# Ubuntu/Debian
sudo apt install -y curl jq lsof openssl

# Para monitoramento
sudo apt install -y postgresql-client
```

---

## ⚙️ Configuração para Testes

### .env para desenvolvimento
```bash
APP_ENV=dev
APP_DEBUG=true
DB_URL=postgresql+psycopg://dfe:dfe@localhost:5432/dfe
NFE_AMBIENTE=HOMOLOG  # Usar homologação para testes
```

### Banco de dados de teste
```bash
# Criar banco separado para testes
docker exec dfe_db psql -U dfe -c "CREATE DATABASE dfe_test;"

# Usar no .env.test
DB_URL=postgresql+psycopg://dfe:dfe@localhost:5432/dfe_test
```

---

## 🐛 Troubleshooting

### Script não executa
```bash
# Dar permissão de execução
chmod +x scripts-dev/*.sh

# Verificar shebang
head -1 scripts-dev/test-api.sh
```

### Certificado inválido
```bash
# Validar certificado
./scripts-dev/validate-cert.sh storage/certs/1.pfx senha

# Verificar informações
openssl pkcs12 -in storage/certs/1.pfx -info -noout
```

### Erro de conexão SEFAZ
```bash
# Testar comunicação direta
./scripts-dev/soap-dfe.sh

# Verificar ambiente no .env
grep NFE_AMBIENTE .env

# Testar com curl
curl -v https://www.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx
```

---

## 📚 Recursos Úteis

- [Documentação NF-e](http://www.nfe.fazenda.gov.br/)
- [Manual do Contribuinte](http://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=tW+YMyk/50s=)
- [Ambientes de Homologação](http://hom.nfe.fazenda.gov.br/)

---

## ⚠️ Lembretes Importantes

1. **Nunca use estes scripts em produção**
2. Use ambiente HOMOLOG para testes
3. Não commite certificados ou senhas
4. Monitore uso de requisições (evitar bloqueio SEFAZ)
5. Respeite rate limits da SEFAZ

---

## 📝 Adicionar Novos Scripts

Ao criar novos scripts de desenvolvimento:

1. Adicione à pasta `scripts-dev/`
2. Torne executável: `chmod +x scripts-dev/novo-script.sh`
3. Documente neste README
4. Use comentários no código
5. Adicione tratamento de erros: `set -euo pipefail`
