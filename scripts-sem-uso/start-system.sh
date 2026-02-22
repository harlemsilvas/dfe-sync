#!/bin/bash

# Script para Gerenciar Portas e Inicializar Sistema DFE-Sync
# ===========================================================

# Carregar variáveis de ambiente
if [ -f .env ]; then
    source .env
else
    echo "❌ Arquivo .env não encontrado!"
    exit 1
fi

# Configurações padrão (caso não estejam no .env)
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BACKEND_PORT=${BACKEND_PORT:-8001}

echo "🔧 GERENCIADOR DE SERVIÇOS DFE-SYNC"
echo "===================================="
echo ""

# Função para matar processos em uma porta específica
kill_port() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Verificando porta $port ($service_name)..."
    
    # Buscar processos usando a porta
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "   ⚠️  Porta $port ocupada por processo(s): $pids"
        echo "   🔥 Encerrando processo(s)..."
        
        # Tentar encerrar gentilmente primeiro
        echo $pids | xargs -r kill -TERM
        sleep 2
        
        # Verificar se ainda há processos
        local remaining_pids=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo "   💀 Forçando encerramento..."
            echo $remaining_pids | xargs -r kill -KILL
            sleep 1
        fi
        
        # Verificação final
        local final_check=$(lsof -ti:$port 2>/dev/null)
        if [ -z "$final_check" ]; then
            echo "   ✅ Porta $port liberada com sucesso"
        else
            echo "   ❌ Falha ao liberar porta $port"
            return 1
        fi
    else
        echo "   ✅ Porta $port já está livre"
    fi
    
    return 0
}

# Função para iniciar o backend
start_backend() {
    echo ""
    echo "🚀 Iniciando Backend (Porta $BACKEND_PORT)..."
    
    # Verificar se o arquivo da API existe
    if [ ! -f "simple_api.py" ]; then
        echo "   ❌ Arquivo simple_api.py não encontrado!"
        return 1
    fi
    
    # Atualizar CORS no arquivo da API
    echo "   🔧 Configurando CORS para porta $FRONTEND_PORT..."
    python3 -c "
import re

# Ler arquivo
with open('simple_api.py', 'r') as f:
    content = f.read()

# Atualizar configuração CORS
cors_pattern = r'origins=\[[^\]]*\]'
new_cors = f'origins=[\"http://localhost:${FRONTEND_PORT}\", \"http://127.0.0.1:${FRONTEND_PORT}\"]'

content = re.sub(cors_pattern, new_cors, content)

# Atualizar porta se necessário
if 'app.run(host=' in content:
    port_pattern = r'app\.run\(host=\"[^\"]*\",\s*port=\d+'
    new_run = f'app.run(host=\"0.0.0.0\", port=${BACKEND_PORT}'
    content = re.sub(port_pattern, new_run, content)

# Salvar arquivo
with open('simple_api.py', 'w') as f:
    f.write(content)

print('CORS configurado com sucesso')
"
    
    # Iniciar backend em background
    echo "   🔄 Iniciando servidor Python..."
    nohup python3 simple_api.py > logs/api-backend.log 2>&1 &
    local backend_pid=$!
    
    # Aguardar inicialização
    echo "   ⏳ Aguardando inicialização do backend..."
    for i in {1..10}; do
        if curl -s http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
            echo "   ✅ Backend iniciado com sucesso (PID: $backend_pid)"
            echo "   🌐 URL: http://localhost:$BACKEND_PORT"
            return 0
        fi
        sleep 1
        echo "      Tentativa $i/10..."
    done
    
    echo "   ❌ Falha ao iniciar backend"
    return 1
}

# Função para iniciar o frontend
start_frontend() {
    echo ""
    echo "🎨 Iniciando Frontend (Porta $FRONTEND_PORT)..."
    
    # Verificar se o diretório web existe
    if [ ! -d "web" ]; then
        echo "   ❌ Diretório web/ não encontrado!"
        return 1
    fi
    
    cd web
    
    # Verificar se package.json existe
    if [ ! -f "package.json" ]; then
        echo "   ❌ package.json não encontrado no diretório web/"
        cd ..
        return 1
    fi
    
    # Atualizar configuração da API no frontend
    echo "   🔧 Configurando URL da API..."
    if [ -f "src/api/admin.ts" ]; then
        sed -i "s|baseURL: ['\"][^'\"]*['\"]|baseURL: 'http://localhost:${BACKEND_PORT}/api'|g" src/api/admin.ts
    fi
    
    # Configurar porta no vite.config.ts
    echo "   🔧 Configurando porta do Vite..."
    if [ -f "vite.config.ts" ]; then
        # Verificar se já existe configuração de server
        if grep -q "server:" vite.config.ts; then
            # Atualizar porta existente
            sed -i "s/port: [0-9]*/port: ${FRONTEND_PORT}/g" vite.config.ts
        else
            # Adicionar configuração de servidor
            sed -i "/export default defineConfig({/a\\  server: {\n    port: ${FRONTEND_PORT},\n    host: true\n  }," vite.config.ts
        fi
    fi
    
    # Iniciar frontend em background
    echo "   🔄 Iniciando servidor Vite..."
    nohup npm run dev > ../logs/frontend-vite.log 2>&1 &
    local frontend_pid=$!
    
    # Aguardar inicialização
    echo "   ⏳ Aguardando inicialização do frontend..."
    for i in {1..15}; do
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            echo "   ✅ Frontend iniciado com sucesso (PID: $frontend_pid)"
            echo "   🌐 URL: http://localhost:$FRONTEND_PORT"
            cd ..
            return 0
        fi
        sleep 1
        echo "      Tentativa $i/15..."
    done
    
    echo "   ❌ Falha ao iniciar frontend"
    cd ..
    return 1
}

# Função para mostrar status dos serviços
show_status() {
    echo ""
    echo "📊 STATUS DOS SERVIÇOS:"
    echo "======================="
    
    # Backend
    if curl -s http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
        echo "   🟢 Backend: ONLINE (http://localhost:$BACKEND_PORT)"
    else
        echo "   🔴 Backend: OFFLINE"
    fi
    
    # Frontend
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo "   🟢 Frontend: ONLINE (http://localhost:$FRONTEND_PORT)"
    else
        echo "   🔴 Frontend: OFFLINE"
    fi
}

# Função principal
main() {
    echo "Configuração atual:"
    echo "   Frontend: Porta $FRONTEND_PORT"
    echo "   Backend:  Porta $BACKEND_PORT"
    echo ""
    
    # Criar diretório de logs se não existir
    mkdir -p logs
    
    # Liberar portas
    kill_port $BACKEND_PORT "Backend API"
    kill_port $FRONTEND_PORT "Frontend Vite"
    
    # Aguardar um pouco para garantir que as portas foram liberadas
    sleep 2
    
    # Iniciar serviços
    if start_backend; then
        if start_frontend; then
            show_status
            echo ""
            echo "🎉 SISTEMA INICIADO COM SUCESSO!"
            echo "================================"
            echo ""
            echo "📱 Interface principal: http://localhost:$FRONTEND_PORT"
            echo "🔗 API Backend: http://localhost:$BACKEND_PORT/api"
            echo ""
            echo "📋 Páginas disponíveis:"
            echo "   • Empresas: http://localhost:$FRONTEND_PORT/empresas"
            echo "   • Certificados: http://localhost:$FRONTEND_PORT/certificados"
            echo ""
            echo "📊 Logs em tempo real:"
            echo "   • Backend: tail -f logs/api-backend.log"
            echo "   • Frontend: tail -f logs/frontend-vite.log"
        else
            echo ""
            echo "❌ Falha ao iniciar frontend!"
        fi
    else
        echo ""
        echo "❌ Falha ao iniciar backend!"
    fi
}

# Executar função principal
main