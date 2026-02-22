#!/bin/bash

# Script para iniciar o Sistema Administrativo DFE Sync
# Autor: Sistema DFE Sync

echo "🚀 Iniciando Sistema Administrativo DFE Sync"
echo "============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    
    if [[ -n "$BACKEND_PID" ]]; then
        log_info "Parando backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [[ -n "$FRONTEND_PID" ]]; then
        log_info "Parando frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    pkill -P $$ 2>/dev/null || true
    log_success "✅ Serviços parados!"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

log_info "1. Ativando ambiente virtual Python..."
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
    log_success "✅ Ambiente virtual ativado"
else
    log_error "❌ Ambiente virtual não encontrado"
    exit 1
fi

log_info "2. Verificando PostgreSQL Docker..."
if ! docker ps | grep -q postgres; then
    log_warning "Iniciando PostgreSQL..."
    docker-compose up -d postgres
    sleep 3
fi
log_success "✅ PostgreSQL rodando"

log_info "3. Iniciando Backend (FastAPI) na porta 8001..."
(
    cd "$(pwd)"
    python src/api/routes/classificador.py
) &
BACKEND_PID=$!
log_success "✅ Backend iniciado (PID: $BACKEND_PID)"

sleep 5

if kill -0 $BACKEND_PID 2>/dev/null; then
    log_success "✅ Backend operacional"
else
    log_error "❌ Falha no backend"
    exit 1
fi

log_info "4. Preparando Frontend Administrativo..."
cd web/

if [[ ! -d "node_modules" ]] || [[ ! -f "node_modules/.package-lock.json" ]]; then
    log_info "Instalando dependências npm..."
    npm install
    log_success "✅ Dependências instaladas"
fi

log_info "5. Iniciando Frontend Administrativo (Vite) na porta 5173..."
npm run dev &
FRONTEND_PID=$!
log_success "✅ Frontend iniciado (PID: $FRONTEND_PID)"

cd ..

echo ""
echo "🎉 Sistema Administrativo DFE Sync iniciado!"
echo "============================================"
echo ""
echo "📋 URLs de Acesso:"
echo "  🌐 Sistema Administrativo: http://localhost:5173"
echo "  🔗 API Documentation:      http://localhost:8001/docs"
echo "  🔗 API Redoc:              http://localhost:8001/redoc"
echo ""
echo "🎯 Funcionalidades Disponíveis:"
echo "  📊 Dashboard com métricas em tempo real"
echo "  🏢 Cadastro completo de empresas"
echo "  🔐 Gestão de certificados digitais"
echo "  📋 Configuração de CFOPs"
echo "  📁 Importação e upload de documentos"
echo "  🔄 Classificação manual de XMLs"
echo "  📈 Relatórios e logs do sistema"
echo "  ⚙️ Configurações avançadas"
echo ""
echo "🚫 SEM LINHA DE COMANDO!"
echo "   Tudo pode ser feito pela interface web!"
echo ""
echo "🛑 Para parar: Pressione Ctrl+C"
echo ""

log_info "Sistema rodando... (Ctrl+C para parar)"
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log_error "Backend parou!"
        break
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        log_error "Frontend parou!"
        break
    fi
    
    sleep 5
done