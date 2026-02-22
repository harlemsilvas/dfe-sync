#!/usr/bin/env bash
# Script para iniciar Backend + Frontend juntos
set -euo pipefail

SCRIPT_REAL="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_REAL")"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$BASE_DIR"

echo "🚀 Iniciando DFe Sync - Full Stack"
echo "==================================="
echo ""

# 1. Verificar se backend já está rodando
if curl -s http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ Backend já está rodando em http://localhost:8001"
else
    echo "🔧 Iniciando Backend FastAPI..."
    ./start-api.sh > logs/api-backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   PID: $BACKEND_PID"
    
    # Aguardar backend iniciar
    echo "   Aguardando backend iniciar..."
    for i in {1..10}; do
        if curl -s http://localhost:8001/health >/dev/null 2>&1; then
            echo "   ✅ Backend iniciado!"
            break
        fi
        sleep 1
    done
fi

echo ""

# 2. Verificar se frontend já está rodando
if curl -s http://localhost:5173 >/dev/null 2>&1; then
    echo "✅ Frontend já está rodando em http://localhost:5173"
else
    echo "🔧 Iniciando Frontend Vite..."
    cd web
    npm run dev > ../logs/frontend-vite.log 2>&1 &
    FRONTEND_PID=$!
    echo "   PID: $FRONTEND_PID"
    cd ..
    
    # Aguardar frontend iniciar
    echo "   Aguardando frontend iniciar..."
    for i in {1..10}; do
        if curl -s http://localhost:5173 >/dev/null 2>&1; then
            echo "   ✅ Frontend iniciado!"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "✅ Sistema iniciado com sucesso!"
echo ""
echo "📍 URLs:"
echo "   Frontend:     http://localhost:5173"
echo "   Backend API:  http://localhost:8001"
echo "   API Docs:     http://localhost:8001/docs"
echo ""
echo "📁 Logs:"
echo "   Backend:  tail -f logs/api-backend.log"
echo "   Frontend: tail -f logs/frontend-vite.log"
echo ""
echo "🛑 Para parar:"
echo "   Backend:  ./stop-api.sh"
echo "   Frontend: pkill -f 'vite'"
echo ""
