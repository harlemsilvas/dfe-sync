# Organização de Scripts - DFe Sync

## 📁 Estrutura Atual

```
dfe-sync/
├── scripts-prod/          # Scripts para PRODUÇÃO ✅
│   ├── start-api.sh
│   ├── stop-api.sh
│   ├── restart-api.sh
│   └── README.md
│
├── scripts-dev/           # Scripts para DESENVOLVIMENTO/TESTES ⚠️
│   ├── diagnose.sh
│   ├── generate-ca-bundle.sh
│   ├── monitor-sync.sh
│   ├── setup-dfe-environment.sh
│   ├── soap-dfe.sh
│   ├── test-api.sh
│   ├── test-complete-workflow.sh
│   ├── test-dfe-api.sh
│   ├── test-prod-quick.sh
│   ├── validate-cert.sh
│   └── README.md
│
├── start-api.sh      → scripts-prod/start-api.sh (link simbólico)
├── stop-api.sh       → scripts-prod/stop-api.sh (link simbólico)
└── restart-api.sh    → scripts-prod/restart-api.sh (link simbólico)
```

---

## ✅ Scripts de Produção (scripts-prod/)

Mantidos e organizados para uso em produção:

1. **start-api.sh** - Inicia a API
2. **stop-api.sh** - Para a API (com opções -p porta, -f força)
3. **restart-api.sh** - Reinicia a API (com opções -b background, -l log)

**Mudanças aplicadas:**
- ✅ Caminhos corrigidos para trabalhar de dentro de `scripts-prod/`
- ✅ BASE_DIR aponta para pasta raiz do projeto (um nível acima)
- ✅ Links simbólicos criados na raiz para facilitar uso

---

## ⚠️ Scripts de Desenvolvimento (scripts-dev/)

Scripts movidos para `scripts-dev/` (NÃO usar em produção):

### Testes
- **test-api.sh** - Testes básicos da API
- **test-dfe-api.sh** - Testes específicos DFe
- **test-complete-workflow.sh** - Teste completo de workflow
- **test-prod-quick.sh** - Teste rápido com timeout

### Diagnóstico
- **diagnose.sh** - Diagnóstico rápido do sistema
- **monitor-sync.sh** - Monitoramento em tempo real

### Certificados
- **validate-cert.sh** - Valida certificado A1
- **generate-ca-bundle.sh** - Gera bundle de CAs

### Setup/Utilitários
- **setup-dfe-environment.sh** - Setup completo do ambiente
- **soap-dfe.sh** - Cliente SOAP direto para testes

---

## ❌ Scripts Removidos (duplicados/obsoletos)

Foram removidos os seguintes scripts duplicados:

1. **start-dfe-api.sh** - Duplicado (caminho hardcoded incorreto)
2. **start-dfe-api-new.sh** - Duplicado
3. **stop-dfe-api.sh** - Duplicado (porta 8002 incorreta)
4. **restart-dfe-api.sh** - Duplicado

**Motivo:** Todos eram versões antigas com:
- Caminhos hardcoded incorretos (`/home/harlem/projetos/zipados/openai-xml/`)
- Porta 8002 em vez de 8001
- Lógica duplicada dos scripts principais

---

## 🚀 Como Usar

### Em Produção

```bash
# Da raiz do projeto (usa links simbólicos)
./start-api.sh
./stop-api.sh
./restart-api.sh

# Ou diretamente
./scripts-prod/start-api.sh
./scripts-prod/stop-api.sh
./scripts-prod/restart-api.sh -b  # background
```

### Em Desenvolvimento

```bash
# Executar do diretório raiz
./scripts-dev/test-api.sh
./scripts-dev/monitor-sync.sh
./scripts-dev/diagnose.sh

# Ou entrar na pasta
cd scripts-dev
./test-complete-workflow.sh
```

---

## 📖 Documentação

Cada pasta tem seu próprio README:

- **scripts-prod/README.md** - Documentação completa dos scripts de produção
- **scripts-dev/README.md** - Documentação completa dos scripts de desenvolvimento

---

## 🔧 Benefícios da Nova Organização

### ✅ Antes vs Depois

**Antes:**
```
dfe-sync/
├── start-api.sh
├── start-dfe-api.sh          # duplicado
├── start-dfe-api-new.sh      # duplicado
├── stop-api.sh
├── stop-dfe-api.sh           # duplicado
├── restart-api.sh
├── restart-dfe-api.sh        # duplicado
├── test-api.sh               # misturado
├── diagnose.sh               # misturado
├── ... 17 scripts na raiz
```

**Depois:**
```
dfe-sync/
├── scripts-prod/             # 3 scripts essenciais
│   ├── start-api.sh
│   ├── stop-api.sh
│   └── restart-api.sh
├── scripts-dev/              # 10 scripts de teste/debug
│   └── (organizados por função)
└── [links simbólicos para prod]
```

### Vantagens

1. ✅ **Clareza** - Separa produção de desenvolvimento
2. ✅ **Segurança** - Scripts de teste não ficam acessíveis em prod
3. ✅ **Manutenção** - Fácil identificar o que manter/atualizar
4. ✅ **Documentação** - README específico para cada contexto
5. ✅ **Limpeza** - Removidos duplicados e scripts obsoletos
6. ✅ **Compatibilidade** - Links simbólicos mantêm comandos antigos funcionando

---

## 🔄 Migrações Necessárias

Se você tinha comandos em automação/cron:

### Antes
```bash
/path/to/dfe-sync/start-dfe-api.sh
```

### Depois
```bash
/path/to/dfe-sync/start-api.sh
# ou
/path/to/dfe-sync/scripts-prod/start-api.sh
```

---

## 📝 Checklist de Atualização

- [x] Scripts de produção movidos para `scripts-prod/`
- [x] Scripts de desenvolvimento movidos para `scripts-dev/`
- [x] Caminhos corrigidos (BASE_DIR aponta para raiz)
- [x] Links simbólicos criados na raiz
- [x] READMEs criados para cada pasta
- [x] Scripts duplicados removidos
- [x] Documentação atualizada

---

## 🆘 Suporte

Para mais informações:
- Ver `scripts-prod/README.md` para uso em produção
- Ver `scripts-dev/README.md` para desenvolvimento e testes
- Consultar documentação do projeto principal no `README.md` da raiz
