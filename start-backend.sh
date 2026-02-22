#!/bin/bash

# Script para iniciar apenas o Backend (FastAPI) na porta 8001
# Autor: Sistema DFE Sync

echo "⚙️ Iniciando Backend DFE Sync (FastAPI)"
echo "======================================"

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos no diretório correto
if [[ ! -f "requirements.txt" ]]; then
    log_error "Execute este script do diretório dfe-sync"
    exit 1
fi

log_info "Ativando ambiente virtual Python..."
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
    log_success "✅ Ambiente virtual ativado"
else
    log_error "❌ Ambiente virtual não encontrado em .venv/"
    exit 1
fi

log_info "Verificando PostgreSQL Docker..."
if ! docker ps | grep -q postgres; then
    log_info "Iniciando PostgreSQL..."
    docker-compose up -d postgres
    sleep 3
fi

log_info "Iniciando servidor FastAPI..."
echo ""
echo "🎉 Backend será iniciado na porta 8001"
echo "🔗 API Docs: http://localhost:8001/docs"
echo "🔗 Redoc: http://localhost:8001/redoc"
echo ""
echo "🛑 Para parar: Pressione Ctrl+C"
echo ""

python src/api/routes/classificador.py