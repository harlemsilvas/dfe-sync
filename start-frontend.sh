#!/bin/bash

# Script para iniciar apenas o Frontend (Vite React) na porta 5173
# Autor: Sistema DFE Sync

echo "🌐 Iniciando Frontend DFE Sync (Vite React)"
echo "==========================================="

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Verificar se estamos no diretório correto
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ Execute este script do diretório dfe-sync"
    exit 1
fi

log_info "Navegando para diretório web..."
cd web/

log_info "Verificando dependências npm..."
if [[ ! -d "node_modules" ]]; then
    log_info "Instalando dependências..."
    npm install
    log_success "✅ Dependências instaladas"
fi

log_info "Iniciando servidor de desenvolvimento Vite..."
echo ""
echo "🎉 Frontend será iniciado na porta 5173"
echo "🔗 URL: http://localhost:5173"
echo ""
echo "🛑 Para parar: Pressione Ctrl+C"
echo ""

npm run dev