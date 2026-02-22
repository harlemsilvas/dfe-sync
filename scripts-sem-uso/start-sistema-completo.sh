#!/bin/bash

# Script para iniciar o sistema completo - Backend (FastAPI) + Frontend (Vite React)
# Autor: Sistema DFE Sync
# Data: $(date '+%d/%m/%Y')

set -e  # Sair em caso de erro

echo "🚀 Iniciando Sistema DFE Sync - Backend + Frontend"
echo "================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos no diretório correto
if [[ ! -f "requirements.txt" ]]; then
    log_error "Execute este script do diretório dfe-sync"
    exit 1
fi

# Função para cleanup ao sair
cleanup() {
    log_warning "\n🛑 Parando serviços..."
    
    # Parar backend
    if [[ -n "$BACKEND_PID" ]]; then
        log_info "Parando backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Parar frontend
    if [[ -n "$FRONTEND_PID" ]]; then
        log_info "Parando frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Parar processos do grupo
    pkill -P $$ 2>/dev/null || true
    
    log_success "✅ Serviços parados com sucesso!"
    exit 0
}

# Capturar sinais para cleanup
trap cleanup SIGINT SIGTERM EXIT

log_info "1. Ativando ambiente virtual Python..."
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
    log_success "✅ Ambiente virtual ativado"
else
    log_error "❌ Ambiente virtual não encontrado em .venv/"
    log_info "Execute: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

log_info "2. Verificando PostgreSQL Docker..."
if ! docker ps | grep -q postgres; then
    log_warning "PostgreSQL não está rodando. Iniciando..."
    docker-compose up -d postgres
    sleep 3
    log_success "✅ PostgreSQL iniciado"
else
    log_success "✅ PostgreSQL já está rodando"
fi

log_info "3. Iniciando Backend (FastAPI) na porta 8001..."
# Iniciar backend em background
(
    cd "$(pwd)"
    python src/api/routes/classificador.py
) &
BACKEND_PID=$!
log_success "✅ Backend iniciado (PID: $BACKEND_PID)"

# Aguardar backend subir
log_info "Aguardando backend inicializar..."
sleep 5

# Verificar se backend está rodando
if kill -0 $BACKEND_PID 2>/dev/null; then
    log_success "✅ Backend rodando em http://localhost:8001"
else
    log_error "❌ Falha ao iniciar backend"
    exit 1
fi

log_info "4. Verificando dependências do Frontend..."
cd web/
if [[ ! -d "node_modules" ]]; then
    log_warning "Instalando dependências npm..."
    npm install
    log_success "✅ Dependências instaladas"
else
    log_success "✅ Dependências já instaladas"
fi

log_info "5. Iniciando Frontend (Vite React) na porta 5173..."
# Iniciar frontend em background
npm run dev &
FRONTEND_PID=$!
log_success "✅ Frontend iniciado (PID: $FRONTEND_PID)"

cd ..

echo ""
echo "🎉 Sistema DFE Sync iniciado com sucesso!"
echo "=========================================="
echo ""
echo "📋 URLs disponíveis:"
echo "  🔗 Frontend (React):     http://localhost:5173"
echo "  🔗 Dashboard (HTML):     http://localhost:3000/dashboard.html" 
echo "  🔗 API Documentation:    http://localhost:8001/docs"
echo "  🔗 API Redoc:            http://localhost:8001/redoc"
echo ""
echo "📊 Funcionalidades:"
echo "  ✅ Classificação automática de XMLs"
echo "  ✅ Dashboard com gráficos em tempo real"
echo "  ✅ API REST completa"
echo "  ✅ Interface React moderna"
echo ""
echo "🛑 Para parar: Pressione Ctrl+C"
echo ""

# Manter o script rodando
log_info "Sistema rodando... (Ctrl+C para parar)"
while true; do
    # Verificar se os processos ainda estão rodando
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log_error "Backend parou inesperadamente!"
        break
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        log_error "Frontend parou inesperadamente!"
        break
    fi
    
    sleep 5
done