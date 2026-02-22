# Guia de Gerenciamento do Sistema DFE-Sync

## 🔧 Scripts de Controle

### Iniciar Sistema
```bash
./start-system.sh
```
- Carrega configurações do `.env`
- Libera portas ocupadas automaticamente
- Inicia backend (porta 8001) e frontend (porta 5173)
- Configura CORS e URLs automaticamente

### Parar Sistema
```bash
./stop-system.sh
```
- Para todos os serviços relacionados
- Libera todas as portas
- Encerra processos Python e Node.js

## 📋 Configurações Padrão

### Portas
- **Frontend**: 5173 (Vite/React)
- **Backend**: 8001 (FastAPI/Python)

### URLs
- **Interface**: http://localhost:5173
- **API**: http://localhost:8001/api

## 🌐 Páginas Disponíveis

- **Dashboard**: http://localhost:5173/
- **Empresas**: http://localhost:5173/empresas
- **Certificados**: http://localhost:5173/certificados

## 📊 Monitoramento

### Logs em Tempo Real
```bash
# Backend
tail -f logs/api-backend.log

# Frontend  
tail -f logs/frontend-vite.log
```

### Status dos Serviços
```bash
# Verificar se estão rodando
curl http://localhost:8001/api/health  # Backend
curl http://localhost:5173             # Frontend
```

## ⚙️ Configuração de Ambiente

O arquivo `.env` contém todas as configurações:

```env
# Portas
FRONTEND_PORT=5173
BACKEND_PORT=8001

# URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8001
API_BASE_URL=http://localhost:8001/api

# CORS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## 🔄 Comandos Úteis

### Reiniciar Sistema
```bash
./stop-system.sh && ./start-system.sh
```

### Verificar Portas
```bash
lsof -i :5173  # Frontend
lsof -i :8001  # Backend
```

### Liberar Porta Manualmente
```bash
# Encontrar processo
lsof -ti :PORTA

# Encerrar processo
kill -9 $(lsof -ti :PORTA)
```

## 🛠️ Resolução de Problemas

### Erro de Porta Ocupada
O script `start-system.sh` automaticamente libera as portas, mas se necessário:
```bash
./stop-system.sh
./start-system.sh
```

### Erro de CORS
As configurações de CORS são atualizadas automaticamente pelo script de início.

### API não Responde
Verificar logs:
```bash
tail -f logs/api-backend.log
```

### Frontend não Carrega
Verificar logs:
```bash
tail -f logs/frontend-vite.log
```

## 📁 Estrutura de Arquivos

```
dfe-sync/
├── .env                    # Configurações globais
├── start-system.sh        # Script de inicialização
├── stop-system.sh         # Script de parada
├── simple_api.py          # Backend API
├── web/                   # Frontend React
│   ├── vite.config.ts     # Configuração Vite
│   └── src/api/admin.ts   # Cliente API
└── logs/                  # Logs do sistema
    ├── api-backend.log
    └── frontend-vite.log
```