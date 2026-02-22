# Correções Aplicadas aos Scripts

## ✅ Problema Resolvido

### Sintoma Inicial

```bash
$ ./start-api.sh
[start-api] Virtualenv não encontrado em /home/harlem/projetos/zipados/apps/openai-xml/.venv/bin/activate
```

**Causa:** Os scripts estavam calculando o `BASE_DIR` incorretamente ao serem executados via links simbólicos, resultando na busca do virtualenv na pasta **pai** em vez da pasta do projeto `dfe-sync`.

---

## 🔧 Correções Aplicadas

### 1. Scripts de Produção - Resolução de Links Simbólicos

Todos os 3 scripts de produção foram corrigidos para usar `readlink -f` e resolver corretamente o caminho real do script:

**Arquivos corrigidos:**

- `scripts-prod/start-api.sh`
- `scripts-prod/stop-api.sh`
- `scripts-prod/restart-api.sh`

**Código anterior:**

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
```

**Código corrigido:**

```bash
# Resolve o caminho real do script (segue links simbólicos) e sobe para a raiz
SCRIPT_REAL="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_REAL")"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
```

**Benefício:** Agora o script funciona corretamente tanto quando executado:

- Diretamente: `./scripts-prod/start-api.sh`
- Via link simbólico: `./start-api.sh`
- De outro diretório: `/path/to/dfe-sync/start-api.sh`

---

### 2. Stop API - Suporte a Múltiplos PIDs

O script `stop-api.sh` foi corrigido para lidar corretamente com múltiplos processos na mesma porta (uvicorn parent + worker).

**Problema anterior:**

```bash
pid_port=$(lsof -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true)
kill "$found_pid"  # Falhava quando havia múltiplos PIDs
```

**Correção aplicada:**

```bash
# Pega todos os PIDs e trata como lista
pid_port=$(lsof -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | tr '\n' ' ' | xargs echo || true)

# Matar todos os PIDs encontrados
for pid in $found_pid; do
  kill "$pid" 2>/dev/null || true
done

# Aguardar término de cada processo
for pid in $found_pid; do
  for i in {1..20}; do
    if [[ -d "/proc/$pid" ]]; then
      sleep 0.2
    else
      break
    fi
  done
done

# Force kill se necessário
if $FORCE; then
  for pid in $still_running; do
    kill -9 "$pid" 2>/dev/null || true
  done
fi
```

**Benefício:** Para corretamente tanto o processo pai do uvicorn quanto os workers.

---

## ✅ Validação

### Testes Realizados

1. **Iniciar API:**

   ```bash
   cd dfe-sync
   ./start-api.sh
   # ✅ API inicia corretamente
   ```

2. **Health Check:**

   ```bash
   curl http://localhost:8001/health
   # ✅ Retorna: {"status":"ok"}
   ```

3. **Parar API:**

   ```bash
   ./stop-api.sh
   # ✅ Para todos os processos corretamente
   ```

4. **Via Link Simbólico:**
   ```bash
   cd ..
   dfe-sync/start-api.sh
   # ✅ Funciona corretamente
   ```

---

## 📋 Estrutura Final Validada

```
dfe-sync/
├── scripts-prod/
│   ├── start-api.sh      ✅ Corrigido
│   ├── stop-api.sh       ✅ Corrigido
│   ├── restart-api.sh    ✅ Corrigido
│   └── README.md
├── scripts-dev/
│   └── (10 scripts de teste/debug)
├── start-api.sh → scripts-prod/start-api.sh     ✅ Funciona
├── stop-api.sh → scripts-prod/stop-api.sh       ✅ Funciona
├── restart-api.sh → scripts-prod/restart-api.sh ✅ Funciona
└── .venv/               ✅ Encontrado corretamente
    └── bin/activate
```

---

## 🎯 Comandos Funcionais

Todos os comandos abaixo agora funcionam corretamente:

```bash
# Da raiz do projeto
cd /mnt/c/Projetos/dfe-sync

# Iniciar (qualquer forma)
./start-api.sh
./scripts-prod/start-api.sh
bash start-api.sh

# Parar (qualquer forma)
./stop-api.sh
./stop-api.sh -f              # força SIGKILL
./stop-api.sh -p 8002         # porta customizada

# Reiniciar (qualquer forma)
./restart-api.sh
./restart-api.sh -b           # background
./restart-api.sh -b -l logs/api.log
```

---

## 🔍 Debug

Se ainda houver problemas, use:

```bash
# Ver caminho resolvido
cd dfe-sync
SCRIPT_REAL="$(readlink -f "./start-api.sh")"
echo "Script real: $SCRIPT_REAL"
echo "Diretório: $(dirname "$SCRIPT_REAL")"

# Ver virtualenv
ls -la .venv/bin/activate

# Testar manualmente
source .venv/bin/activate
python --version
which uvicorn
```

---

## 📝 Notas Importantes

1. ✅ `readlink -f` resolve links simbólicos recursivamente
2. ✅ Scripts funcionam independente do diretório de execução
3. ✅ Múltiplos processos uvicorn são parados corretamente
4. ✅ Virtualenv em `dfe-sync/.venv/` é encontrado corretamente
5. ✅ Links simbólicos na raiz continuam funcionando

---

## 🚀 Status: RESOLVIDO

Todos os scripts de produção estão funcionando corretamente após as correções aplicadas.
