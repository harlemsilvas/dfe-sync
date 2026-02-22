#!/bin/bash

# Script de Inicialização do Sistema DFE Sync Admin
# Versão: 2.0 - Com Melhorias

echo "🚀 Iniciando Sistema DFE Sync Admin v2.0..."
echo "==============================================="

# Verificar se estamos no diretório correto
if [ ! -f "simple_api.py" ]; then
    echo "❌ Erro: simple_api.py não encontrado!"
    echo "Execute este script no diretório: /mnt/c/Projetos/dfe-sync"
    exit 1
fi

# Parar processos anteriores
echo "🔄 Parando processos anteriores..."
pkill -f simple_api.py 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
sleep 2

# Iniciar Backend API
echo "🖥️  Iniciando Backend API (porta 8001)..."
nohup python3 simple_api.py > api.log 2>&1 &
API_PID=$!
echo "   ✅ Backend iniciado (PID: $API_PID)"

# Esperar backend inicializar
sleep 3

# Verificar se backend está respondendo
if curl -s http://localhost:8001/health > /dev/null; then
    echo "   ✅ Backend API respondendo em http://localhost:8001"
else
    echo "   ❌ Backend não está respondendo!"
    exit 1
fi

# Iniciar Frontend
echo "🌐 Iniciando Frontend React (porta 5175)..."
cd web
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend iniciado (PID: $FRONTEND_PID)"
cd ..

# Esperar frontend inicializar
sleep 5

# Verificar se frontend está respondendo
if curl -s http://localhost:5175 > /dev/null; then
    echo "   ✅ Frontend respondendo em http://localhost:5175"
else
    echo "   ❌ Frontend não está respondendo!"
fi

echo ""
echo "🎉 SISTEMA INICIADO COM SUCESSO!"
echo "==============================================="
echo "📊 Dashboard: http://localhost:5175"
echo "🔧 API Backend: http://localhost:8001"
echo "📖 Logs API: tail -f api.log"
echo "📖 Logs Frontend: tail -f frontend.log"
echo ""
echo "🛑 Para parar o sistema: ./stop-sistema.sh"
echo ""
echo "✨ MELHORIAS IMPLEMENTADAS:"
echo "   • Dashboard com loading states melhorados"
echo "   • Tratamento de erros mais informativo"
echo "   • API com dados mais realistas"
echo "   • Botão de refresh no dashboard"
echo "   • Timestamp de última atualização"
echo "   • Endpoints CRUD completos para empresas"
echo ""

# Verificar saúde do sistema
echo "🔍 Verificando saúde do sistema..."
DASHBOARD_STATS=$(curl -s http://localhost:8001/api/dashboard/stats)
if [ $? -eq 0 ]; then
    echo "   ✅ API Dashboard: Funcionando"
    echo "   📊 XMLs Processados: $(echo $DASHBOARD_STATS | python3 -c 'import json,sys; print(json.load(sys.stdin)["total_xmls"])')"
    echo "   🏢 Empresas: $(echo $DASHBOARD_STATS | python3 -c 'import json,sys; print(json.load(sys.stdin)["empresas_cadastradas"])')"
else
    echo "   ❌ API Dashboard: Erro"
fi

echo ""
echo "🎯 Sistema pronto para uso! Acesse: http://localhost:5175"