#!/bin/bash

# Script para parar todos os serviços do sistema DFE Sync
# Autor: Sistema DFE Sync

echo "🛑 Parando Sistema DFE Sync"
echo "==========================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parar processos Python na porta 8001 (Backend)
log_info "Parando Backend (porta 8001)..."
BACKEND_PIDS=$(lsof -ti:8001)
if [[ -n "$BACKEND_PIDS" ]]; then
    kill -TERM $BACKEND_PIDS 2>/dev/null
    sleep 2
    # Force kill se ainda estiver rodando
    BACKEND_PIDS=$(lsof -ti:8001)
    if [[ -n "$BACKEND_PIDS" ]]; then
        kill -KILL $BACKEND_PIDS 2>/dev/null
    fi
    log_success "✅ Backend parado"
else
    log_info "Backend já estava parado"
fi

# Parar processos Node.js na porta 5173 (Frontend)
log_info "Parando Frontend (porta 5173)..."
FRONTEND_PIDS=$(lsof -ti:5173)
if [[ -n "$FRONTEND_PIDS" ]]; then
    kill -TERM $FRONTEND_PIDS 2>/dev/null
    sleep 2
    # Force kill se ainda estiver rodando
    FRONTEND_PIDS=$(lsof -ti:5173)
    if [[ -n "$FRONTEND_PIDS" ]]; then
        kill -KILL $FRONTEND_PIDS 2>/dev/null
    fi
    log_success "✅ Frontend parado"
else
    log_info "Frontend já estava parado"
fi

# Parar processos na porta 3000 (Dashboard HTML)
log_info "Parando Dashboard (porta 3000)..."
DASHBOARD_PIDS=$(lsof -ti:3000)
if [[ -n "$DASHBOARD_PIDS" ]]; then
    kill -TERM $DASHBOARD_PIDS 2>/dev/null
    sleep 2
    DASHBOARD_PIDS=$(lsof -ti:3000)
    if [[ -n "$DASHBOARD_PIDS" ]]; then
        kill -KILL $DASHBOARD_PIDS 2>/dev/null
    fi
    log_success "✅ Dashboard parado"
else
    log_info "Dashboard já estava parado"
fi

# Parar processos relacionados ao DFE Sync
log_info "Parando outros processos relacionados..."
pkill -f "classificador.py" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

echo ""
log_success "🎉 Todos os serviços do DFE Sync foram parados!"
echo ""
echo "Para reiniciar:"
echo "  • Sistema completo:  ./start-sistema-completo.sh"
echo "  • Apenas backend:    ./start-backend.sh"
echo "  • Apenas frontend:   ./start-frontend.sh"