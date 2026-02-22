#!/bin/bash

# Script para Parar Todos os Serviços DFE-Sync
# ============================================

# Carregar variáveis de ambiente
if [ -f .env ]; then
    source .env
fi

# Configurações padrão
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BACKEND_PORT=${BACKEND_PORT:-8001}

echo "🛑 PARANDO SERVIÇOS DFE-SYNC"
echo "============================"
echo ""

# Função para matar processos em uma porta
stop_port() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Verificando porta $port ($service_name)..."
    
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "   🔥 Encerrando processo(s): $pids"
        
        # Encerrar gentilmente
        echo $pids | xargs -r kill -TERM
        sleep 2
        
        # Verificar se ainda há processos
        local remaining_pids=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo "   💀 Forçando encerramento..."
            echo $remaining_pids | xargs -r kill -KILL
            sleep 1
        fi
        
        echo "   ✅ Porta $port liberada"
    else
        echo "   ✅ Porta $port já estava livre"
    fi
}

# Parar serviços
stop_port $BACKEND_PORT "Backend API"
stop_port $FRONTEND_PORT "Frontend Vite"

# Parar outros processos relacionados
echo ""
echo "🔍 Verificando outros processos relacionados..."

# Processos Python (simple_api.py)
python_pids=$(pgrep -f "simple_api.py")
if [ -n "$python_pids" ]; then
    echo "   🔥 Encerrando processos Python: $python_pids"
    echo $python_pids | xargs -r kill -TERM
    sleep 1
fi

# Processos Node.js/Vite
node_pids=$(pgrep -f "vite\|npm.*dev")
if [ -n "$node_pids" ]; then
    echo "   🔥 Encerrando processos Node.js: $node_pids"
    echo $node_pids | xargs -r kill -TERM
    sleep 1
fi

echo ""
echo "✅ TODOS OS SERVIÇOS FORAM PARADOS"
echo ""