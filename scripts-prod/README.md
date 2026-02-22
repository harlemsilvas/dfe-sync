# Scripts de Produção

Scripts essenciais para operação da aplicação em ambiente de produção.

## Scripts Disponíveis

### 🚀 start-api.sh

Inicia a API FastAPI no modo produção.

**Uso:**

```bash
./scripts-prod/start-api.sh
```

**Funcionalidades:**

- Ativa automaticamente o virtualenv
- Define PYTHONPATH corretamente
- Inicia uvicorn na porta 8001
- Modo reload habilitado (pode desabilitar para produção)

**Pré-requisitos:**

- Virtualenv criado em `.venv/`
- Dependências instaladas (`pip install -r requirements.txt`)
- Banco de dados configurado e migrations aplicadas

---

### 🛑 stop-api.sh

Para a API de forma segura.

**Uso:**

```bash
./scripts-prod/stop-api.sh [-p PORTA] [-f]
```

**Opções:**

- `-p PORTA`: Porta da API (default: 8001)
- `-f`: Força SIGKILL se término gracioso falhar
- `-h`: Ajuda

**Exemplos:**

```bash
# Parar API na porta padrão
./scripts-prod/stop-api.sh

# Parar forçadamente
./scripts-prod/stop-api.sh -f

# Parar API em porta diferente
./scripts-prod/stop-api.sh -p 8002
```

---

### 🔄 restart-api.sh

Reinicia a API (stop + start).

**Uso:**

```bash
./scripts-prod/restart-api.sh [-p PORTA] [-m APP_MODULE] [-H HOST] [-b] [-l LOGFILE]
```

**Opções:**

- `-p PORTA`: Porta (default: 8001)
- `-m APP_MODULE`: Módulo ASGI (default: src.api.main:app)
- `-H HOST`: Host bind (default: 0.0.0.0)
- `-b`: Executa em background (nohup)
- `-l LOGFILE`: Caminho do log quando em background
- `-h`: Ajuda

**Exemplos:**

```bash
# Reiniciar normalmente
./scripts-prod/restart-api.sh

# Reiniciar em background
./scripts-prod/restart-api.sh -b

# Reiniciar em background com log customizado
./scripts-prod/restart-api.sh -b -l logs/api-custom.log

# Reiniciar em porta diferente
./scripts-prod/restart-api.sh -p 8002
```

---

## Fluxo de Deploy em Produção

### 1. Setup Inicial

```bash
# Criar virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Ajustar para produção

# Aplicar migrations
alembic upgrade head
```

### 2. Iniciar Aplicação

```bash
# Iniciar API em background
./scripts-prod/restart-api.sh -b -l logs/api-production.log

# Verificar se está rodando
curl http://localhost:8001/health
```

### 3. Monitoramento

```bash
# Ver logs
tail -f logs/api-production.log

# Verificar processo
ps aux | grep uvicorn

# Verificar porta
lsof -i :8001
```

### 4. Atualizações

```bash
# Pull do código
git pull origin main

# Instalar novas dependências (se houver)
source .venv/bin/activate
pip install -r requirements.txt

# Aplicar migrations
alembic upgrade head

# Reiniciar API
./scripts-prod/restart-api.sh -b -l logs/api-production.log
```

---

## Systemd Service (Opcional)

Para rodar como serviço do sistema:

### Criar arquivo de serviço

```bash
sudo nano /etc/systemd/system/dfe-sync.service
```

```ini
[Unit]
Description=DFe Sync API
After=network.target postgresql.service

[Service]
Type=simple
User=harlem
WorkingDirectory=/mnt/c/Projetos/dfe-sync
Environment="PATH=/mnt/c/Projetos/dfe-sync/.venv/bin"
ExecStart=/mnt/c/Projetos/dfe-sync/.venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Gerenciar serviço

```bash
# Habilitar e iniciar
sudo systemctl enable dfe-sync
sudo systemctl start dfe-sync

# Status
sudo systemctl status dfe-sync

# Parar
sudo systemctl stop dfe-sync

# Reiniciar
sudo systemctl restart dfe-sync

# Ver logs
sudo journalctl -u dfe-sync -f
```

---

## Troubleshooting

### API não inicia

```bash
# Verificar virtualenv
ls -la .venv/bin/activate

# Verificar dependências
source .venv/bin/activate
pip list

# Verificar logs
tail -f logs/api.log
```

### Porta já em uso

```bash
# Verificar processo na porta
lsof -i :8001

# Parar forçadamente
./scripts-prod/stop-api.sh -f

# Ou matar diretamente
kill -9 $(lsof -ti:8001)
```

### Problemas de permissão

```bash
# Dar permissão de execução aos scripts
chmod +x scripts-prod/*.sh
```

---

## Variáveis de Ambiente Importantes

```bash
# .env para produção
APP_ENV=production
APP_DEBUG=false
DB_URL=postgresql+psycopg://user:pass@localhost:5432/dfe
NFE_AMBIENTE=PRODUCAO
```

## Segurança

⚠️ **IMPORTANTE:**

- Não commitar `.env` no git
- Usar senhas fortes no banco de dados
- Manter certificados em `storage/certs/` (ignorado pelo git)
- Executar API com usuário não-root
- Configurar firewall adequadamente
- Usar HTTPS em produção (nginx/reverse proxy)
